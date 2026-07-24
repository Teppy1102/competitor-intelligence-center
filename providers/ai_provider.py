"""OpenAIAIClient - implementation THAT cua analyzer.AIClient (interface,
xem analyzer/ai_client.py). Port pattern model-fallback-chain tu
MARKET_INTELLIGENCE_CENTER/providers/ai_provider.py - KHONG doi cach chon
model, chi doi tu list[Dict] (MIC) sang 2 chuoi system_prompt/user_prompt
(CIC, dung PromptBundle da build san o analyzer/prompt_builder.py).
"""

from __future__ import annotations

import os
import re

from openai import AsyncOpenAI

from analyzer import AIClient, AIClientError

# gpt-5-mini nhe/re, du manh cho tac vu tong hop van ban co cau truc - giong
# lua chon mac dinh cua MIC de dong bo chi phi van hanh.
DEFAULT_MODEL = "gpt-5-mini"
FALLBACK_MODELS = ["gpt-5-mini", "gpt-4o-mini", "gpt-4.1-mini", "gpt-3.5-turbo"]


class OpenAIAIClient(AIClient):
    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model_name = model_name

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        last_error: Exception | None = None
        for model in self._model_candidates():
            try:
                response = await self._client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                html = (response.choices[0].message.content or "").strip()
                if html.startswith("```"):
                    html = re.sub(
                        r"^```(?:html)?\s*|\s*```$", "", html, flags=re.MULTILINE
                    ).strip()
                if not html:
                    raise AIClientError(f"Model {model} trả về nội dung rỗng.")
                return html
            except Exception as e:  # noqa: BLE001 - thu model fallback tiep theo
                last_error = e
                continue
        raise AIClientError(f"Không thể gọi AI sau khi thử hết model fallback: {last_error}")

    def _model_candidates(self) -> list[str]:
        ordered = [self._model_name]
        ordered += [m for m in FALLBACK_MODELS if m != self._model_name]
        return ordered


def get_ai_client() -> OpenAIAIClient:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Thiếu OPENAI_API_KEY. Thêm dòng OPENAI_API_KEY=... vào file .env.")
    model_name = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    return OpenAIAIClient(api_key=api_key, model_name=model_name)

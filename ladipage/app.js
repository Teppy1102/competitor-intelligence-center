/* ==========================================================================
   Market Intelligence Center — Ladipage Frontend
   app.js — Vanilla JS, khong framework, khong build step.
   To chuc thanh cac "module" bang IIFE de tranh dung bien global, van la
   1 file duy nhat de de dan vao Ladipage HTML Block.

   Muc luc:
     1. CONFIG        - hang so cau hinh (API_BASE la dong DUY NHAT can sua
                         neu doi domain backend)
     2. ICONS          - SVG icon dung chung
     3. API             - lop goi REST API (khong sua logic, chi goi dung
                           endpoint da co san)
     4. UTILS            - ham tien ich thuan (format, escape, mapping)
     5. RENDER.section     - render tung section Dashboard tu JSON that
     6. RENDER.dashboard    - lap rap toan bo Dashboard
     7. LOADING              - dieu khien man hinh loading + polling
     8. APP                   - dieu phoi flow, wiring DOM event
   ========================================================================== */

/* ---------- 1. CONFIG ---------- */
const CONFIG = Object.freeze({
  // Doi URL nay neu Backend Render doi domain - day la noi DUY NHAT can sua.
  API_BASE: "https://market-intelligence-center-api.onrender.com",
  POLL_INTERVAL_MS: 4000,
  POLL_MAX_RETRIES: 3, // so lan loi mang lien tiep truoc khi bao loi han (khong tinh loi tu server)
  EXAMPLE_KEYWORDS: [
    "Khóa học HRBP",
    "Khóa học L&D",
    "Khóa học Total Rewards",
    "Khóa học BSC-KPI",
    "Khóa học OKR",
    "Khóa học HRM",
  ],
});

/* ---------- 2. ICONS ---------- */
const ICONS = {
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4.3-4.3"/></svg>`,
  globe: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 6 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-6-3.8-9s1.3-6.3 3.8-9z"/></svg>`,
  file: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/></svg>`,
  brain: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4a3 3 0 0 0-3 3v1a3 3 0 0 0-1 5.8V15a3 3 0 0 0 3 3h1"/><path d="M15 4a3 3 0 0 1 3 3v1a3 3 0 0 1 1 5.8V15a3 3 0 0 1-3 3h-1"/><path d="M9 4a3 3 0 0 1 6 0v13a3 3 0 0 1-6 0z"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M12 20V4M20 20v-7"/></svg>`,
  trend: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/></svg>`,
  bulb: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6M10 22h4"/><path d="M12 2a6 6 0 0 0-4 10.5c.6.6 1 1.4 1 2.5h6c0-1.1.4-1.9 1-2.5A6 6 0 0 0 12 2z"/></svg>`,
  users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><circle cx="18" cy="9" r="2.4"/><path d="M15.8 14.2c2.6.5 4.2 2.4 4.2 5.3"/></svg>`,
  shield: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v6c0 4.5-3 7.7-7 9-4-1.3-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7"/></svg>`,
  clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg>`,
  target: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="0.8" fill="currentColor" stroke="none"/></svg>`,
  compass: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M15 9l-2 6-6 2 2-6z"/></svg>`,
  link: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 14a4 4 0 0 0 5.7 0l2.3-2.3a4 4 0 0 0-5.7-5.7L11 7"/><path d="M14 10a4 4 0 0 0-5.7 0L6 12.3a4 4 0 0 0 5.7 5.7L13 17"/></svg>`,
  layers: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></svg>`,
  arrowUpRight: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M8 7h9v9"/></svg>`,
  download: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0l-4-4m4 4l4-4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>`,
  refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v5h5"/><path d="M20 20v-5h-5"/><path d="M5.6 9A7 7 0 0 1 19 12M18.4 15A7 7 0 0 1 5 12"/></svg>`,
};

/* ---------- 3. API ---------- */
const Api = (() => {
  async function request(path, options = {}) {
    const res = await fetch(`${CONFIG.API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      /* endpoint /html khong tra JSON - xu ly rieng o getReportHtml() */
    }
    if (!res.ok) {
      throw new Error((data && data.detail) || `Lỗi API (HTTP ${res.status})`);
    }
    return data;
  }

  return {
    health: () => request("/api/health"),

    startResearch: (keyword) =>
      request("/api/research", {
        method: "POST",
        body: JSON.stringify({ keyword }),
      }),

    getReport: (jobId) => request(`/api/report/${encodeURIComponent(jobId)}`),

    getReportHtml: async (jobId) => {
      const res = await fetch(`${CONFIG.API_BASE}/api/report/${encodeURIComponent(jobId)}/html`);
      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const j = await res.json();
          detail = j.detail || detail;
        } catch (e) {
          /* noop */
        }
        throw new Error(detail);
      }
      return res.text();
    },

    getHistory: () => request("/api/history"),

    deleteHistory: (jobId) =>
      request(`/api/history/${encodeURIComponent(jobId)}`, { method: "DELETE" }),
  };
})();

/* ---------- 4. UTILS ---------- */
const Utils = (() => {
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return escapeHtml(str).replace(/"/g, "&quot;");
  }

  function domainOf(url) {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch (e) {
      return url || "";
    }
  }

  function formatDateTime(isoLike) {
    if (!isoLike) return "-";
    const d = new Date(isoLike);
    if (isNaN(d.getTime())) return isoLike;
    return d.toLocaleString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  const TIER_PCT = { "Thấp": 25, "Trung bình": 55, "Cao": 85, "Không đủ dữ liệu": 8 };
  const TREND_PCT = { "Đang giảm": 20, "Ổn định": 50, "Đang lên": 85, "Chưa rõ": 15, "Không đủ dữ liệu": 8 };

  function scoreToPercent(name, value) {
    if (name === "AI Confidence") {
      const n = parseInt(value, 10);
      return Number.isFinite(n) ? Math.max(4, Math.min(100, n)) : 8;
    }
    if (name === "Trend Score") return TREND_PCT[value] ?? 30;
    return TIER_PCT[value] ?? 30;
  }

  function scoreTone(name, value) {
    if (value === "Không đủ dữ liệu") return "gray";
    if (name === "AI Confidence") {
      const n = parseInt(value, 10);
      if (!Number.isFinite(n)) return "gray";
      return n >= 70 ? "green" : n >= 45 ? "blue" : "orange";
    }
    if (name === "Trend Score") {
      if (value === "Đang lên") return "green";
      if (value === "Đang giảm") return "orange";
      return "blue";
    }
    const goodWhenHigh = name === "Opportunity Score";
    if (value === "Cao") return goodWhenHigh ? "green" : "orange";
    if (value === "Thấp") return goodWhenHigh ? "orange" : "blue";
    return "blue";
  }

  function safeArray(v) {
    return Array.isArray(v) ? v : [];
  }

  return { escapeHtml, escapeAttr, domainOf, formatDateTime, scoreToPercent, scoreTone, safeArray };
})();

/* ---------- 5 & 6. RENDER ---------- */
const Render = (() => {
  function card({ title, icon, subtitle, body, span2 = false, extraClass = "" }) {
    return `
    <div class="card card-pad ${span2 ? "mic-span-2" : ""} ${extraClass}">
      <div class="card-header">
        <div class="card-title-group">
          <div class="card-icon">${ICONS[icon] || ""}</div>
          <div>
            <div class="card-title">${Utils.escapeHtml(title)}</div>
            ${subtitle ? `<div class="card-subtitle">${Utils.escapeHtml(subtitle)}</div>` : ""}
          </div>
        </div>
      </div>
      <div class="card-body">${body}</div>
    </div>`;
  }

  function citationsHtml(citations) {
    const list = Utils.safeArray(citations);
    if (!list.length) return "";
    const links = list
      .map(
        (c) =>
          `<a href="${Utils.escapeAttr(c.url)}" target="_blank" rel="noopener">${Utils.escapeHtml(c.text || Utils.domainOf(c.url))}</a>`
      )
      .join(", ");
    return `<div class="mic-citations">Nguồn: ${links}</div>`;
  }

  /* Danh sach dang {text, citations} - dung cho Trend / Opportunity / Recommendation */
  function textListBody(items, emptyMsg) {
    const list = Utils.safeArray(items);
    if (!list.length) return `<p class="card-empty">${Utils.escapeHtml(emptyMsg)}</p>`;
    return `<ul>${list
      .map(
        (it) => `<li>${Utils.escapeHtml(it.text)}${citationsHtml(it.citations)}</li>`
      )
      .join("")}</ul>`;
  }

  function genericTableBody(rows, columns, emptyMsg) {
    const list = Utils.safeArray(rows);
    if (!list.length) return `<p class="card-empty">${Utils.escapeHtml(emptyMsg)}</p>`;
    const head = columns.map((c) => `<th>${Utils.escapeHtml(c.label)}</th>`).join("");
    const body = list
      .map((row) => {
        const cells = columns
          .map((c) => `<td>${Utils.escapeHtml(row[c.key] ?? "-")}</td>`)
          .join("");
        return `<tr>${cells}</tr>${
          row.citations && row.citations.length
            ? `<tr><td colspan="${columns.length}" style="padding-top:0">${citationsHtml(row.citations)}</td></tr>`
            : ""
        }`;
      })
      .join("");
    return `<div class="table-wrap"><table class="data-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  /* ---- Section: Executive Dashboard ---- */
  function execDashboard(executiveSummary) {
    const qna = Utils.safeArray(executiveSummary && executiveSummary.qna);
    const rows = qna
      .map(
        (q) => `
        <div class="mic-qna-row">
          <span class="mic-qna-no">${String(q.no).padStart(2, "0")}</span>
          <span class="mic-qna-q">${Utils.escapeHtml(q.question)}</span>
          <span class="mic-qna-a">${
            q.answer === "Không đủ dữ liệu"
              ? `<span class="badge badge-gray">Không đủ dữ liệu</span>`
              : Utils.escapeHtml(q.answer)
          }</span>
        </div>`
      )
      .join("");
    return `<div class="mic-qna-list">${rows || `<p class="card-empty">Không có dữ liệu.</p>`}</div>`;
  }

  const SCORE_META = {
    "Competition Score": { icon: "users", tip: "Mức độ cạnh tranh hiện diện trong nguồn tìm kiếm — không phải thị phần thật." },
    "Opportunity Score": { icon: "bulb", tip: "Mức độ hấp dẫn của khoảng trống đã phát hiện." },
    "Trend Score": { icon: "trend", tip: "Mức độ 'nóng' của chủ đề dựa trên các cụm nội dung đang tăng." },
    "Authority Score": { icon: "shield", tip: "Tỷ trọng nguồn uy tín (Tier 1-2) đang thảo luận chủ đề này." },
    "Content Saturation": { icon: "layers", tip: "Mức độ các góc nội dung đã bị khai thác nhiều." },
    "SEO Difficulty": { icon: "target", tip: "Ước tính thô độ khó xếp hạng nội dung mới — không thay thế công cụ SEO chuyên dụng." },
    "AI Confidence": { icon: "shield", tip: "AI tự đánh giá độ tin cậy report." },
  };

  function kpiGrid(scores) {
    const s = scores || {};
    const cards = Object.keys(SCORE_META)
      .map((name) => {
        const entry = s[name] || { value: "Không đủ dữ liệu", note: "" };
        const meta = SCORE_META[name];
        const tone = Utils.scoreTone(name, entry.value);
        const pct = Utils.scoreToPercent(name, entry.value);
        return `
        <div class="card mic-kpi-card">
          <div class="mic-kpi-top">
            <span class="mic-kpi-label">${Utils.escapeHtml(name)}</span>
            <span class="mic-kpi-icon tone-${tone}">${ICONS[meta.icon]}</span>
          </div>
          <div class="mic-kpi-value">${Utils.escapeHtml(entry.value)}</div>
          <div class="progress-track"><div class="progress-fill tone-${tone}" style="width:${pct}%"></div></div>
          <div class="mic-kpi-caption">${Utils.escapeHtml(entry.note || meta.tip)}</div>
        </div>`;
      })
      .join("");
    return `<div class="mic-kpi-grid">${cards}</div>
    <div class="mic-kpi-footnote">* Score do AI tự đánh giá theo REPORT_SPECIFICATION_V2.md — mang tính tham khảo, không phải số liệu thị trường đã kiểm chứng độc lập.</div>`;
  }

  /* ---- Section: Market Overview ---- */
  function marketOverview(mo) {
    const text = (mo && mo.text) || "";
    const table = (mo && mo.table) || null;
    const citations = (mo && mo.citations) || [];
    let html = text
      ? `<p>${Utils.escapeHtml(text)}</p>`
      : `<p class="card-empty">Không đủ dữ liệu.</p>`;
    if (Array.isArray(table) && table.length) {
      const cols = Object.keys(table[0]);
      const head = cols.map((c) => `<th>${Utils.escapeHtml(c)}</th>`).join("");
      const body = table
        .map((r) => `<tr>${cols.map((c) => `<td>${Utils.escapeHtml(r[c])}</td>`).join("")}</tr>`)
        .join("");
      html += `<div class="table-wrap" style="margin-top:var(--sp-4)"><table class="data-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }
    html += citationsHtml(citations);
    return html;
  }

  /* ---- Section: Top Websites (rut gon tu sources) ---- */
  function topWebsites(sources) {
    const list = Utils.safeArray(sources).slice(0, 8);
    if (!list.length) return `<p class="card-empty">Không có dữ liệu.</p>`;
    const max = list.length;
    return list
      .map(
        (s, i) => `
        <div class="mic-rank-row">
          <span class="rank-pill ${i < 3 ? "rank-" + (i + 1) : ""}">${s.rank ?? i + 1}</span>
          <span class="mic-rank-row-name">${Utils.escapeHtml(s.domain || Utils.domainOf(s.url))}</span>
          <span style="flex:2;font-size:12px;color:var(--text-2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${Utils.escapeHtml(s.title || "")}</span>
        </div>`
      )
      .join("");
  }

  /* ---- Section: Sources (bang day du) ---- */
  function sourcesTable(sources) {
    const list = Utils.safeArray(sources);
    if (!list.length) return `<p class="card-empty">Không có nguồn nào được trích dẫn.</p>`;
    const rows = list
      .map((s, i) => {
        const rankClass = i < 3 ? `rank-${i + 1}` : "";
        return `
        <tr>
          <td><span class="rank-pill ${rankClass}">${s.rank ?? i + 1}</span></td>
          <td><span class="source-domain"><span class="source-favicon">${ICONS.globe}</span>${Utils.escapeHtml(s.domain || Utils.domainOf(s.url))}</span></td>
          <td>${Utils.escapeHtml(s.title || "")}</td>
          <td><span class="badge badge-gray">${Utils.escapeHtml(s.source_type || "-")}</span></td>
          <td><a href="${Utils.escapeAttr(s.url)}" target="_blank" rel="noopener">Mở ${ICONS.arrowUpRight}</a></td>
        </tr>`;
      })
      .join("");
    return `<div class="table-wrap"><table class="data-table"><thead><tr><th>#</th><th>Nguồn</th><th>Tiêu đề</th><th>Loại</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  /* ---- Section: Gap (content_angle_mapping) ---- */
  function gapSection(cam) {
    const saturated = Utils.safeArray(cam && cam.saturated);
    const gaps = Utils.safeArray(cam && cam.gaps);
    if (!saturated.length && !gaps.length) return `<p class="card-empty">Không đủ dữ liệu.</p>`;
    const block = (title, items) =>
      items.length
        ? `<p style="font-weight:600;margin-bottom:var(--sp-2)">${title}</p><ul>${items
            .map((it) => `<li>${Utils.escapeHtml(it.text)}${citationsHtml(it.citations)}</li>`)
            .join("")}</ul>`
        : "";
    return `${block("Góc nội dung đã bão hoà", saturated)}<div style="height:var(--sp-4)"></div>${block("Góc nội dung còn trống", gaps)}`;
  }

  function renderDashboard(container, { keyword, report, downloadHref }) {
    const scores = (report.executive_summary && report.executive_summary.scores) || {};

    container.innerHTML = `
      <div class="mic-dash-header">
        <div class="mic-dash-header-left">
          <span class="badge badge-blue">Market Research</span>
          <h1 class="mic-dash-title">Market Intelligence Report — “${Utils.escapeHtml(keyword)}”</h1>
          <div class="mic-dash-meta">${report.source_count || 0} nguồn đã phân tích · Hoàn tất lúc ${Utils.formatDateTime(report.completed_at)}</div>
        </div>
        <div class="mic-dash-actions">
          <button class="btn btn-ghost btn-sm" id="micDownloadBtn">${ICONS.download} Download HTML</button>
          <button class="btn btn-primary btn-sm" id="micAgainBtn">${ICONS.refresh} Research Again</button>
        </div>
      </div>

      ${card({ title: "Executive Dashboard", icon: "compass", subtitle: "10 câu hỏi cốt lõi cho Ban Giám đốc", body: execDashboard(report.executive_summary), extraClass: "mic-exec" })}

      ${kpiGrid(scores)}

      <div class="mic-section-grid">
        ${card({ title: "Market Overview", icon: "layers", body: marketOverview(report.market_overview), span2: true })}

        ${card({ title: "Top Websites", icon: "globe", subtitle: "Nguồn nổi bật nhất", body: topWebsites(report.sources) })}
        ${card({ title: "Competitor", icon: "users", subtitle: "Đối thủ & tín hiệu đầu tư", body:
            genericTableBody(report.top_competitors, [
              { key: "name", label: "Tên" },
              { key: "mention_count", label: "Số nguồn" },
              { key: "source_type", label: "Loại nguồn" },
            ], "Không đủ dữ liệu, chưa xác định được đối thủ cụ thể.") +
            (Utils.safeArray(report.competitor_analysis).length
              ? `<div style="margin-top:var(--sp-4)">${genericTableBody(report.competitor_analysis, [
                  { key: "organization", label: "Tổ chức" },
                  { key: "signal", label: "Tín hiệu đầu tư" },
                  { key: "level", label: "Mức độ" },
                ], "")}</div>`
              : "")
        })}

        ${card({ title: "Key Messages", icon: "file", subtitle: "Thông điệp đối thủ lặp lại nhiều nhất", body:
            genericTableBody(report.message_mapping, [
              { key: "message", label: "Thông điệp" },
              { key: "independent_sources", label: "Số nguồn" },
              { key: "examples", label: "Ví dụ" },
            ], "Chưa đủ dữ liệu để xác định thông điệp chủ đạo.")
        })}
        ${card({ title: "Trend", icon: "trend", subtitle: "Xu hướng thị trường", body: textListBody(report.market_trend, "Không đủ dữ liệu.") })}

        ${card({ title: "Gap", icon: "layers", subtitle: "Khoảng trống nội dung", body: gapSection(report.content_angle_mapping) })}
        ${card({ title: "Opportunity", icon: "bulb", subtitle: "Cơ hội hành động", body: textListBody(report.opportunity_analysis, "Không đủ dữ liệu.") })}

        ${card({ title: "Benchmark", icon: "chart", subtitle: "LinkPower vs Top Competitor", body:
            genericTableBody(report.benchmark, [
              { key: "criteria", label: "Tiêu chí" },
              { key: "linkpower", label: "LinkPower" },
              { key: "top_competitor", label: "Top Competitor" },
              { key: "status", label: "Trạng thái" },
            ], "Chưa đủ dữ liệu Benchmark."), span2: true
        })}

        ${card({ title: "Recommendation", icon: "compass", subtitle: "LinkPower nên đầu tư chủ đề/kênh nào", body: textListBody(report.strategic_recommendation, "Chưa đủ cơ sở để đề xuất chiến lược.") })}
        ${card({ title: "Action Plan", icon: "clock", subtitle: "Lịch hành động 30 / 60 / 90 ngày", body:
            genericTableBody(report.action_plan, [
              { key: "horizon", label: "Mốc" },
              { key: "action", label: "Hành động" },
              { key: "channel", label: "Kênh" },
              { key: "reason", label: "Lý do" },
            ], "Chưa có khuyến nghị để lập kế hoạch hành động.")
        })}

        ${card({ title: "Sources", icon: "link", subtitle: `${Utils.safeArray(report.sources).length} nguồn được AI trích dẫn`, body: sourcesTable(report.sources), span2: true })}
      </div>
    `;
  }

  return { renderDashboard };
})();

/* ---------- 7. LOADING ---------- */
const LOADING_STAGES = [
  { label: "Đang tìm kiếm nguồn dữ liệu", icon: "search" },
  { label: "Đang xếp hạng & phân loại nguồn", icon: "layers" },
  { label: "AI đang phân tích thị trường", icon: "brain" },
  { label: "Đang tổng hợp Dashboard", icon: "chart" },
  { label: "Hoàn tất", icon: "check" },
];

class LoadingController {
  constructor(listEl, keywordEl) {
    this.listEl = listEl;
    this.keywordEl = keywordEl;
    this.timers = [];
    this._build();
  }

  _build() {
    this.listEl.innerHTML = LOADING_STAGES.map(
      (s, i) => `
      <div class="mic-stage-item" data-i="${i}">
        <span class="mic-stage-icon">${ICONS[s.icon]}</span>
        <span>${s.label}</span>
      </div>`
    ).join("");
    this.items = Array.from(this.listEl.querySelectorAll(".mic-stage-item"));
  }

  setKeyword(kw) {
    if (this.keywordEl) this.keywordEl.textContent = `“${kw}”`;
  }

  setStage(index) {
    this.items.forEach((el, i) => {
      el.classList.remove("is-active", "is-done");
      if (i < index) el.classList.add("is-done");
      else if (i === index) el.classList.add("is-active");
    });
  }

  /* Tien trinh mo phong theo thoi gian thuc cua polling - viec that (search+AI)
     dang chay o backend, day chi la nhan phu hop voi tung khoang thoi gian de
     UX khong dung yen mot cho trong luc cho 1 request mang dai. */
  tickByElapsed(elapsedMs) {
    let idx = 0;
    if (elapsedMs > 8000) idx = 1;
    if (elapsedMs > 20000) idx = 2;
    if (elapsedMs > 70000) idx = 3;
    this.setStage(idx);
  }

  reset() {
    this.timers.forEach(clearTimeout);
    this.timers = [];
    this.setStage(-1);
  }
}

/* ---------- 8. APP ---------- */
const App = (() => {
  let state = {
    jobId: null,
    keyword: null,
    pollTimer: null,
    startedAt: null,
    networkErrorCount: 0,
  };

  let els = {};
  let loadingCtrl = null;

  function cacheEls() {
    els.viewHome = document.getElementById("micViewHome");
    els.viewLoading = document.getElementById("micViewLoading");
    els.viewDashboard = document.getElementById("micViewDashboard");
    els.keywordInput = document.getElementById("micKeywordInput");
    els.researchBtn = document.getElementById("micResearchBtn");
    els.homeError = document.getElementById("micHomeError");
    els.examples = document.getElementById("micExamples");
    els.loadingKeyword = document.getElementById("micLoadingKeyword");
    els.stageList = document.getElementById("micStageList");
    els.loadingError = document.getElementById("micLoadingError");
    els.loadingErrorText = document.getElementById("micLoadingErrorText");
    els.backHomeBtn = document.getElementById("micBackHomeBtn");
    els.dashboardRoot = document.getElementById("micDashboardRoot");
    els.footerTime = document.getElementById("micFooterTime");
  }

  function showView(name) {
    els.viewHome.classList.toggle("hidden", name !== "home");
    els.viewLoading.classList.toggle("hidden", name !== "loading");
    els.viewDashboard.classList.toggle("hidden", name !== "dashboard");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function renderExamples() {
    els.examples.innerHTML =
      `<span class="label">Ví dụ:</span>` +
      CONFIG.EXAMPLE_KEYWORDS.map(
        (kw) => `<span class="mic-chip" data-kw="${Utils.escapeAttr(kw)}">${Utils.escapeHtml(kw)}</span>`
      ).join("");
    els.examples.querySelectorAll(".mic-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        els.keywordInput.value = chip.dataset.kw;
        els.keywordInput.focus();
      });
    });
  }

  function showHomeError(msg) {
    els.homeError.textContent = msg;
    els.homeError.classList.remove("hidden");
  }

  function clearHomeError() {
    els.homeError.classList.add("hidden");
  }

  async function startResearch() {
    const keyword = (els.keywordInput.value || "").trim();
    if (!keyword) {
      showHomeError("Vui lòng nhập từ khoá nghiên cứu.");
      return;
    }
    clearHomeError();
    els.researchBtn.disabled = true;

    try {
      const res = await Api.startResearch(keyword);
      state.jobId = res.job_id;
      state.keyword = keyword;
      state.startedAt = Date.now();
      state.networkErrorCount = 0;

      loadingCtrl.reset();
      loadingCtrl.setKeyword(keyword);
      loadingCtrl.setStage(0);
      els.loadingError.classList.add("hidden");
      showView("loading");

      poll();
    } catch (err) {
      showHomeError(err.message || "Không thể bắt đầu Research, thử lại sau.");
    } finally {
      els.researchBtn.disabled = false;
    }
  }

  function poll() {
    clearTimeout(state.pollTimer);
    state.pollTimer = setTimeout(async () => {
      try {
        const elapsed = Date.now() - state.startedAt;
        loadingCtrl.tickByElapsed(elapsed);

        const report = await Api.getReport(state.jobId);
        state.networkErrorCount = 0;

        if (report.status === "completed") {
          loadingCtrl.setStage(4);
          setTimeout(() => showDashboard(report), 400);
          return;
        }
        if (report.status === "failed") {
          showLoadingError(report.error || "AI không thể tạo report cho từ khoá này.");
          return;
        }
        poll(); // van dang "processing" - hoi lai
      } catch (err) {
        state.networkErrorCount += 1;
        if (state.networkErrorCount > CONFIG.POLL_MAX_RETRIES) {
          showLoadingError("Mất kết nối tới máy chủ, vui lòng thử lại.");
          return;
        }
        poll(); // loi mang tam thoi - thu lai, khong huy ngay
      }
    }, CONFIG.POLL_INTERVAL_MS);
  }

  function showLoadingError(msg) {
    els.loadingErrorText.textContent = msg;
    els.loadingError.classList.remove("hidden");
  }

  function showDashboard(report) {
    showView("dashboard");
    Render.renderDashboard(els.dashboardRoot, {
      keyword: state.keyword,
      report,
    });
    document.getElementById("micDownloadBtn").addEventListener("click", downloadHtml);
    document.getElementById("micAgainBtn").addEventListener("click", resetToHome);
  }

  async function downloadHtml() {
    const btn = document.getElementById("micDownloadBtn");
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = "Đang tải...";
    try {
      const html = await Api.getReportHtml(state.jobId);
      const blob = new Blob([html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const safeName = (state.keyword || "report").replace(/[^\p{L}\p{N}_-]+/gu, "_").slice(0, 60);
      const a = document.createElement("a");
      a.href = url;
      a.download = `market-intelligence-${safeName}.html`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Không tải được file HTML: " + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  }

  function resetToHome() {
    clearTimeout(state.pollTimer);
    state = { jobId: null, keyword: null, pollTimer: null, startedAt: null, networkErrorCount: 0 };
    els.keywordInput.value = "";
    clearHomeError();
    showView("home");
  }

  function wireEvents() {
    els.researchBtn.addEventListener("click", startResearch);
    els.keywordInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") startResearch();
    });
    els.backHomeBtn.addEventListener("click", resetToHome);
    document.getElementById("micBrand").addEventListener("click", resetToHome);
  }

  function init() {
    cacheEls();
    loadingCtrl = new LoadingController(els.stageList, els.loadingKeyword);
    renderExamples();
    wireEvents();
    if (els.footerTime) {
      els.footerTime.textContent = new Date().toLocaleString("vi-VN");
    }
    showView("home");
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", App.init);

/* ==========================================================================
   9. CIC — Competitor Intelligence Center (Facebook MVP, Sprint bo sung)
   Module doc lap voi App/Render/LoadingController o tren (khong dung chung
   state) - goi 1 backend RIENG (Competitor Intelligence Center API), tu ve
   idle/loading/result/error cua chinh no trong section #cicSection.
   Tai su dung Utils/ICONS da dinh nghia o tren (Muc 2, 4) va cac class
   component chung .card/.btn/.data-table/.progress-track (khong dung rieng
   cho MIC - xem style.css).
   ========================================================================== */
const Cic = (() => {
  const CONFIG = Object.freeze({
    // Doi URL nay neu Backend CIC tren Render doi domain - dong DUY NHAT can sua.
    // Da xac nhan production that: https://competitor-intelligence-center-api.onrender.com
    API_BASE: "https://competitor-intelligence-center-api.onrender.com",
    // Backend co the mat toi ~180s (APIFY_TIMEOUT_SECONDS) cho Apify + them
    // thoi gian goi AI - dat timeout rong rai o frontend de tranh huy request
    // dang chay binh thuong, nhung van phai co gioi han ro rang (khong cho vo han).
    REQUEST_TIMEOUT_MS: 240000,
  });

  let els = {};

  function cacheEls() {
    els.urlInput = document.getElementById("cicUrlInput");
    els.analyzeBtn = document.getElementById("cicAnalyzeBtn");
    els.error = document.getElementById("cicError");
    els.loading = document.getElementById("cicLoading");
    els.result = document.getElementById("cicResult");
  }

  function normalizeUrl(raw) {
    let url = (raw || "").trim();
    if (!url) return "";
    if (!/^https?:\/\//i.test(url)) url = "https://" + url;
    return url;
  }

  function isLikelyFacebookUrl(url) {
    return /facebook\.com|fb\.com|fb\.watch/i.test(url);
  }

  function showError(msg) {
    els.error.textContent = msg;
    els.error.classList.remove("hidden");
  }

  function clearError() {
    els.error.classList.add("hidden");
  }

  async function analyze() {
    clearError();
    const url = normalizeUrl(els.urlInput.value);
    if (!url) {
      showError("Vui lòng nhập URL Fanpage Facebook.");
      return;
    }
    if (!isLikelyFacebookUrl(url)) {
      showError(
        "URL không hợp lệ — hiện chỉ hỗ trợ Fanpage Facebook (facebook.com/...). LinkedIn/TikTok/YouTube sẽ hỗ trợ ở giai đoạn sau."
      );
      return;
    }

    els.analyzeBtn.disabled = true;
    els.result.classList.add("hidden");
    els.loading.classList.remove("hidden");

    const timeoutController = new AbortController();
    const timeoutId = setTimeout(() => timeoutController.abort(), CONFIG.REQUEST_TIMEOUT_MS);

    try {
      let res;
      try {
        res = await fetch(`${CONFIG.API_BASE}/api/competitor/facebook`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
          signal: timeoutController.signal,
        });
      } catch (networkErr) {
        if (networkErr.name === "AbortError") {
          // Qua CONFIG.REQUEST_TIMEOUT_MS ma backend chua phan hoi - huy request,
          // bao loi ro rang thay vi de nguoi dung cho vo han.
          throw new Error(
            "Quá thời gian chờ phản hồi từ máy chủ phân tích, vui lòng thử lại sau."
          );
        }
        // fetch() tu choi (mat mang, CORS, DNS...) tra ve loi trinh duyet
        // chung chung ("Failed to fetch") - doi thanh thong bao ro rang
        // bang tieng Viet thay vi hien nguyen van cho nguoi dung.
        throw new Error(
          "Không thể kết nối tới máy chủ phân tích, vui lòng kiểm tra kết nối mạng và thử lại."
        );
      }

      let data = null;
      try {
        data = await res.json();
      } catch (e) {
        /* noop - phan loi xu ly ben duoi bang res.ok */
      }

      if (!res.ok) {
        const detail =
          (data && data.detail) || `Không thể phân tích (HTTP ${res.status}).`;
        throw new Error(detail);
      }
      renderResult(data);
    } catch (err) {
      showError(
        err.message ||
          "Có lỗi không mong muốn xảy ra, vui lòng thử lại sau."
      );
    } finally {
      clearTimeout(timeoutId);
      els.loading.classList.add("hidden");
      els.analyzeBtn.disabled = false;
    }
  }

  /* ---- render helpers ---- */

  function card(title, bodyHtml, span2) {
    return `
    <div class="card card-pad ${span2 ? "cic-span-2" : ""}">
      <div class="card-header">
        <div class="card-title-group"><div class="card-title">${Utils.escapeHtml(title)}</div></div>
      </div>
      <div class="card-body">${bodyHtml}</div>
    </div>`;
  }

  function metricCard(label, value) {
    return `
    <div class="card cic-metric-card">
      <div class="cic-metric-label">${Utils.escapeHtml(label)}</div>
      <div class="cic-metric-value">${Utils.escapeHtml(String(value))}</div>
    </div>`;
  }

  function listOrEmpty(items) {
    const list = Utils.safeArray(items);
    if (!list.length) return `<p class="card-empty">Không đủ dữ liệu.</p>`;
    return `<ul>${list.map((i) => `<li>${Utils.escapeHtml(i)}</li>`).join("")}</ul>`;
  }

  function barChart(entries) {
    const list = Utils.safeArray(entries);
    if (!list.length) return `<p class="card-empty">Không đủ dữ liệu.</p>`;
    return list
      .map(
        (e) => `
      <div class="cic-bar-row">
        <span class="cic-bar-label">${Utils.escapeHtml(e.type || e.tone || "-")}</span>
        <div class="cic-bar-track progress-track"><div class="progress-fill" style="width:${Math.max(e.percentage || 0, 3)}%"></div></div>
        <span class="cic-bar-pct">${e.percentage ?? 0}%</span>
      </div>`
      )
      .join("");
  }

  function postList(posts) {
    const list = Utils.safeArray(posts).slice(0, 5);
    if (!list.length) return `<p class="card-empty">Không đủ dữ liệu.</p>`;
    return list
      .map(
        (p, i) => `
      <div class="cic-post-item">
        <span class="cic-post-rank">#${i + 1}</span>
        <div class="cic-post-body">
          <div class="cic-post-reason">${Utils.escapeHtml(p.reason || "")}</div>
          <a class="cic-post-link" href="${Utils.escapeAttr(p.permalink)}" target="_blank" rel="noopener">${Utils.escapeHtml(p.permalink)}</a>
        </div>
      </div>`
      )
      .join("");
  }

  function benchmarkTable(benchmark) {
    const rows = Utils.safeArray(benchmark && benchmark.rows);
    if (!rows.length) return `<p class="card-empty">Không đủ dữ liệu Benchmark.</p>`;
    const body = rows
      .map(
        (r) => `
      <tr>
        <td>${Utils.escapeHtml(r.criteria)}</td>
        <td>${Utils.escapeHtml(r.linkpower)}</td>
        <td>${Utils.escapeHtml(r.competitor)}</td>
        <td><span class="badge badge-gray">${Utils.escapeHtml(r.status)}</span></td>
      </tr>`
      )
      .join("");
    return `<div class="table-wrap"><table class="data-table"><thead><tr><th>Tiêu chí</th><th>LinkPower</th><th>Đối thủ</th><th>Trạng thái</th></tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function extractAvgLikes(benchmark) {
    const rows = Utils.safeArray(benchmark && benchmark.rows);
    const row = rows.find((r) => (r.criteria || "").indexOf("Engagement trung bình") !== -1);
    return row ? row.competitor : "Không đủ dữ liệu";
  }

  const DATA_STATUS_LABELS = {
    complete: { text: "Đầy đủ", tone: "badge-green" },
    partial: { text: "Một phần", tone: "badge-orange" },
    insufficient: { text: "Không đủ dữ liệu", tone: "badge-gray" },
  };

  function renderResult(report) {
    const a = report.account_overview || {};
    const completeness = report.completeness || {};
    const es = report.executive_summary || {};
    const pillars = (report.content_analysis && report.content_analysis.content_pillars) || [];
    const topPillar = pillars.length
      ? pillars.slice().sort((x, y) => (y.percentage || 0) - (x.percentage || 0))[0]
      : null;
    const pubPattern = report.publishing_pattern || {};
    const postsCollected = completeness.competitor_posts_collected ?? 0;
    const postsAnalyzed = report.posts_analyzed ?? postsCollected;
    const statusMeta = DATA_STATUS_LABELS[report.data_status] || DATA_STATUS_LABELS.insufficient;

    els.result.innerHTML = `
      <div class="cic-result-header">
        <div>
          <span class="badge badge-blue">Facebook</span>
          <span class="badge ${statusMeta.tone} cic-status-badge">${Utils.escapeHtml(statusMeta.text)}</span>
          <h3 class="cic-result-title">${Utils.escapeHtml(a.display_name || "(Không rõ tên trang)")}</h3>
          <div class="cic-result-counts">
            <span>Đã thu thập: <strong>${postsCollected}</strong> bài</span>
            <span>Đã phân tích: <strong>${postsAnalyzed}</strong> bài</span>
            <span>Thời điểm phân tích: <strong>${Utils.escapeHtml(Utils.formatDateTime(report.generated_at))}</strong></span>
          </div>
        </div>
      </div>

      <div class="cic-metric-grid">
        ${metricCard("Followers", a.scale || "Không đủ dữ liệu")}
        ${metricCard("Likes trung bình/bài", extractAvgLikes(report.benchmark))}
        ${metricCard("Số bài phân tích", postsAnalyzed)}
        ${metricCard("Tần suất đăng bài", `${pubPattern.posts_per_week_avg ?? 0} bài/tuần`)}
      </div>

      <div class="cic-section-grid">
        ${card(
          "AI Summary",
          `<p>${Utils.escapeHtml(es.ai_summary)}</p><p>${Utils.escapeHtml(es.overview)}</p><p><em>${Utils.escapeHtml(es.data_confidence_note)}</em></p>`,
          true
        )}

        ${card("Top 5 bài nổi bật", postList(report.engagement_analysis && report.engagement_analysis.top_performing_posts))}
        ${card(
          "Top Content Pillar",
          topPillar
            ? `<p><strong>${Utils.escapeHtml(topPillar.pillar)}</strong> — ${topPillar.percentage}% (${topPillar.post_count} bài)</p>`
            : `<p class="card-empty">Không đủ dữ liệu.</p>`
        )}

        ${card("Hook thường dùng", listOrEmpty(report.content_style && report.content_style.hook_patterns))}
        ${card("CTA thường dùng", listOrEmpty(report.content_style && report.content_style.cta_patterns))}

        ${card("Phân bố loại nội dung", barChart(report.content_analysis && report.content_analysis.content_type_breakdown))}
        ${card("Điểm Benchmark với LinkPower", benchmarkTable(report.benchmark), true)}
      </div>
    `;
    els.result.classList.remove("hidden");
    els.result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function wireEvents() {
    els.analyzeBtn.addEventListener("click", analyze);
    els.urlInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") analyze();
    });
  }

  function init() {
    cacheEls();
    wireEvents();
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", Cic.init);

/* ==========================================================================
   10. BENCHMARK — Social Competitor Benchmark (Ver 3, Sprint V3.2)
   Module doc lap voi App/Cic o tren (khong dung chung state) - goi
   /api/v3/benchmark/* tren CUNG 1 backend voi Cic (Competitor Intelligence
   Center API), tu ve toan bo flow (tao du an -> them thuong hieu/kenh ->
   chay phan tich -> hien report) trong section #benchmarkSection. Tai su
   dung Utils/ICONS da dinh nghia o tren (Muc 2, 4) va cac class component
   chung .card/.btn/.data-table/.badge/.progress-track (khong dung rieng -
   xem style.css Muc 9 "SOCIAL COMPETITOR BENCHMARK").
   ========================================================================== */
const Benchmark = (() => {
  const CONFIG = Object.freeze({
    // Cung backend voi Cic (route moi /api/v3/* duoc mount them, khong doi
    // domain) - xem docs/ver3/V3_ARCHITECTURE.md muc 11.
    API_BASE: "https://competitor-intelligence-center-api.onrender.com",
    // Chay dong bo (giong Cic) - co the mat toi vai phut neu nhieu kenh +
    // provider that (Apify) duoc cau hinh, dat timeout rong rai o frontend.
    REQUEST_TIMEOUT_MS: 240000,
  });

  const JOB_STATUS_LABELS = {
    pending: { text: "Đang chờ", tone: "badge-gray" },
    collecting: { text: "Đang thu thập", tone: "badge-blue" },
    collected: { text: "Đã thu thập", tone: "badge-green" },
    partially_collected: { text: "Thu thập một phần", tone: "badge-orange" },
    failed: { text: "Thất bại", tone: "badge-gray" },
    requires_manual_input: { text: "Cần nhập thủ công", tone: "badge-orange" },
  };

  let state = { projectId: null, brands: [] };
  let els = {};

  function cacheEls() {
    els.projectName = document.getElementById("bmkProjectName");
    els.objective = document.getElementById("bmkObjective");
    els.dateRange = document.getElementById("bmkDateRange");
    els.contentLimit = document.getElementById("bmkContentLimit");
    els.createProjectBtn = document.getElementById("bmkCreateProjectBtn");
    els.projectError = document.getElementById("bmkProjectError");
    els.brandCard = document.getElementById("bmkBrandCard");
    els.brandName = document.getElementById("bmkBrandName");
    els.brandType = document.getElementById("bmkBrandType");
    els.addBrandBtn = document.getElementById("bmkAddBrandBtn");
    els.brandError = document.getElementById("bmkBrandError");
    els.brandList = document.getElementById("bmkBrandList");
    els.runCard = document.getElementById("bmkRunCard");
    els.runBtn = document.getElementById("bmkRunBtn");
    els.runError = document.getElementById("bmkRunError");
    els.runLoading = document.getElementById("bmkRunLoading");
    els.jobList = document.getElementById("bmkJobList");
    els.reportRoot = document.getElementById("bmkReportRoot");
  }

  function showError(el, msg) {
    el.textContent = msg;
    el.classList.remove("hidden");
  }
  function clearError(el) {
    el.classList.add("hidden");
  }

  /* ---- API ---- */
  async function apiRequest(path, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT_MS);
    let res;
    try {
      res = await fetch(`${CONFIG.API_BASE}${path}`, { ...options, signal: controller.signal });
    } catch (networkErr) {
      clearTimeout(timeoutId);
      if (networkErr.name === "AbortError") {
        throw new Error("Quá thời gian chờ phản hồi từ máy chủ, vui lòng thử lại sau.");
      }
      throw new Error("Không thể kết nối tới máy chủ phân tích, vui lòng kiểm tra kết nối mạng.");
    }
    clearTimeout(timeoutId);

    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      /* noop */
    }
    if (!res.ok) {
      throw new Error((data && data.detail) || `Lỗi API (HTTP ${res.status})`);
    }
    return data;
  }

  const Api = {
    createProject: (payload) =>
      apiRequest("/api/v3/benchmark/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    addBrand: (projectId, payload) =>
      apiRequest(`/api/v3/benchmark/projects/${projectId}/brands`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    addChannel: (projectId, payload) =>
      apiRequest(`/api/v3/benchmark/projects/${projectId}/channels`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    deleteChannel: (channelId) =>
      apiRequest(`/api/v3/benchmark/channels/${channelId}`, { method: "DELETE" }),
    runProject: (projectId) =>
      apiRequest(`/api/v3/benchmark/projects/${projectId}/run`, { method: "POST" }),
    getJobs: (projectId) => apiRequest(`/api/v3/benchmark/projects/${projectId}/jobs`),
    retryJob: (jobId) => apiRequest(`/api/v3/benchmark/jobs/${jobId}/retry`, { method: "POST" }),
    getReport: (projectId) => apiRequest(`/api/v3/benchmark/projects/${projectId}/report`),
    importFile: (channelId, file) => {
      const form = new FormData();
      form.append("channel_id", channelId);
      form.append("file", file);
      // KHONG tu dat Content-Type - trinh duyet tu dat multipart boundary dung.
      return apiRequest("/api/v3/benchmark/import", { method: "POST", body: form });
    },
  };

  /* ---- Buoc 1: Project ---- */
  async function createProject() {
    const name = (els.projectName.value || "").trim();
    if (!name) {
      showError(els.projectError, "Vui lòng nhập tên dự án.");
      return;
    }
    clearError(els.projectError);
    els.createProjectBtn.disabled = true;
    try {
      const project = await Api.createProject({
        name,
        objective: (els.objective.value || "").trim() || null,
        date_range_days: parseInt(els.dateRange.value, 10) || 90,
        content_limit: parseInt(els.contentLimit.value, 10) || 30,
      });
      state.projectId = project.id;
      state.brands = [];
      els.brandCard.classList.remove("hidden");
      els.runCard.classList.add("hidden");
      els.reportRoot.classList.add("hidden");
      renderBrandList();
      els.brandCard.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      showError(els.projectError, err.message || "Không thể tạo dự án, thử lại sau.");
    } finally {
      els.createProjectBtn.disabled = false;
    }
  }

  /* ---- Buoc 2-3: Brand & Channel ---- */
  async function addBrand() {
    const name = (els.brandName.value || "").trim();
    const brand_type = els.brandType.value;
    if (!name) {
      showError(els.brandError, "Vui lòng nhập tên thương hiệu.");
      return;
    }
    clearError(els.brandError);
    els.addBrandBtn.disabled = true;
    try {
      const brand = await Api.addBrand(state.projectId, { name, brand_type });
      state.brands.push({ ...brand, channels: [] });
      els.brandName.value = "";
      renderBrandList();
    } catch (err) {
      showError(els.brandError, err.message || "Không thể thêm thương hiệu.");
    } finally {
      els.addBrandBtn.disabled = false;
    }
  }

  function renderBrandList() {
    els.brandList.innerHTML = state.brands
      .map(
        (brand) => `
      <div class="bmk-brand-block">
        <div class="bmk-brand-block-header">
          <span class="bmk-brand-name">${Utils.escapeHtml(brand.name)}</span>
          <span class="badge ${brand.brand_type === "linkpower" ? "badge-blue" : "badge-gray"}">${
            brand.brand_type === "linkpower" ? "LinkPower" : "Đối thủ"
          }</span>
        </div>
        <div class="bmk-channel-row">
          <input type="text" class="bmk-channel-url-input" placeholder="Dán URL Facebook/LinkedIn/TikTok..." data-brand-id="${brand.id}">
          <button class="btn btn-ghost btn-sm bmk-add-channel-btn" data-brand-id="${brand.id}">+ Thêm kênh</button>
        </div>
        <div class="bmk-channel-error mic-error hidden" data-brand-id="${brand.id}"></div>
        <div class="bmk-channel-items">
          ${
            brand.channels
              .map(
                (ch) => `
            <div class="bmk-channel-item">
              <span class="badge badge-blue">${Utils.escapeHtml(ch.platform)}</span>
              <span class="bmk-channel-url">${Utils.escapeHtml(ch.normalized_url)}</span>
              <button class="bmk-channel-remove" data-channel-id="${ch.id}" data-brand-id="${brand.id}">Xoá</button>
            </div>`
              )
              .join("") || `<p class="card-empty">Chưa có kênh nào.</p>`
          }
        </div>
      </div>`
      )
      .join("");

    els.brandList.querySelectorAll(".bmk-add-channel-btn").forEach((btn) => {
      btn.addEventListener("click", () => addChannel(btn.dataset.brandId));
    });
    els.brandList.querySelectorAll(".bmk-channel-remove").forEach((btn) => {
      btn.addEventListener("click", () => removeChannel(btn.dataset.brandId, btn.dataset.channelId));
    });
  }

  async function addChannel(brandId) {
    const input = els.brandList.querySelector(`.bmk-channel-url-input[data-brand-id="${brandId}"]`);
    const errorEl = els.brandList.querySelector(`.bmk-channel-error[data-brand-id="${brandId}"]`);
    const url = (input.value || "").trim();
    if (!url) {
      showError(errorEl, "Vui lòng nhập URL.");
      return;
    }
    clearError(errorEl);
    try {
      const channel = await Api.addChannel(state.projectId, { brand_id: brandId, url });
      const brand = state.brands.find((b) => b.id === brandId);
      brand.channels.push(channel);
      input.value = "";
      renderBrandList();
      checkRunReady();
    } catch (err) {
      showError(errorEl, err.message || "Không thể thêm kênh.");
    }
  }

  async function removeChannel(brandId, channelId) {
    try {
      await Api.deleteChannel(channelId);
      const brand = state.brands.find((b) => b.id === brandId);
      brand.channels = brand.channels.filter((c) => c.id !== channelId);
      renderBrandList();
      checkRunReady();
    } catch (err) {
      alert(err.message || "Không thể xoá kênh.");
    }
  }

  function checkRunReady() {
    const hasLinkPower = state.brands.some((b) => b.brand_type === "linkpower" && b.channels.length);
    const hasCompetitor = state.brands.some((b) => b.brand_type === "competitor" && b.channels.length);
    els.runCard.classList.toggle("hidden", !(hasLinkPower && hasCompetitor));
  }

  /* ---- Buoc 4: Run ---- */
  async function runProject() {
    clearError(els.runError);
    els.runBtn.disabled = true;
    els.runLoading.classList.remove("hidden");
    els.reportRoot.classList.add("hidden");
    try {
      await Api.runProject(state.projectId);
      await refreshJobsAndReport();
    } catch (err) {
      showError(els.runError, err.message || "Không thể chạy phân tích, thử lại sau.");
    } finally {
      els.runLoading.classList.add("hidden");
      els.runBtn.disabled = false;
    }
  }

  async function refreshJobsAndReport() {
    const jobsRes = await Api.getJobs(state.projectId);
    renderJobs(jobsRes.items);
    try {
      const report = await Api.getReport(state.projectId);
      renderReport(report.full_report);
    } catch (err) {
      /* co the chua co report (vd tat ca channel deu requires_manual_input) -
         khong coi la loi fatal, chi khong hien report */
    }
  }

  function channelInfoMap() {
    const map = {};
    state.brands.forEach((b) =>
      b.channels.forEach((c) => {
        map[c.id] = { platform: c.platform, brandName: b.name };
      })
    );
    return map;
  }

  function renderJobs(jobs) {
    const info = channelInfoMap();
    els.jobList.innerHTML =
      jobs
        .map((job) => {
          const meta = info[job.channel_id] || { platform: "?", brandName: "?" };
          const statusMeta = JOB_STATUS_LABELS[job.status] || { text: job.status, tone: "badge-gray" };
          const needsRetry = job.status === "failed";
          const needsImport = job.status === "requires_manual_input";
          return `
        <div class="bmk-job-row">
          <span class="bmk-job-channel">${Utils.escapeHtml(meta.brandName)} (${Utils.escapeHtml(meta.platform)})</span>
          <span class="badge ${statusMeta.tone}">${statusMeta.text}</span>
          <span>${job.posts_collected != null ? job.posts_collected + " bài" : ""}</span>
          <div class="bmk-job-actions">
            ${needsRetry ? `<button class="btn btn-ghost btn-sm bmk-retry-btn" data-job-id="${job.id}">Thử lại</button>` : ""}
            ${
              needsImport
                ? `<form class="bmk-import-form" data-channel-id="${job.channel_id}">
                     <input type="file" accept=".csv,.json" class="bmk-import-file">
                     <button type="submit" class="btn btn-ghost btn-sm">Nhập dữ liệu</button>
                   </form>`
                : ""
            }
          </div>
          ${job.error_reason ? `<div class="bmk-job-reason">${Utils.escapeHtml(job.error_reason)}</div>` : ""}
        </div>`;
        })
        .join("") || `<p class="card-empty">Chưa có job nào.</p>`;

    els.jobList.querySelectorAll(".bmk-retry-btn").forEach((btn) => {
      btn.addEventListener("click", () => retryJob(btn.dataset.jobId));
    });
    els.jobList.querySelectorAll(".bmk-import-form").forEach((form) => {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        const file = form.querySelector(".bmk-import-file").files[0];
        if (file) importChannelFile(form.dataset.channelId, file);
      });
    });
  }

  async function retryJob(jobId) {
    els.runLoading.classList.remove("hidden");
    try {
      await Api.retryJob(jobId);
      await refreshJobsAndReport();
    } catch (err) {
      alert(err.message || "Không thể thử lại kênh này.");
    } finally {
      els.runLoading.classList.add("hidden");
    }
  }

  async function importChannelFile(channelId, file) {
    els.runLoading.classList.remove("hidden");
    try {
      const result = await Api.importFile(channelId, file);
      alert(
        `Đã nhập ${result.imported_count}/${result.total_rows} dòng hợp lệ. ` +
          `Bấm "Chạy Benchmark" để phân tích lại với dữ liệu mới.`
      );
      const jobsRes = await Api.getJobs(state.projectId);
      renderJobs(jobsRes.items);
    } catch (err) {
      alert(err.message || "Không thể nhập dữ liệu, kiểm tra lại định dạng file.");
    } finally {
      els.runLoading.classList.add("hidden");
    }
  }

  /* ---- Buoc 5: Report ---- */
  function renderReport(report) {
    if (!report) return;
    const es = report.executive_summary || {};
    const ranking = Utils.safeArray(report.brand_ranking);
    const platformBenchmark = report.platform_benchmark || {};
    const recs = Utils.safeArray(report.recommendations);
    const gap = report.competitive_gap || {};

    const platformCards = Object.entries(platformBenchmark)
      .map(
        ([platform, entry]) => `
      <div class="card card-pad">
        <div class="card-header"><div class="card-title-group"><div class="card-title">Benchmark trên ${Utils.escapeHtml(platform)}</div></div></div>
        <div class="card-body">
          ${Utils.safeArray(entry.one_vs_one)
            .map(
              (cmp) =>
                `<p><strong>vs ${Utils.escapeHtml(cmp.competitor || "")}</strong> — <span class="badge badge-gray">${Utils.escapeHtml(cmp.overall_status)}</span> (độ tin cậy: ${Utils.escapeHtml(cmp.confidence_score)})</p>`
            )
            .join("")}
          ${
            entry.one_vs_group
              ? `<p><strong>So với nhóm đối thủ</strong> — <span class="badge badge-gray">${Utils.escapeHtml(entry.one_vs_group.overall_status)}</span></p>
                 <div class="bmk-sample-note">${Utils.escapeHtml(entry.one_vs_group.sample_note || "")}</div>`
              : ""
          }
        </div>
      </div>`
      )
      .join("");

    els.reportRoot.innerHTML = `
      <div class="card card-pad">
        <div class="card-header"><div class="card-title-group"><div class="card-title">Tổng quan (Executive Summary)</div></div></div>
        <div class="card-body">
          <p>${Utils.escapeHtml(es.linkpower_overview || "")}</p>
          <p>Đối thủ mạnh nhất: <strong>${Utils.escapeHtml(es.strongest_competitor || "Không đủ dữ liệu")}</strong></p>
          <p>Khoảng trống lớn nhất: <strong>${Utils.escapeHtml(es.biggest_gap || "Không đủ dữ liệu")}</strong></p>
          <ul>${Utils.safeArray(es.top_3_actions).map((a) => `<li>${Utils.escapeHtml(a)}</li>`).join("")}</ul>
        </div>
      </div>

      <div class="card card-pad">
        <div class="card-header"><div class="card-title-group"><div class="card-title">Xếp hạng thương hiệu</div></div></div>
        <div class="card-body">
          <div class="table-wrap"><table class="data-table">
            <thead><tr><th>Thương hiệu</th><th>Nền tảng</th><th>Overall</th><th>Engagement</th><th>Activity</th><th>Độ tin cậy</th></tr></thead>
            <tbody>${ranking
              .map(
                (r) => `
              <tr>
                <td>${Utils.escapeHtml(r.brand)}</td>
                <td>${Utils.escapeHtml(r.platform)}</td>
                <td>${r.overall_score ?? "-"}</td>
                <td>${r.engagement_score ?? "-"}</td>
                <td>${r.activity_score ?? "-"}</td>
                <td><span class="badge badge-gray">${Utils.escapeHtml(r.confidence)}</span></td>
              </tr>`
              )
              .join("")}</tbody>
          </table></div>
        </div>
      </div>

      ${platformCards}

      <div class="card card-pad">
        <div class="card-header"><div class="card-title-group"><div class="card-title">Khoảng trống nội dung so với đối thủ</div></div></div>
        <div class="card-body">
          <div class="bmk-gap-list">
            ${
              Utils.safeArray(gap.competitor_doing_linkpower_not)
                .map((p) => `<span class="bmk-gap-chip">${Utils.escapeHtml(p)}</span>`)
                .join("") || `<p class="card-empty">Không đủ dữ liệu.</p>`
            }
          </div>
        </div>
      </div>

      <div class="card card-pad">
        <div class="card-header"><div class="card-title-group"><div class="card-title">Đề xuất hành động</div></div></div>
        <div class="card-body">
          <div class="table-wrap"><table class="data-table">
            <thead><tr><th>Nền tảng</th><th>Nội dung</th><th>Ưu tiên</th><th>Lý do</th><th>Mốc</th></tr></thead>
            <tbody>${recs
              .map(
                (r) => `
              <tr>
                <td>${Utils.escapeHtml(r.platform)}</td>
                <td>${Utils.escapeHtml(r.content_type)}</td>
                <td><span class="badge ${r.priority === "high" ? "badge-orange" : "badge-gray"}">${Utils.escapeHtml(r.priority)}</span></td>
                <td>${Utils.escapeHtml(r.reason)}</td>
                <td>${Utils.escapeHtml(r.horizon)}</td>
              </tr>`
              )
              .join("")}</tbody>
          </table></div>
        </div>
      </div>
    `;
    els.reportRoot.classList.remove("hidden");
    els.reportRoot.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function wireEvents() {
    els.createProjectBtn.addEventListener("click", createProject);
    els.addBrandBtn.addEventListener("click", addBrand);
    els.runBtn.addEventListener("click", runProject);
  }

  function init() {
    cacheEls();
    wireEvents();
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", Benchmark.init);

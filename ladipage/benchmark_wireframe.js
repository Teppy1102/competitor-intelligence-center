/* ==========================================================================
   Social Competitor Benchmark — component skeleton (Sprint V3.1 wireframe)

   KHONG duoc <script> include vao ladipage/index.html production o Sprint
   nay - file nay CHUA wire API that (chua co route /api/v3/* de goi, xem
   docs/ver3/V3_ARCHITECTURE.md muc 11 "Sprint V3.1 khong wire route song").
   Day la CHU KY HAM (contract) cho Sprint V3.2 implement than ham, giu dung
   pattern IIFE + Utils/ICONS dung chung da co o app.js (module App/Cic),
   KHONG duoc sua app.js hien co o Sprint nay.
   ========================================================================== */

const Benchmark = (() => {
  /**
   * Ve UI chon nen tang (Facebook bat, LinkedIn/TikTok disabled + tooltip
   * "sap co") - xem docs/ver3/V3_UI_WIREFRAME.md muc 2.
   * @param {HTMLElement} container
   * @param {{onChange: (platforms: string[]) => void}} handlers
   */
  function renderPlatformSelector(container, { onChange } = {}) {
    throw new Error("Chưa implement — Sprint V3.2 (xem V3_UI_WIREFRAME.md mục 2)");
  }

  /**
   * Form nhap 1 kenh LinkPower + N doi thu (V3_UI_WIREFRAME.md muc 3).
   * @param {HTMLElement} container
   * @param {{onSubmit: (payload: {linkpower: object, competitors: object[]}) => void}} handlers
   */
  function renderBrandForm(container, { onSubmit } = {}) {
    throw new Error("Chưa implement — Sprint V3.2 (xem V3_UI_WIREFRAME.md mục 3)");
  }

  /**
   * Danh sach kenh + badge trang thai CollectionStatus (V3_UI_WIREFRAME.md muc 5).
   * @param {HTMLElement} container
   * @param {Array<{name: string, platform: string, status: string}>} channels
   */
  function renderChannelStatusList(container, channels) {
    throw new Error("Chưa implement — Sprint V3.2 (xem V3_UI_WIREFRAME.md mục 5)");
  }

  /**
   * Thong bao loi khong chan toan bo flow (V3_UI_WIREFRAME.md muc 7).
   * @param {HTMLElement} container
   * @param {Array<{channel: string, reason: string}>} failedChannels
   * @param {{onContinue: () => void, onCancel: () => void}} handlers
   */
  function renderErrorState(container, failedChannels, { onContinue, onCancel } = {}) {
    throw new Error("Chưa implement — Sprint V3.2 (xem V3_UI_WIREFRAME.md mục 7)");
  }

  /** Trang thai chua chay benchmark nao (V3_UI_WIREFRAME.md muc 8). */
  function renderEmptyState(container) {
    throw new Error("Chưa implement — Sprint V3.2 (xem V3_UI_WIREFRAME.md mục 8)");
  }

  /**
   * Dashboard tong hop - tai dung genericTableBody()/barChart()/metricCard()
   * da co trong module Cic cua app.js (V3_UI_WIREFRAME.md muc 9), KHONG viet
   * lai component dung chung.
   * @param {HTMLElement} container
   * @param {object} benchmarkRun - report.json cua 1 BenchmarkRun (V3_DATA_MODEL.md)
   */
  function renderDashboard(container, benchmarkRun) {
    throw new Error("Chưa implement — Sprint V3.2 (xem V3_UI_WIREFRAME.md mục 9)");
  }

  return {
    renderPlatformSelector,
    renderBrandForm,
    renderChannelStatusList,
    renderErrorState,
    renderEmptyState,
    renderDashboard,
  };
})();

/* Khong goi Benchmark.init() hay dang ky DOMContentLoaded o day - file nay
   chua duoc include vao trang production (xem ghi chu dau file). */

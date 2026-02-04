# CDU 智慧冷卻分配單元控制系統 (Coolant Distribution Unit Web Control)

**專案概述**：
為資料中心 (Data Center) 液冷散熱系統開發的新一代 Web 監控介面。擺脫傳統工業控制醜陋刻板的印象，導入現代化 **Cyberpunk/Dark Mode** 設計風格，結合高效率的 **Vue 3** 框架與 **SVG** 動態視覺化技術，打造出戰情室等級的即時監控系統。

**擔任角色**：前端工程師 / 系統架構規劃
**技術堆疊**：Vue.js 3 (Composition API), Vite, Tailwind CSS, Axios, HTML5/CSS3 (Grid/Flex), RWD, Git

---

## 💻 專案亮點與技術成就 (Key Achievements)

### 1. **工業級可視化儀表板 (SCADA-like Visualization)**
*   **技術運用**: 深入運用 **SVG (Scalable Vector Graphics)** 結合 Vue 資料綁定。
*   **具體展現**: 
    *   捨棄傳統圖表套件，**自行開發動態系統架構圖 (System Diagram)**。將水路流向、水箱液位、泵浦運轉狀態與管路溫度，透過 SVG 路徑計算與 CSS 動畫即時呈現。
    *   實作 **客製化趨勢圖 (Trend Chart)**，不依賴第三方龐大套件 (如 ECharts)，直接使用 Native SVG Path 繪製即時溫度/壓力曲線，大幅降低 bundle size 並提升渲染效能。
    *   **成效**: 實現了每秒 60fps 的流暢數據刷新，並精確還原實體管路邏輯。

### 2. **戰情室大屏模式 (Kiosk Mode / War Room Display)**
*   **技術運用**: **Fullscreen API**, Event Listeners, Router Guards, CSS Layout Optimization.
*   **具體展現**:
    *   開發專用的 **Kiosk Mode**，整合 `requestFullscreen` API，一鍵切換為無邊框全螢幕監控模式。
    *   實作 **自動輪播機制 (Auto-Rotation)**，利用 `setInterval` 與 Vue Router 在「系統狀態」與「歷史趨勢」間自動切換，滿足無人值守的戰情室需求。
    *   **UX 優化**: 加入鍵盤事件監聽 (`ESC`) 與滑鼠防呆機制，確保操作體驗流暢且防誤觸。

### 3. **現代化響應式 UI 架構 (Modern Responsive UI)**
*   **技術運用**: **Tailwind CSS**, CSS Variables, Glassmorphism (玻璃擬態).
*   **具體展現**:
    *   主導 UI 設計改版，採用 **Dark Theme (深色模式)** 結合霓虹配色 (Cyan/Orange)，提升科技感並降低長期監控的視覺疲勞。
    *   大量運用 **Glassmorphism** (背景模糊) 與 **Grid Layout**，解決工業數據繁雜且難以閱讀的痛點，將 PID 參數、網路設定、感測器數值進行模組化呈現。
    *   **成效**: 介面操作直覺度提升，不僅是控制台，更成為展示產品技術力的行銷利器。

### 4. **複雜狀態管理與即時通訊 (State Management & Real-time Data)**
*   **技術運用**: **Vue Composition API (ref/reactive/computed)**, Async/Await, Axios Interceptors.
*   **具體展現**:
    *   設計 **雙模式數據源 (Dual-Mode Data Source)** 架構：即時模式 (Live) 串接 RESTful API；模擬模式 (Sim) 內建正弦波產生器，方便在無硬體環境下進行展示與除錯。
    *   **PID 參數調校介面**: 開發複雜表單處理 PID (Proportional-Integral-Derivative) 控制參數，不僅是數據顯示，更涉及複雜的表單驗證與即時寫入邏輯。
    *   **網路組態管理**: 實作動態網卡管理介面，處理 IPv4/IPv6 雙堆疊設定，展現對複雜資料結構的處理能力。

---

## 🚀 面試官可能感興趣的細節 (Technical Deep Dive)

*   **為什麼選擇 SVG 而不是 Canvas 或 ECharts?**
    *   *回答策略*：強調「DOM 互動性」與「開發效率」。本專案需要針對管路特定部位 (如閥件開關、水箱水位) 進行 CSS 樣式控制 (變色、閃爍)，SVG 結合 Vue Template 可以直接綁定 Class，比 Canvas 更容易維護且不僅僅是「畫圖」，而是「構建介面」。
*   **如何處理大量即時數據的效能?**
    *   *回答策略*：強調「與其優化渲染，不如優化邏輯」。在 Trends 圖表中，使用 FIFO (先進先出) 陣列管理數據點，並限制最大點數 (Max Points)，確保 SVG Path 字串長度可控，避免記憶體洩漏 (Memory Leak)。
*   **Tailwind CSS 在此專案的優勢?**
    *   *回答策略*：強調「開發速度」與「一致性」。利用 Tailwind 的 Utility-first 特性，快速堆疊出統一的深色系配色與排版，無需撰寫大量 CSS 檔案，大幅縮短 UI 迭代週期 (Iterative Cycle)。

---

## 📊 職能關鍵字 (Keywords for ATS)
Vue.js, Vue 3, Composition API, Vite, Tailwind CSS, JavaScript (ES6+), SVG Visualization, RWD, Axios, RESTful API, Frontend Architecture, Industrial Control, UI/UX Design, Git.

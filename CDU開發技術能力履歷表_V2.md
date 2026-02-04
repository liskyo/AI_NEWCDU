# CDU (Coolant Distribution Unit) 智能監控系統開發

## 📌 專案簡介
本專案為高階液冷散熱系統 (Liquid Cooling) 的核心監控平台。負責將原本基於傳統 SSR (Server Side Rendering) 與 jQuery 的舊架構，全面重構為基於 **Vue 3 + Vite** 的現代化單頁應用程式 (SPA)。系統需即時處理數十個感測器 (溫度、壓力、流量) 的數據回傳，並提供工程師精密的 PID 參數調校介面。

## 🛠️ 技術關鍵字 (Tech Stack)
**Vue.js 3 (Composition API)**, **Vite**, **Tailwind CSS**, **Container Queries (RWD)**, **Axios**, **Modbus/PLC Integration**

## 🚀 專案亮點與具體貢獻 (Key Achievements)

### 1. 舊系統現代化重構 (Legacy Modernization)
- **挑戰**: 原有系統前後端耦合嚴重 (Flask + Jinja2)，維護困難且頁面刷新體驗不佳。
- **行動**: 主導前端架構重整，導入 **Vue 3 Setup Script** 與 **Vite** 建置工具。
- **成果**: 實現前後端分離開發，頁面切換無刷新 (SPA)，將專案建置速度提升 **10倍** 以上，大幅降低後續維護成本。

### 2. 極致響應式的工業圖控系統 (Advanced Data Visualization)
- **挑戰**: 系統核心的「管路架構圖」包含大量感測器數值與狀態圖示，需在不同尺寸的工業螢幕上保持絕對精確的相對位置，傳統 `rem/px` 單位在縮放時常導致圖示錯位或重疊。
- **行動**: 創新採用 CSS 新特性 **容器查詢 (Container Queries)** 與 **`cqw` 單位**，而非依賴 JS 計算或 Canvas 重繪。
- **成果**: 實現了 **Pixel-Perfect** 的響應式佈局。無論視窗如何縮放，底圖與上百個感測器圖示、數值框皆能維持 **100% 完美的相對比例**，徹底解決了圖控介面的跑版問題。

### 3. 工業級複雜表單交互 (Complex Interaction Design)
- **挑戰**: 「工程模式 (Engineer Mode)」需提供數十項硬體參數 (PID, Threshold, Offset) 的讀寫，邏輯複雜且需具備高強度的防呆機制。
- **行動**: 設計模組化的參數設定組件，並實作即時數值驗證與批量寫入功能。
- **成果**: 將原本繁瑣的紙本對照操作，轉化為直覺的 Web UI 介面，大幅降低現場工程師的操作錯誤率。

### 4. 高效能即時數據串流
- **行動**: 優化前端 Polling 機制與狀態管理，針對不同頁面 (Status/Control) 實作差異化的更新頻率。
- **成果**: 在保持低瀏覽器負載的前提下，達成 <1秒 的數據即時更新率，確保監控畫面的即時性與準確性。

## 💡 面試亮點話術 (Interview Talking Points)
> *"在這個專案中，我最自豪的是解決了工業圖控介面在 RWD 上的技術瓶頸。一般網頁通常只針對區塊做 RWD，但我透過運用最新的 Container Queries 技術，讓複雜的管路圖與數值標籤能像『向量圖』一樣無損縮放，這在傳統工業控制 UI 中是非常少見且精緻的實作。"*

---
**適用職缺**: 前端工程師、Full Stack 工程師、Vue.js 開發者、工業物聯網 (IIoT) 系統開發

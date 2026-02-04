# VUE 專案架構及程式碼分析 v2

**版本**: v2.0
**日期**: 2026-02-03
**作者**: Antigravity (Assistant)

---

## 1. 專案概述 (Project Overview)

本專案是一個基於 **Vue 3 (Composition API)** 的現代化單頁應用程式 (SPA)，旨在提供 CDU (Coolant Distribution Unit) 的即時監控、參數控制與系統管理功能。
相較於舊版 (Jinja2/jQuery)，本版本採用了更模組化、響應式且易於維護的前端架構。

### 技術棧 (Tech Stack)
- **核心框架**: Vue.js 3 (Script Setup 語法糖)
- **建置工具**: Vite (快速熱重載與構建)
- **UI 樣式**: TailwindCSS (Utility-first CSS)
- **路由管理**: Vue Router 4
- **HTTP 請求**: Axios
- **圖標庫**: Heroicons Vue
- **響應式技術**: Container Queries (`cqw` 單位)

---

## 2. 目錄結構 (Directory Structure)

```
webUI/frontend/
├── index.html              # 應用程式入口 HTML
├── vite.config.js          # Vite 設定 (包含 API Proxy 轉發至 Flask 後端)
├── tailwind.config.js      # TailwindCSS 設定
├── package.json            # 專案依賴管理
├── public/                 # 靜態資源 (favicon, images)
│   └── img/diagram/        # 系統架構圖相關圖片資源 (Icons, Backgrounds)
└── src/
    ├── main.js             # Vue 實例掛載點 (Mount Application)
    ├── App.vue             # 根組件 (定義全域 Layout 與 Navbar)
    ├── style.css           # 全域樣式 (Tailwind directive)
    ├── router/
    │   └── index.js        # 路由定義 (Routes Configuration)
    └── components/
        ├── Control.vue     # [控制] 參數設定與運轉模式切換
        ├── Network.vue     # [網路] Modbus TCP IP 設定
        ├── Logs.vue        # [日誌] 系統錯誤與停機紀錄查詢 (分頁/搜尋/刪除)
        ├── EngineerMode.vue# [工程] 進階參數調校 (PID, Threshold, Offset)
        ├── Settings.vue    # [設定] 系統單位、密碼、SNMP 設定
        ├── StatusEngineer.vue # [狀態] 首頁儀表板 (整合 SystemDiagram)
        └── SystemDiagram.vue  # [核心] 可視化系統架構圖 (SVG/Image Overlay)
```

---

## 3. 核心組件分析 (Core Module Analysis)

### 3.1 SystemDiagram.vue (系統架構圖)
這是本專案最核心且視覺化程度最高的組件，負責即時顯示 CDU 內各感測器的數值與狀態。

- **技術特點**:
  - **靜態底圖 + 動態疊加**: 使用一張精確繪製的 `CDU底圖.png` 作為背景，透過絕對定位 (`absolute`) 將 Vue 渲染的數據層 (`props.data`) 疊加在特定座標上。
  - **容器查詢 (Container Queries)**: 使用 CSS `container-type: inline-size`，並配合 `cqw` (Container Query Width) 單位設定字體與圖示大小。這確保了圖表無論在寬螢幕或小視窗中，都能保持完美的相對比例，不會跑版。
  - **圖示映射 (Sensor Mapping)**: 透過 `sensors` 陣列定義所有感測器的屬性：
    - `key`: 對應 API 回傳資料的欄位名稱 (e.g., `temp_waterIn`).
    - `x/y`: 在底圖上的百分比座標。
    - `icon`: 顯示的圖示檔案名稱。
    - `layout`: 支援多種排版模式 (`row-val-icon`, `row-icon-val`, `row-label-icon-val`) 以適應底圖管路走向。
    - `sizeClass/labelSizeClass`: 支援個別圖示或標籤的大小微調 (如 T1~T5 縮小至 60%)。

- **排版模式說明**:
  - `vertical` (預設): 標籤 -> 圖示 -> 數值 (垂直堆疊)。
  - `row-val-icon`: [數值] [圖示] (水平排列，適用左側管路)。
  - `row-icon-val`: [圖示] [數值] (水平排列，適用右側管路)。
  - `row-label-icon-val`: [標籤] [圖示] [數值] (水平排列，適用環境感測器)。

### 3.2 Logs.vue (日誌系統)
提供完整的系統日誌查詢與管理功能。

- **功能亮點**:
  - **雙分頁設計**: 區分 "All Error Logs" (所有錯誤) 與 "Shutdown Errors" (停機錯誤)。
  - **表格功能**: 實作了 **伺服器端分頁 (Server-side Pagination)**、關鍵字搜尋、全選/單選功能。
  - **視覺化標示**: 根據錯誤代碼 (`M2` vs `M3`) 自動標註 Severity (ALERT 紅色 / ERROR 灰色)。
  - **API 整合**:
    - `GET /get_signal_records`: 獲取日誌清單。
    - `POST /delete_signal_records`: 批次刪除日誌 (包含防呆確認機製)。

### 3.3 EngineerMode.vue (工程模式)
將原本繁雜的表單參數進行分區管理，提供研發人員調校設備的能力。

- **子功能區塊**:
  1.  **Sensor Adjustment**: 調整 Offset 與 Gain。
  2.  **Threshold Setting**: 設定各感測器的警告閥值。
  3.  **PID Setting**: 調整溫度/壓力控制的 PID 參數。
  4.  **Valve Setting**: 閥件作動邏輯設定。
  5.  **FW/Version**: 韌體版本資訊與功能開關。

### 3.4 App.vue & Layout
- **RWD 導航列**: 使用 TailwindCSS 實作響應式 Navbar，在桌面版顯示完整選單。
- **路由過渡**: 使用 Vue `<transition>` 實作頁面切換時的淡入淡出 (`fade`) 效果，提升使用者體驗。

---

## 4. 前後端整合 (Frontend-Backend Integration)

前端透過 Axios 與 Flask 後端 API 進行通訊。

- **開發模式 (Dev)**:
  - `vite.config.js` 設定 Proxy，將 `/api` 請求轉發至 `http://localhost:5000`，解決 CORS 跨域問題。
- **生產模式 (Prod)**:
  - 運行 `npm run build` 打包。
  - 後端 Flask 需設定 Static Folder 指向 `dist` 目錄，並在根路由 `/` 回傳 `index.html`。

### 關鍵 API 列表
| 功能 | Method | Endpoint | 說明 |
|---|---|---|---|
| 即時數據 | GET | `/get_data_status` | 狀態頁面 1秒/次 輪詢 |
| 控制數據 | GET | `/get_data_control` | 控制頁面 1秒/次 輪詢 |
| 模式切換 | POST | `/set_operation_mode` | 切換 Auto/Manual/Stop |
| 日誌查詢 | GET | `/get_signal_records` | 分頁查詢錯誤日誌 |
| 參數寫入 | POST | `/writeSensorAdjust` | 寫入感測器校正值 |

---

## 5. 未來優化建議 (Future Improvements)

1.  **狀態管理 (State Management)**:
    - 目前 API 資料多在各組件內獨立請求 (e.g., Status 與 Control 頁面分別請求)。若多個組件需共享同一份即時數據 (如全域警報狀態)，建議引入 **Pinia** 進行集中狀態管理，減少重複 API 請求。
2.  **型別檢查 (TypeScript)**:
    - 隨著專案規模擴大，建議逐步遷移至 TypeScript，對 API 回傳的資料結構定義 Interface，減少 `props.data?.value?.key` 這類 Optional Chaining 的不確定性。
3.  **網路設定頁面**:
    - 目前 `Network.vue` 僅支援 Modbus 設定。待後端補齊 "取得本機網卡資訊" (IP/Mask/Gateway) 的 API 後，應盡快補上乙太網路設定功能。

---
**End of Document**

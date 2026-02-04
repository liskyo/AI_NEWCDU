# VUE 專案架構及程式碼分析

## 1. 專案概述
本專案已將原有的 Jinja2/jQuery 前端架構遷移至現代化的 **Vue 3 (Composition API)** 單頁應用程式 (SPA)。
技術棧包含：
- **核心框架**: Vue.js 3
- **建置工具**: Vite
- **UI 樣式**: TailwindCSS
- **路由管理**: Vue Router 4
- **HTTP 請求**: Axios

## 2. 目錄結構
```
webUI/frontend/
├── index.html              # 入口 HTML
├── vite.config.js          # Vite 設定檔 (設定 Proxy 轉發 API)
├── package.json            # 專案依賴
├── src/
│   ├── main.js             # Vue 應用程式入口
│   ├── App.vue             # 根組件 (包含全域 Layout/Navigation)
│   ├── router/
│   │   └── index.js        # 路由定義
│   └── components/
│       ├── Control.vue     # 控制頁面
│       ├── Network.vue     # 網路設定頁面
│       ├── Logs.vue        # 錯誤日誌頁面
│       ├── EngineerMode.vue# 工程模式頁面
│       ├── Settings.vue    # 系統設定頁面
│       └── StatusEngineer.vue # 狀態監控首頁
```

## 3. 組件功能分析

### 3.1 App.vue (全域佈局)
- **職責**: 定義應用程式的主要佈局，包含頂部導航列 (Navbar) 和路由渲染區 (`<router-view>`)。
- **導航**: 提供至 Status, Control, Network, Logs, Engineer Mode, Settings 的連結。

### 3.2 Control.vue (控制頁面)
- **功能**:
  - **模式切換**: 支援 Auto, Manual, Stop, Engineer 模式。
  - **參數設定**:
    - Auto 模式: 設定目標溫度與壓力。
    - Manual 模式: 設定 Pump轉速 (1 & 2) 與 PV 開度。
  - **即時數據**: 每秒呼叫 `/get_data_control` 更新感測器數值。
- **API 整合**:
  - `POST /control/auto_mode_set_aply`: 套用自動模式參數。
  - `POST /set_operation_mode`: 切換運轉模式。
  - `POST /pump_speed_setting`: 設定手動泵浦轉速。

### 3.3 Network.vue (網路設定)
- **功能**:
  - **Modbus TCP 設定**: 顯示並修改 Modbus Slave IP。
  - **介面資訊 (限制)**: 由於後端缺少 `/get_network_info` API，目前乙太網路介面設定 (IP/Mask/Gateway) 暫時以靜態訊息呈現，待後端補上 API 後即可串接。
- **API 整合**:
  - `GET /get_modbus_ip`: 取得目前 Modbus IP。
  - `POST /update_modbus_ip`: 更新 Modbus IP。

### 3.4 Logs.vue (日誌頁面)
- **功能**:
  - **分頁瀏覽**: 支援 "All Error Logs" 與 "Shutdown Errors" 兩個分頁。
  - **表格管理**: 實作分頁 (Pagination)、搜尋、全選/單選功能。
  - **刪除功能**: 支援批次刪除選取的日誌，並具備防呆機制 (未復歸的錯誤需二次確認)。
- **API 整合**:
  - `GET /get_signal_records`: 取得所有錯誤紀錄。
  - `GET /get_downtime_signal_records`: 取得停機錯誤紀錄。
  - `POST /delete_signal_records` / `/delete_downtime_signal_records`: 刪除紀錄。

### 3.5 EngineerMode.vue (工程模式)
- **功能**: 完整移植原有的複雜表單，包含多個子區塊。
  1. **Sensor Adjustment**: 所有感測器的 Factor 與 Offset 調整。
  2. **Threshold Setting**: 感測器的 Warning 與 Alert 上下限設定。
  3. **PID Setting**: 溫度與壓力的 PID 參數 (KP, KI, KD) 設定。
  4. **FW Setting**: 序號、型號、版本資訊讀寫。
  5. **Version Switch**: 切換舊版/新版功能邏輯 (Flow, Function, Median Filter 等)。
  6. **Auto Mode Redundancy**: 設定自動模式下的備援參數。
  7. **Valve Setting**: 設定閥件關閉條件。
- **API 整合**:
  - `POST /writeSensorAdjust`
  - `POST /thrshd_set`
  - `POST /store_pid`
  - `POST /write_version`
  - `POST /version_switch`

### 3.6 Settings.vue (系統設定)
- **功能**:
  - **單位設定**: 切換公制/英制。
  - **密碼管理**: 修改一般使用者密碼。
  - **時間設定**: 手動設定系統時間。
  - **參數設定**: 設定 Log 取樣頻率 與 SNMP Trap IP/Community。
- **API 整合**:
  - `POST /systemSetting/unit_set`
  - `POST /update_password`
  - `POST /set_time`
  - `POST /store_sampling_rate`
  - `POST /store_snmp_setting`

## 4. 前後端整合說明
- **開發環境 (Development)**: 使用 Vite 的 `server.proxy` 功能，將 `/api` 請求代理至 Flask 後端 (預設 Port 5000)，解決 CORS 問題。
- **生產環境 (Production)**: 執行 `npm run build` 產出靜態檔案至 `dist/`，Flask 後端需設定路由指向 `index.html` 與靜態資源。

## 5. 待辦事項與限制
1. **Network Info API**: 目前後端程式碼 (`app.py`) 中未發現 `/get_network_info` 路由，導致前端無法動態顯示網路介面卡資訊。需在後端實作該 API (使用 Python `subprocess` 呼叫 `ipconfig` 或 `nmcli`)。
2. **Rack Setting**: Engineer Mode 中的 Rack Enable Setting 雖已實作，但需確認後端 `/set_rack_engineer` 是否如預期運作 (目前依據 HTML 邏輯推斷)。

---
本文件旨在記錄當前 Vue.js 重構版本的架構與功能實現狀況，供後續開發與維護參考。

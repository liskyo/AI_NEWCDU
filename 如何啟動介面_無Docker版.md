# 無 Docker 環境專案啟動指南 (Deployment Guide)

由於本專案主要運行於 Windows 環境且未使用 Docker 容器化技術，請依照以下步驟確保在客戶端 (Client Side) 能正確啟動系統。

## 1. 環境需求 (Prerequisites)

在執行啟動腳本前，請確保目標電腦已安裝以下基礎軟體：

### 必須安裝
1.  **Python 3.10+**
    *   請至 [Python 官網](https://www.python.org/downloads/) 下載並安裝。
    *   **重要**: 安裝時請務必勾選 **"Add Python to PATH"**。
2.  **Node.js (LTS 版本)**
    *   請至 [Node.js 官網](https://nodejs.org/) 下載 "LTS (Long Term Support)" 版本 (建議 v18 或 v20)。
    *   這是為了運行 Vue 3 前端介面所必需。

---

## 2. 快速啟動 (One-Click Start)

我們已準備好自動化批次檔，可一鍵完成環境建置與啟動。

### 步驟
1.  進入專案根目錄。
2.  雙擊執行 **`windows_run_v2.bat`** (請使用新版腳本)。

### 腳本執行內容
該腳本會自動依序執行以下動作：
1.  **檢查 Python 環境**: 建立並啟動虛擬環境 (`windows_venv`)。
2.  **安裝後端依賴**: 自動讀取 `RestAPI/requirements.txt` 並安裝 Python 套件。
3.  **檢查 Node.js 環境**: 確認 `npm` 指令是否存在。
4.  **安裝前端依賴**: 自動進入 `webUI/frontend` 並執行 `npm install` (僅首次需較長時間)。
5.  **啟動服務**:
    *   啟動 Python Backend (API Server) 於背景 (Port 5001)。
    *   啟動 Vue Frontend (Web Server) 並自動開啟瀏覽器 (Port 5173)。

---

## 3. 手動啟動 (Manual Start) - 除錯用

若批次檔執行失敗，您可以嘗試手動分開啟動前後端：

### 終端機 A - 啟動後端 (RestAPI)
```cmd
cd 專案路徑
python -m venv windows_venv
call windows_venv\Scripts\activate
pip install -r RestAPI\requirements.txt
cd RestAPI
python app.py
```
*成功時會看到: `Running on http://0.0.0.0:5001`*

### 終端機 B - 啟動前端 (Vue Frontend)
```cmd
cd 專案路徑\webUI\frontend
npm install
npm run dev
```
*成功時會看到: `Local: http://localhost:5173`*

---

## 4. 常見問題排除 (Troubleshooting)

*   **Q: 看到 "`'python' 不是內部或外部命令`" 錯誤?**
    *   A: 請重新安裝 Python 並確保勾選 "Add to PATH"。
*   **Q: 看到 "`'npm' 不是內部或外部命令`" 錯誤?**
    *   A: 請安裝 Node.js。
*   **Q: 前端畫面顯示 "`Network Error`" 或數據未更新?**
    *   A: 後端 API Server 可能未成功啟動。請檢查終端機視窗是否有 Python 錯誤訊息 (如 Modbus 連線失敗)。

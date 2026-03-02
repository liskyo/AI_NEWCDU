## 💼 CDU 開發專案 104 履歷表亮點撰寫建議 (V3)

若想在 104 或是其他求職平台上，針對「Guchii CDU (冷卻分配單元) 控制系統」這個專案來行銷自己，建議**不要只是條列技術名稱**，而是要強調您**「解決了什麼工業痛點」**以及**「架構設計能力」**。

你可以把這個專案拆分成以下幾個區塊放在履歷的「專案經驗」或「專業技能」中：

---

### 🌟 專案名稱：企業級 CDU (冷卻分配單元) 智慧監控與遠端控制系統
**擔任角色**：全端工程師 (Full-Stack Developer) / 系統架構師

#### 🔹 專案概述 (Project Abstract)
主導開發半導體/工業級冷卻分配單元 (CDU, Cooling Distribution Unit) 之 Web 儀表板與後端控制服務。系統整合硬體 PLC 設備，提供即時毫秒級的感測器數據監控、遠端設備調度 (幫浦與閥門控制)、完整的歷史響應式趨勢分析圖表，以及自動化異常警報機制。

#### 🔹 核心亮點與成就 (Key Achievements) - 面試官必看的亮點！
* **🚀 現代化微服務架構轉型**：
  * 將傳統且笨重的工控介面，翻新為現代化 Vue 3 SPA (Single Page Application) 架構。利用 TailwindCSS 提供符合人因工程的深色系戰情室 (War Room) UI/UX 體驗。
* **🔌 硬體跨域通訊與即時輪詢機制**：
  * 使用 Python Flask 建構 RESTful API，並利用 **PyModbus** (TCP) 設計高容錯的背景執行緒 (Background Thread)，達到每 1 秒更新全域數十項感測器變數 (溫度、壓力、流量)，並精準捕捉底層變更狀態，達成 100% 同步的即時數據流。
* **🛠️ 智慧型展演引擎 (Smart Mock Engine) 架構設計**：
  * 獨立設計 `DEMO_MODE` 全域展示引擎。**此為最大亮點。** 
  * 針對「無硬體環境展示」及「前端開發無痛接軌」的需求，在後端實作數學模擬演算法 (Sine Waves) 乘載時間序列，不僅能完美模擬平滑的感測曲線，更實作了 **「動態異常注入 (Dynamic Event Injection)」** 機制，全自動週期性向日誌推播警告與解除訊號。此舉**大幅縮短了行銷展示與無硬體環境下的開發與除錯時間**。
* **🌐 高效能輕量化多語系架構 (Lightweight i18n)**：
  * 在不依賴龐大第三方套件 (如 `vue-i18n`) 的前提下，採用 Vue `ref` 與 `localStorage` 機制，為系統量身打造零延遲、無閃爍的前端導航列中英雙語切換功能。
* **📊 戰情室無人自動巡檢模式 (Kiosk Mode)**：
  * 開發能與瀏覽器原生 Full-Screen API 結合的戰情室輪播模式。結合 Vue Router，實現無人看守時系統自動在「狀態儀表板」與「數據趨勢分析」間定期智能切換輪播。

#### 🔹 專業技術堆疊 (Tech Stack) 列表寫法
可以這樣分類寫在履歷的技能欄位中：
* **前端框架 (Frontend Component)**: Vue 3 (Composition API), Vite, TailwindCSS v4, Vue-Router, Axios
* **後端架構 (Backend Services)**: Python, Flask (RESTful API Design), Gunicorn
* **工控通訊協定 (Industrial Protocol)**: Modbus TCP, SNMP (簡易網路管理協定整合)
* **資料處理與架構 (Data Architecture)**: Multi-threading State Management (背景執行緒全域記憶體), Disk JSON Persistence (輕量化日誌持久儲存)

---

### 面試進攻策略 (如果面試官問到...)
💡 如果面試官問：**「這個系統跟一般的 CRUD 網站有什麼不一樣？」**
👉 **你的回答**：
「最大的差異在於**實時性 (Real-time)** 與 **硬體耦合的穩定度**。一般網站可能等用戶點擊才會更新資料，但我設計的系統必須 24 小時不間斷地背景連線 PLC。遇到硬體斷線 (如 504 Timeout 或 M351 錯誤) 時，系統不能掛掉或卡死前端畫面；我加入了自動化 Bypass 與 Timeout 攔截機制，甚至在沒有硬體時可以一鍵啟動我寫的『實況展演引擎 (Demo Engine)』，這是純軟體界較少處理到的『軟硬通訊容錯架構』。」

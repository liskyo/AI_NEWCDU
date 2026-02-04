# CDU (Coolant Distribution Unit) 冷卻液分配單元控制系統 - 開發技術履歷撰寫指南

此文件旨在協助將 CDU 專案經驗轉化為 104 履歷表上的亮點。重點在於將「功能實作」轉化為「解決方案」與「技術價值」，展現出**全端開發 (Full Stack)** 與 **IT/OT 整合 (IIoT)** 的能力。

---

## 📌 專案名稱 (Project Name)
**CDU (Coolant Distribution Unit) 智慧型冷卻監控系統開發**

## 🔧 核心技術關鍵字 (Core Tech Stack)
*(建議填寫於「擅長工具」或專案描述的開頭)*
- **程式語言**: Python 3, Shell Scripting
- **後端框架**: Flask, Flask-RESTX, Gunicorn, RESTful API
- **工業通訊**: Modbus TCP/RTU, PyModbus, Serial Communication
- **系統架構**: Linux (Systemd Services), Nginx, Multi-threading (Concurrency), Queue Management
- **其他技能**: Logging System Design, Error Handling, IIoT, Edge Computing

---

## 📝 專案描述 (Project Description)
*(適用於專案內容欄位，建議 150-200 字)*

主導開發高可靠度的工業級冷卻液分配單元 (CDU) 控制軟體，負責 **AI 伺服器散熱系統** 的核心控制邏輯。系統採分層微服務架構，成功整合底層硬體控制 (PLC/Modbus) 與上層管理介面 (WebUI)。實現了對溫度、壓力、流量等 50+ 個關鍵感測器的**毫秒級即時監控**，並具備泵浦自動輪替 (Redundancy) 與多重過濾器管理功能，確保冷卻系統達到 **99.9% 高可用性 (High Availability)**。

---

## 🏆 重點成就與技術亮點 (Key Achievements)
*(這是最能吸引面試官的部分，請根據實際情況微調)*

### 1. 系統架構設計 (System Architecture)
*   **亮點**: 解決了即時控制與外部請求的衝突，確保系統穩定。
*   **履歷寫法**:
    *   設計 **Driver-Logic-API 分層架構**，將即時硬體輪詢 (Polling Loop) 與 API 服務解耦，確保 Modbus 通訊在重負載下仍保持低延遲與高穩定性。
    *   利用 **Python Multi-threading** 技術並發處理多個 Modbus Slave 設備，大幅提升資料採集頻率。

### 2. 高可靠度與容錯機制 (Reliability & Fault Tolerance)
*   **亮點**: 展現對工業級軟體「穩定性」的重視。
*   **履歷寫法**:
    *   實作 **雙泵浦自動輪替與備援機制 (Pump Redundancy Logic)**，當主泵發生異常時能於秒級內自動切換至備援泵，防止伺服器過熱停機。
    *   建立標準化的 **故障代碼系統 (Error Code System M1xx-M3xx)**，涵蓋 Warning、Alert、Error 三級警報，提升現場除錯效率 50%。
    *   導入 **Concurrent Logging (並發日誌系統)**，完整記錄長時間運行的感測數據與操作歷程，並實作自動輪替 (Log Rotation) 以優化磁碟空間管理。

### 3. API 設計與前後端整合 (API Development)
*   **亮點**: 展現符合現代標準的開發規範。
*   **履歷寫法**:
    *   使用 **Flask-RESTX** 建置標準化 RESTful API，提供清晰的 Swagger/OpenAPI 文件，大幅降低前後端對接成本。
    *   設計結構化的 **JSON Data Schema** 來標準化數十種感測器數據 (Sensor Data Normalization)，使前端能動態渲染不同型號的設備數據。

### 4. 軟硬體整合與部署 (Integration & Deployment)
*   **亮點**: 展現具備 Linux 系統運維與自動化能力。
*   **履歷寫法**:
    *   編寫 **Shell Scripts** 實現一鍵部署與環境建置，整合 Nginx 反向代理與 Gunicorn 應用伺服器，優化生產環境的效能與安全性。
    *   開發硬體模擬層 (Mock Hardware Layer)，在無實體 PLC 的環境下也能進行單元測試與 API 驗證，加速開發迭代週期。

---

## 💡 面試問答準備 (Interview QA Prep)

**Q: 這個專案最困難的點是什麼？**
> **建議回答**: 是在處理 Modbus 串列通訊的「阻塞 (Blocking)」特性與 Web API 需「即時回應」之間的矛盾。我透過獨立的 Thread 負責硬體通訊，並利用記憶體變數 (Shared Memory) 或 Queue 來做資料交換，確保 API 永遠能快速回傳最新的快取數據，而不會卡住等待硬體回應。

**Q: 你如何確保泵浦切換時系統不會崩潰？**
> **建議回答**: 我在邏輯層實作了嚴格的狀態機 (State Machine)，在切換前會先檢查備援泵的健康狀態 (Health Check)，並設有平滑啟動時間 (Ramp-up time) 與壓力穩定延遲 (Stabilization Delay)，避免水錘效應 (Water Hammer) 損壞管路。

---

## 📋 104 職務內容範例 (可以直接複製貼上)

**職務名稱**: 軟體工程師 / 系統整合工程師
**專案: CDU 冷卻液監控系統**
*   **架構設計**: 使用 Python Flask 開發後端控制核心，透過 Modbus TCP/RTU整合 PLC 與感測器網絡。
*   **API開發**: 設計 RESTful API 供 Web 前端與環控系統介接，定義標準化 JSON 資料結構。
*   **演算法實作**: 撰寫 PID 控制邏輯調整泵浦轉速，並實作泵浦健康度監測與自動備援切換策略。
*   **系統優化**: 優化 Modbus 通訊時序，解決多設備輪詢的延遲問題；導入日誌輪替機制確保長期運行穩定。
*   **環境部署**: 使用 Linux Shell Script 與 Systemd 建立自動化部署流程，管理 Nginx/Gunicorn 服務。

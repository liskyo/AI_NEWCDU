# 如何判斷本專案的 Modbus 點位類型 (Data Type)

這份文件說明如何從專案程式碼 (`PLC/plc.py` 與 `RestAPI/app.py`) 中的蛛絲馬跡，判斷出各個 Modbus 點位應該使用哪種資料型態。

## 1. Bit (位元 / 線圈)
**判斷依據**：程式碼中使用 `write_coils` 或 `read_coils`。

*   **程式碼特徵**：
    *   在 `PLC/plc.py` 中，`bit_output_regs` 字典儲存的是 `True` / `False`。
    *   使用 `client.write_coils(0, value)` 寫入。
*   **本專案案例**：
    *   **Address 0-9**: 因為 `write_coils` 操作位址從 0 開始，且寫入的是布林值列表。
    *   `inv1_en` (啟動變頻器), `EV1` (開閥門) 都是這種型態。

## 2. Float32 (32位元浮點數)
**判斷依據**：位址每隔 2 跳號，且有使用 `struct.pack` 或浮點數轉換函數。

*   **程式碼特徵**：
    *   **位址間隔**：在 `measured_data_mapping` 中，位址是 `11`, `13`, `15`... 每次 +2。代表一個數值佔用了 2 個 Register (16bit x 2 = 32bit)。
    *   **轉換函數**：程式碼中呼叫了 `cvt_float_byte(value)` (寫入時) 或 `cvt_registers_to_float(...)` (讀取時)。
    *   **資料內容**：溫度 (`Temp`), 壓力 (`Prsr`), 流量 (`Flow`) 等帶有小數點的物理量。
*   **本專案案例**：
    *   **Address 11-47**: 所有感測器讀值。
    *   **Address 1000+**: 所有閾值設定 (Thresholds)，例如 `1000` (警告高限)。

## 3. UInt16 / Int16 (16位元整數)
**判斷依據**：位址連續 (或只佔 1 個 Register)，且直接寫入整數值。

*   **程式碼特徵**：
    *   **直接讀寫**：使用 `client.read_holding_registers(count=1)` 或 `write_registers` 寫入整數 (Integer)。
    *   **無浮點轉換**：沒有經過 `float` 轉換，直接存取 `registers[0]`。
*   **本專案案例**：
    *   **Address 200, 202**: `pump1_run_time_hr`。運轉時數通常只會增加，不會是負的，且時數通常是整數，故為 **UInt16** (Unsigned Integer)。
    *   **Address 50**: `pid_pump_out`。PID 輸出通常是 `0-100%` 或 `0-4096` 的整數值。若可能有負輸出則為 **Int16**，若僅為正則為 **UInt16** (本專案假設為 UInt16 即可涵蓋)。

## 4. BitMask (位元遮罩)
**判斷依據**：一個 Register 代表多個狀態。

*   **程式碼特徵**：
    *   程式邏輯將多個 `True/False` (例如 Error Flags) 轉換成一個二進位數值寫入。
    *   例如：`value = (Err1 << 0) + (Err2 << 1) + ...`
    *   寫入時使用 `write_registers` (視為整數)，但解讀時需要拆成 Bit 看。
*   **本專案案例**：
    *   **Address 750 (推測)**: `Inspection Result`。通常自動巡檢會把多個步驟的 Pass/Fail 壓縮在一個數值回傳。
    *   **Address 1700+**: 程式中的 `set_warning_registers` 就是典型的 BitMask 操作。

---

## 快速對照表

| 型態 | 佔用長度 | 判斷關鍵字 (Python) | 代表意義 |
| :--- | :--- | :--- | :--- |
| **Bit (Coil)** | 1 Bit | `write_coils`, `True/False` | 開關、燈號 |
| **Float32** | 2 Regs | `cvt_registers_to_float`, 位址+2 | 溫度、壓力、流量 |
| **UInt16** | 1 Reg | `write_registers`, 整數值 | 時間、計數、狀態碼 |
| **BitMask** | 1 Reg | 把多個 Bool 塞進一個 Int | 綜合警報、錯誤碼 |

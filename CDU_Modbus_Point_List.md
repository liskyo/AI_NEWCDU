# CDU Modbus 點位表 (Modbus Address Map)

本文件列出 CDU 控制系統的 Modbus TCP 通訊點位。
**更新日期**: 2026-02-04
**格式說明**:
*   **Protocol Address**: 程式開發用 (Base 0)。
*   **PLC Address**: 人機介面用 (Base 1, 4xxxx/0xxxx)。
*   **R/W**: R=Read Only (唯讀), RW=Read/Write (讀寫)。

---

## 1. Boolean (Coils) - 0xxxx
**功能**: 控制開關與狀態指示。
**Base 1 Address**: `00001` + Protocol Address

| Protocol Addr (Dec) | PLC Addr (0x) | 名稱 (Name) | 描述 (Description) | R/W |
| :--- | :--- | :--- | :--- | :--- |
| 0 | 00001 | `inv1_en` | 變頻器 1 啟動 | RW |
| 1 | 00002 | `inv2_en` | 變頻器 2 啟動 | RW |
| 2 | 00003 | `mc1` | MC1 接觸器 (泵浦電源) | RW |
| 3 | 00004 | `mc2` | MC2 接觸器 (泵浦電源) | RW |
| 4 | 00005 | `led_err` | 異常燈號 | RW |
| 5 | 00006 | `led_pw` | 電源燈號 | RW |
| 6 | 00007 | `EV1` | 電動閥 1 開關 | RW |
| 7 | 00008 | `EV2` | 電動閥 2 開關 | RW |
| 8 | 00009 | `EV3` | 電動閥 3 開關 | RW |
| 9 | 00010 | `EV4` | 電動閥 4 開關 | RW |

---

## 2. Sensor Readings (Float32) - 4xxxx
**功能**: 讀取感測器數值。
**特性**: 每個數值佔用 **2** 個 Register (32-bit Float)。
**PLC Address**: `40001` + Protocol Address

| Protocol Addr (Dec) | PLC Addr (4x) | 名稱 (Name) | 描述 (Description) | 單位 |
| :--- | :--- | :--- | :--- | :--- |
| 11 | 40012-40013 | `TempClntSply` | 冷卻液供應溫度 | °C |
| 13 | 40014-40015 | `TempClntSplySpr` | 冷卻液供應備用溫度 | °C |
| 15 | 40016-40017 | `TempClntRtn` | 冷卻液回水溫度 | °C |
| 17 | 40018-40019 | `TempWaterIn` | 一次側進水溫度 | °C |
| 19 | 40020-40021 | `TempWaterOut` | 一次側出水溫度 | °C |
| 21 | 40022-40023 | `PrsrClntSply` | 冷卻液供應壓力 | bar |
| 23 | 40024-40025 | `PrsrClntSplySpr` | 冷卻液供應備用壓力 | bar |
| 25 | 40026-40027 | `PrsrClntRtn` | 冷卻液回水壓力 | bar |
| 27 | 40028-40029 | `PrsrClntRtnSpr` | 冷卻液回水備用壓力 | bar |
| 29 | 40030-40031 | `PrsrFltIn` | 過濾器進口壓力 | bar |
| 31 | 40032-40033 | `PrsrFlt1Out` | 過濾器 1 出口壓力 | bar |
| 33 | 40034-40035 | `PrsrFlt2Out` | 過濾器 2 出口壓力 | bar |
| 35 | 40036-40037 | `PrsrFlt3Out` | 過濾器 3 出口壓力 | bar |
| 37 | 40038-40039 | `PrsrFlt4Out` | 過濾器 4 出口壓力 | bar |
| 39 | 40040-40041 | `PrsrFlt5Out` | 過濾器 5 出口壓力 | bar |
| 41 | 40042-40043 | `PrsrWaterIn` | 一次側進水壓力 | bar |
| 43 | 40044-40045 | `PrsrWaterOut` | 一次側出水壓力 | bar |
| 45 | 40046-40047 | `ClntFlow` | 二次側流量 | LPM |
| 47 | 40048-40049 | `WaterFlow` | 一次側流量 | LPM |

---

## 3. Control Parameters & Status (Mixed) - 4xxxx
**功能**: 系統設定與狀態回傳。

| Protocol Addr | PLC Addr | 名稱 | 描述 | 型態 |
| :--- | :--- | :--- | :--- | :--- |
| 50 | 40051 | `pid_pump_out` | PID 控制輸出值 | Int16 |
| 200 | 40201 | `pump1_run_time_hr` | 泵浦 1 總運轉時數 (小時) | UInt16 |
| 202 | 40203 | `pump2_run_time_hr` | 泵浦 2 總運轉時數 (小時) | UInt16 |
| 222 | 40223-40224 | `inv2_speed_set` | 變頻器 2 頻率設定 | Float32 |
| 246 | 40247-40248 | `inv1_speed_set` | 變頻器 1 頻率設定 | Float32 |
| 352 | 40353-40354 | `Water_PV_Set` | 水閥開度設定 | Float32 |
| 750 | 40751 | `Inspection Result` | 巡檢結果 (BitMask) | Word |
| 800 | 40801 | `Inspection Progress` | 巡檢進度步驟 | UInt16 |

---

## 4. Threshold Settings (Float32) - 4xxxx
**功能**: 設定警告與危險閾值。
**佔用**: 2 Registers (雖然位址跳號間隔為 4，但有效資料為 2 Regs)。

| Protocol Addr | PLC Addr | 名稱 | 描述 |
| :--- | :--- | :--- | :--- |
| 1000 | 41001-41002 | `Thr_W_TempClntSply_H` | 冷卻液供應溫度 (警告高限) |
| 1004 | 41005-41006 | `Thr_A_TempClntSply_H` | 冷卻液供應溫度 (危險高限) |
| 1008 | 41009-41010 | `Thr_W_TempClntSplySpr_H` | 備用溫度 (警告高限) |
| 1056 | 41057-41058 | `Thr_W_PrsrClntSply_H` | 供應壓力 (警告高限) |
| 1200 | 41201-41202 | `Thr_W_CoolantFlowRate_L` | 二次側流量 (警告低限) |

*(其餘閾值請參考 Excel 完整列表)*

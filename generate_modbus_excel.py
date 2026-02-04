import pandas as pd
import os

# Define the data
data = []

# Helper to add rows
def add_row(category, address_dec, name, desc, rw_type, data_type):
    # Determine PLC Address (Standard Modbus Notation)
    # Coils (0xxxx), Discrete Inputs (1xxxx), Input Registers (3xxxx), Holding Registers (4xxxx)
    
    plc_addr = ""
    hex_addr = f"0x{address_dec:04X}"
    
    if "Coil" in category or "Coil" in rw_type:
        # Coils are 0xxxx. Base 1.
        plc_addr = f"{address_dec + 1:05d}" 
    else:
        # All others are Holding Registers (4xxxx). Base 1.
        start_addr = address_dec + 1
        if "Float32" in data_type:
             # Float32 uses 2 registers
             end_addr = start_addr + 1
             plc_addr = f"4{start_addr:04d}-4{end_addr:04d}"
        else:
             # 1 Register
             plc_addr = f"4{start_addr:04d}"

    data.append({
        "Category": category,
        "Protocol Address (Dec)": address_dec,
        "PLC Address (4x/0x)": plc_addr,
        "Address (Hex)": hex_addr,
        "Name": name,
        "Description": desc,
        "R/W": rw_type,
        "Data Type": data_type
    })

# --- POPULATE DATA ---

# 1. Coils
coils = [
    (0, "inv1_en", "變頻器 1 啟動"),
    (1, "inv2_en", "變頻器 2 啟動"),
    (2, "mc1", "MC1 接觸器 (泵浦電源)"),
    (3, "mc2", "MC2 接觸器 (泵浦電源)"),
    (4, "led_err", "異常燈號"),
    (5, "led_pw", "電源燈號"),
    (6, "EV1", "電動閥 1 開關"),
    (7, "EV2", "電動閥 2 開關"),
    (8, "EV3", "電動閥 3 開關"),
    (9, "EV4", "電動閥 4 開關"),
]
for addr, name, desc in coils:
    add_row("Control (Coils)", addr, name, desc, "RW", "Bit")

# 2. Sensors (Holding Registers)
sensors = [
    (11, "TempClntSply", "冷卻液供應溫度"),
    (13, "TempClntSplySpr", "冷卻液供應備用溫度"),
    (15, "TempClntRtn", "冷卻液回水溫度"),
    (17, "TempWaterIn", "一次側進水溫度"),
    (19, "TempWaterOut", "一次側出水溫度"),
    (21, "PrsrClntSply", "冷卻液供應壓力"),
    (23, "PrsrClntSplySpr", "冷卻液供應備用壓力"),
    (25, "PrsrClntRtn", "冷卻液回水壓力"),
    (27, "PrsrClntRtnSpr", "冷卻液回水備用壓力"),
    (29, "PrsrFltIn", "過濾器進口壓力"),
    (31, "PrsrFlt1Out", "過濾器 1 出口壓力"),
    (33, "PrsrFlt2Out", "過濾器 2 出口壓力"),
    (35, "PrsrFlt3Out", "過濾器 3 出口壓力"),
    (37, "PrsrFlt4Out", "過濾器 4 出口壓力"),
    (39, "PrsrFlt5Out", "過濾器 5 出口壓力"),
    (41, "PrsrWaterIn", "一次側進水壓力"),
    (43, "PrsrWaterOut", "一次側出水壓力"),
    (45, "ClntFlow", "二次側流量"),
    (47, "WaterFlow", "一次側流量"),
]
for addr, name, desc in sensors:
    add_row("Sensor Readings", addr, name, desc, "RO", "Float32")

# 3. Control Registers
controls = [
    (50, "pid_pump_out", "PID 控制輸出值", "Register", "Int16"),
    (200, "pump1_run_time_hr", "泵浦 1 總運轉時數 (小時)", "Register", "UInt16"),
    (202, "pump2_run_time_hr", "泵浦 2 總運轉時數 (小時)", "Register", "UInt16"),
    (222, "inv2_speed_set", "變頻器 2 頻率設定", "Float32", "Float32"),
    (246, "inv1_speed_set", "變頻器 1 頻率設定", "Float32", "Float32"),
    (352, "Water_PV_Set", "水閥開度設定", "Float32", "Float32"),
    (750, "Inspection Result", "巡檢結果", "Register", "BitMask"),
    (800, "Inspection Progress", "巡檢進度步驟", "Register", "UInt16"),
]
for addr, name, desc, r_type, d_type in controls:
    add_row("Control Parameters", addr, name, desc, "RW", d_type)

# 4. Thresholds (Sample)
thresholds = [
    (1000, "Thr_W_TempClntSply_H", "冷卻液供應溫度 (警告高限)"),
    (1004, "Thr_A_TempClntSply_H", "冷卻液供應溫度 (危險高限)"),
    (1056, "Thr_W_PrsrClntSply_H", "供應壓力 (警告高限)"),
    (1200, "Thr_W_CoolantFlowRate_L", "二次側流量 (警告低限)"),
]
for addr, name, desc in thresholds:
    add_row("Threshold Settings", addr, name, desc, "RW", "Float32")


# Create DataFrame
df = pd.DataFrame(data)

# Reorder columns
cols = ["Category", "Protocol Address (Dec)", "PLC Address (4x/0x)", "Address (Hex)", "Name", "Description", "R/W", "Data Type"]
df = df[cols]

# Export to Excel with formatting
output_file = "c:/Users/sky.lo/Desktop/CDU程式碼/CDU/250303/CDU_Modbus_Point_List.xlsx"

try:
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Modbus Point List")
        
        # Access the workbook and sheet for formatting
        workbook = writer.book
        worksheet = writer.sheets["Modbus Point List"]
        
        # Adjust column widths
        for i, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            worksheet.column_dimensions[chr(65 + i)].width = max_len

    print(f"Excel file generated successfully: {output_file}")

except Exception as e:
    print(f"Error generating Excel: {e}")

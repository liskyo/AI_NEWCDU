import csv

# Modbus Point List Data

# 1. Coils
coils = [
    {"Address": 0, "Name": "inv1_en", "Description": "變頻器 1 啟動", "Type": "Coil (RW)"},
    {"Address": 1, "Name": "inv2_en", "Description": "變頻器 2 啟動", "Type": "Coil (RW)"},
    {"Address": 2, "Name": "mc1", "Description": "MC1 接觸器", "Type": "Coil (RW)"},
    {"Address": 3, "Name": "mc2", "Description": "MC2 接觸器", "Type": "Coil (RW)"},
    {"Address": 4, "Name": "led_err", "Description": "異常燈", "Type": "Coil (RW)"},
    {"Address": 5, "Name": "led_pw", "Description": "電源燈", "Type": "Coil (RW)"},
    {"Address": 6, "Name": "EV1", "Description": "電動閥 1", "Type": "Coil (RW)"},
    {"Address": 7, "Name": "EV2", "Description": "電動閥 2", "Type": "Coil (RW)"},
    {"Address": 8, "Name": "EV3", "Description": "電動閥 3", "Type": "Coil (RW)"},
    {"Address": 9, "Name": "EV4", "Description": "電動閥 4", "Type": "Coil (RW)"},
]

# 2. Sensors (Holding Registers 11-47)
sensors = [
    {"Address": 11, "Name": "TempClntSply", "Description": "冷卻液供應溫度", "Type": "Float32 (RO)"},
    {"Address": 13, "Name": "TempClntSplySpr", "Description": "冷卻液供應備用溫度", "Type": "Float32 (RO)"},
    {"Address": 15, "Name": "TempClntRtn", "Description": "冷卻液回水溫度", "Type": "Float32 (RO)"},
    {"Address": 17, "Name": "TempWaterIn", "Description": "一次側進水溫度", "Type": "Float32 (RO)"},
    {"Address": 19, "Name": "TempWaterOut", "Description": "一次側出水溫度", "Type": "Float32 (RO)"},
    {"Address": 21, "Name": "PrsrClntSply", "Description": "冷卻液供應壓力", "Type": "Float32 (RO)"},
    {"Address": 23, "Name": "PrsrClntSplySpr", "Description": "冷卻液供應備用壓力", "Type": "Float32 (RO)"},
    {"Address": 25, "Name": "PrsrClntRtn", "Description": "冷卻液回水壓力", "Type": "Float32 (RO)"},
    {"Address": 27, "Name": "PrsrClntRtnSpr", "Description": "冷卻液回水備用壓力", "Type": "Float32 (RO)"},
    {"Address": 29, "Name": "PrsrFltIn", "Description": "過濾器進口壓力", "Type": "Float32 (RO)"},
    {"Address": 31, "Name": "PrsrFlt1Out", "Description": "過濾器 1 出口壓力", "Type": "Float32 (RO)"},
    {"Address": 33, "Name": "PrsrFlt2Out", "Description": "過濾器 2 出口壓力", "Type": "Float32 (RO)"},
    {"Address": 35, "Name": "PrsrFlt3Out", "Description": "過濾器 3 出口壓力", "Type": "Float32 (RO)"},
    {"Address": 37, "Name": "PrsrFlt4Out", "Description": "過濾器 4 出口壓力", "Type": "Float32 (RO)"},
    {"Address": 39, "Name": "PrsrFlt5Out", "Description": "過濾器 5 出口壓力", "Type": "Float32 (RO)"},
    {"Address": 41, "Name": "PrsrWaterIn", "Description": "一次側進水壓力", "Type": "Float32 (RO)"},
    {"Address": 43, "Name": "PrsrWaterOut", "Description": "一次側出水壓力", "Type": "Float32 (RO)"},
    {"Address": 45, "Name": "ClntFlow", "Description": "二次側流量", "Type": "Float32 (RO)"},
    {"Address": 47, "Name": "WaterFlow", "Description": "一次側流量", "Type": "Float32 (RO)"},
]

# 3. Control & Settings
controls = [
    {"Address": 50, "Name": "pid_pump_out", "Description": "PID控制輸出值", "Type": "Register (RW)"},
    {"Address": 200, "Name": "pump1_run_time_hr", "Description": "泵浦 1 總運轉時數 (小時)", "Type": "Register (RW)"},
    {"Address": 202, "Name": "pump2_run_time_hr", "Description": "泵浦 2 總運轉時數 (小時)", "Type": "Register (RW)"},
    {"Address": 222, "Name": "inv2_speed_set", "Description": "變頻器 2 頻率設定", "Type": "Float32 (RW)"},
    {"Address": 246, "Name": "inv1_speed_set", "Description": "變頻器 1 頻率設定", "Type": "Float32 (RW)"},
    {"Address": 352, "Name": "Water_PV_Set", "Description": "水閥開度設定", "Type": "Float32 (RW)"},
    {"Address": 750, "Name": "Inspection Result", "Description": "自動巡檢結果", "Type": "Register (RW)"},
    {"Address": 800, "Name": "Inspection Progress", "Description": "自動巡檢進度", "Type": "Register (RW)"},
]

# 4. Thresholds (Sample)
thresholds = [
    {"Address": 1000, "Name": "Thr_W_TempClntSply_H", "Description": "冷卻液供應溫度 (警告高限)", "Type": "Float32 (RW)"},
    {"Address": 1004, "Name": "Thr_A_TempClntSply_H", "Description": "冷卻液供應溫度 (危險高限)", "Type": "Float32 (RW)"},
    {"Address": 1008, "Name": "Thr_W_TempClntSplySpr_H", "Description": "備用溫度 (警告高限)", "Type": "Float32 (RW)"},
    {"Address": 1012, "Name": "Thr_A_TempClntSplySpr_H", "Description": "備用溫度 (危險高限)", "Type": "Float32 (RW)"},
    {"Address": 1016, "Name": "Thr_W_TempClntRtn_H", "Description": "回水溫度 (警告高限)", "Type": "Float32 (RW)"},
    {"Address": 1020, "Name": "Thr_A_TempClntRtn_H", "Description": "回水溫度 (危險高限)", "Type": "Float32 (RW)"},
    {"Address": 1024, "Name": "Thr_W_WaterSupplyTemperature_L", "Description": "供水溫度 (警告低限)", "Type": "Float32 (RW)"},
    {"Address": 1028, "Name": "Thr_W_WaterSupplyTemperature_H", "Description": "供水溫度 (警告高限)", "Type": "Float32 (RW)"},
    {"Address": 1056, "Name": "Thr_W_PrsrClntSply_H", "Description": "供應壓力 (警告高限)", "Type": "Float32 (RW)"},
    {"Address": 1060, "Name": "Thr_A_PrsrClntSply_H", "Description": "供應壓力 (危險高限)", "Type": "Float32 (RW)"},
    {"Address": 1200, "Name": "Thr_W_CoolantFlowRate_L", "Description": "二次側流量 (警告低限)", "Type": "Float32 (RW)"},
    {"Address": 1204, "Name": "Thr_A_CoolantFlowRate_L", "Description": "二次側流量 (危險低限)", "Type": "Float32 (RW)"},
]

# Combine all
all_points = coils + sensors + controls + thresholds
all_points.sort(key=lambda x: x["Address"])

# Write to CSV
# Using 'utf-8-sig' for Excel compatibility with Chinese characters
filename = "c:/Users/sky.lo/Desktop/CDU程式碼/CDU/250303/CDU_Modbus_Point_List.csv"
with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
    fieldnames = ['Address', 'Name', 'Description', 'Type']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for row in all_points:
        writer.writerow(row)

print(f"CSV file generated at: {filename}")

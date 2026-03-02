import json
import os
from datetime import datetime, timedelta

log_path = r"c:\Users\sky.lo\Desktop\NEW CDU程式碼\CDU\250303\webUI\web\json"
os.makedirs(log_path, exist_ok=True)

now = datetime.now()

# 1. Fake ALL LOGS
all_logs = [
    {
        "signal_name": "M3_CoolantTemp_High",
        "on_time": (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
        "off_time": (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "severity": "Warning",
        "signal_value": "Coolant Temperature above 50°C"
    },
    {
        "signal_name": "M2_Pump_Fail",
        "on_time": (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "off_time": "",
        "severity": "Alert",
        "signal_value": "Pump 1 failed to start"
    },
    {
        "signal_name": "Sys_Info",
        "on_time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "off_time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "severity": "Info",
        "signal_value": "System User Login: admin"
    }
]

# 2. Fake SHUTDOWN LOGS
shutdown_logs = [
    {
        "signal_name": "M2_Emergency_Stop",
        "on_time": (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "off_time": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "severity": "Alert",
        "signal_value": "Emergency Stop Button Triggered"
    }
]

with open(f"{log_path}/signal_records.json", "w", encoding="utf-8") as f:
    json.dump(all_logs, f, indent=4)

with open(f"{log_path}/downtime_signal_records.json", "w", encoding="utf-8") as f:
    json.dump(shutdown_logs, f, indent=4)

print("Test logs successfully created!")

import threading
import time
import os
import logging
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.sync import ModbusSerialClient
import struct
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
import statistics
from collections import deque
from dotenv import load_dotenv
import platform
import json


if platform.system() == "Linux":
    project_root = os.path.dirname(os.getcwd())
    env_path = os.path.join(project_root, "webUI/web/.env")
    onLinux = True

else:
    env_path = "webUI/web/.env"
    onLinux = False


load_dotenv(env_path)

modbus_ip = os.getenv("MODBUS_IP")


if onLinux:
    modbus_host = modbus_ip
else:
    modbus_host = "192.168.3.250"
# modbus_host = "127.0.0.1"

modbus_port = 502
modbus_slave_id = 1
modbus_address = 0

port = "/dev/ttyS1"

switch_address = 0x0000

log_path = os.getcwd()


if onLinux:
    journal_dir = f"{log_path}/logs/journal"
else:
    journal_dir = f"{log_path}/PLC/logs/journal"

if not os.path.exists(journal_dir):
    os.makedirs(journal_dir)

max_bytes = 4 * 1024 * 1024 * 1024
backup_count = 1

file_name = "journal.log"
log_file = os.path.join(journal_dir, file_name)
journal_handler = ConcurrentTimedRotatingFileHandler(
    log_file,
    maxBytes=max_bytes,
    backupCount=backup_count,
    encoding="UTF-8",
    delay=False,
)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
journal_handler.setFormatter(formatter)

journal_logger = logging.getLogger("journal_logger")
journal_logger.setLevel(logging.INFO)
journal_logger.addHandler(journal_handler)

server1_count = 0
check_server2 = 0
pre_check_server2 = 0
server2_occur_stop = False


f1_data = []
p1_data = []
p2_data = []
p1_error_box = []
p2_error_box = []
pump_signial = ""
change_back_mode = ""
count_f1 = 0
previous_inv = 4
x = 0
water_pv_set = 0
count = 0
diff = 0
previous_inv1 = False
previous_inv2 = False
oc_issue = False
warning_light = False
f1_issue = False
one_time_stop = True
zero_flag = False
auto_flag = False
rtu_flag = False
previous_ver = None
oc_trigger = False

bit_output_regs = {
    "inv1_en": False,
    "inv2_en": False,
    "mc1": False,
    "mc2": False,
    "led_err": False,
    "led_pw": False,
    "EV1": False,
    "EV2": False,
    "EV3": False,
    "EV4": False,
}

word_regs = {
    "inv1_speed_set": 1,
    "inv2_speed_set": 0,
    "pid_pump_out": 0,
}

bit_input_regs = {
    "Inv1_Error": None,
    "Inv2_Error": None,
    "Water_Leak": False,
    "Water_Leak_Broken": False,
    "EV1_Open": False,
    "EV1_Close": False,
    "EV2_Open": False,
    "EV2_Close": False,
    "EV3_Open": False,
    "EV3_Close": False,
    "EV4_Open": False,
    "EV4_Close": False,
}

raw_485_data = {
    "relative_humidity": 0,
    "ambient_temperature": 0,
    "dew_point_temperature": 0,
    "coolant_flow_rate": 0,
    "facility_water_flow_rate": 0,
    "ph": 0,
    "conductivity": 0,
    "turbidity": 0,
    "instant_power_consumption": 0,
    "inv1_speed": 0,
    "inv2_speed": 0,
    "average_current": 0,
    "ATS1": False,
    "ATS2": False,
}

raw_485_communication = {
    "inv1_speed": False,
    "inv2_speed": False,
    "ambient_temperature": False,
    "coolant_flow_rate": False,
    "facility_water_flow_rate": False,
    "conductivity": False,
    "ph": False,
    "turbidity": False,
    "ATS1": False,
    "instant_power_consumption": False,
}


sensor_raw = {
    "Temp_ClntSply": 0,
    "Temp_ClntSplySpr": 0,
    "Temp_ClntRtn": 0,
    "Temp_WaterIn": 0,
    "Temp_WaterOut": 0,
    "Prsr_ClntSply": 0,
    "Prsr_ClntSplySpr": 0,
    "Prsr_ClntRtn": 0,
    "Prsr_FltIn": 0,
    "Prsr_Flt1Out": 0,
    "Prsr_Flt2Out": 0,
    "Prsr_Flt3Out": 0,
    "Prsr_Flt4Out": 0,
    "Prsr_Flt5Out": 0,
    "Prsr_ClntRtnSpr": 0,
    "Prsr_WtrIn": 0,
    "Prsr_WtrOut": 0,
    "PV_Wtr": 0,
    "Relative_Humid": 0,
    "Temp_Ambient": 0,
    "Dew_Point_Temp": 0,
    "Clnt_Flow": 0,
    "Wtr_Flow": 0,
    "ph": 0,
    "Cndct": 0,
    "Tbd": 0,
    "Power": 0,
    "Inv1_Sp": 0,
    "Inv2_Sp": 0,
    "AC": 0,
    "Heat_Capacity": 0,
}

ad_sensor_value = {
    "Temp_ClntSply": 0,
    "Temp_ClntSplySpr": 0,
    "Temp_ClntRtn": 0,
    "Temp_WaterIn": 0,
    "Temp_WaterOut": 0,
    "Prsr_ClntSply": 0,
    "Prsr_ClntSplySpr": 0,
    "Prsr_ClntRtn": 0,
    "Prsr_FltIn": 0,
    "Prsr_Flt1Out": 0,
    "Prsr_Flt2Out": 0,
    "Prsr_Flt3Out": 0,
    "Prsr_Flt4Out": 0,
    "Prsr_Flt5Out": 0,
    "Prsr_ClntRtnSpr": 0,
    "Prsr_WtrIn": 0,
    "Prsr_WtrOut": 0,
    "PV_Wtr": 0,
}

serial_sensor_value = {
    "Relative_Humid": 0,
    "Temp_Ambient": 0,
    "Dew_Point_Temp": 0,
    "Clnt_Flow": 0,
    "Wtr_Flow": 0,
    "ph": 0,
    "Cndct": 0,
    "Tbd": 0,
    "Power": 0,
    "Inv1_Sp": 0,
    "Inv2_Sp": 0,
    "AC": 0,
    "Heat_Capacity": 0,
}


oc_detection = {
    "M20": False,
    "M21": False,
}

inspection_data = {
    "prev": {
        "inv1": False,
        "inv2": False,
    },
    "result": {
        "ev1_open": False,
        "ev2_open": False,
        "ev3_open": False,
        "ev4_open": False,
        "ev1_close": False,
        "ev2_close": False,
        "ev3_close": False,
        "ev4_close": False,
        "p1_speed": False,
        "p2_speed": False,
        "water_pv": False,
        "f1": [],
        "f2": False,
        "Temp_ClntSply_broken": False,
        "Temp_ClntSplySpr_broken": False,
        "Temp_ClntRtn_broken": False,
        "Temp_WaterIn_broken": False,
        "Temp_WaterOut_broken": False,
        "Prsr_ClntSply_broken": False,
        "Prsr_ClntSplySpr_broken": False,
        "Prsr_ClntRtn_broken": False,
        "Prsr_ClntRtnSpr_broken": False,
        "Prsr_FltIn_broken": False,
        "Prsr_Flt1Out_broken": False,
        "Prsr_Flt2Out_broken": False,
        "Prsr_Flt3Out_broken": False,
        "Prsr_Flt4Out_broken": False,
        "Prsr_Flt5Out_broken": False,
        "Prsr_WtrIn_broken": False,
        "Prsr_WtrOut_broken": False,
        "Clnt_Flow_broken": False,
        "Wtr_Flow_broken": False,
        "inv1_speed_com": [],
        "inv2_speed_com": [],
        "ambient_temperature_com": [],
        "coolant_flow_rate_com": [],
        "facility_water_flow_rate_com": [],
        "conductivity_com": [],
        "ph_com": [],
        "turbidity_com": [],
        "ATS1_com": [],
        "instant_power_consumption_com": [],
        "level1": False,
        "level2": False,
        "level3": False,
        "power1": False,
        "power2": False,
    },
    "progress": {
        "ev1_open": 1,
        "ev2_open": 1,
        "ev3_open": 1,
        "ev4_open": 1,
        "ev1_close": 1,
        "ev2_close": 1,
        "ev3_close": 1,
        "ev4_close": 1,
        "p1_speed": 1,
        "p2_speed": 1,
        "water_pv": 1,
        "f1": 1,
        "f2": 1,
        "Temp_ClntSply_broken": 1,
        "Temp_ClntSplySpr_broken": 1,
        "Temp_ClntRtn_broken": 1,
        "Temp_WaterIn_broken": 1,
        "Temp_WaterOut_broken": 1,
        "Prsr_ClntSply_broken": 1,
        "Prsr_ClntSplySpr_broken": 1,
        "Prsr_ClntRtn_broken": 1,
        "Prsr_ClntRtnSpr_broken": 1,
        "Prsr_FltIn_broken": 1,
        "Prsr_Flt1Out_broken": 1,
        "Prsr_Flt2Out_broken": 1,
        "Prsr_Flt3Out_broken": 1,
        "Prsr_Flt4Out_broken": 1,
        "Prsr_Flt5Out_broken": 1,
        "Prsr_WtrIn_broken": 1,
        "Prsr_WtrOut_broken": 1,
        "Clnt_Flow_broken": 1,
        "Wtr_Flow_broken": 1,
        "inv1_speed_com": 1,
        "inv2_speed_com": 1,
        "ambient_temperature_com": 1,
        "coolant_flow_rate_com": 1,
        "facility_water_flow_rate_com": 1,
        "conductivity_com": 1,
        "ph_com": 1,
        "turbidity_com": 1,
        "ATS1_com": 1,
        "instant_power_consumption_com": 1,
        "level1": 1,
        "level2": 1,
        "level3": 1,
        "power1": 1,
        "power2": 1,
    },
    "set": {"total_inspect_time": 95},
    "step": 1,
    "start_time": 0,
    "mid_time": 0,
    "end_time": 0,
    "final_end_time": 0,
    "force_change_mode": 0,
    "start_btn": False,
    "cancel_btn": False,
    "skip": False,
}

ver_switch = {
    "function_switch": False,
    "flow_switch": False,
    "flow2_switch": False,
    "median_switch": False,
}

valve_setting = {"t1": 0, "ta": 0}

measured_data_mapping = {
    11: "TempClntSply",
    13: "TempClntSplySpr",
    15: "TempClntRtn",
    17: "TempWaterIn",
    19: "TempWaterOut",
    21: "PrsrClntSply",
    23: "PrsrClntSplySpr",
    25: "PrsrClntRtn",
    27: "PrsrClntRtnSpr",
    29: "PrsrFltIn",
    31: "PrsrFlt1Out",
    33: "PrsrFlt2Out",
    35: "PrsrFlt3Out",
    37: "PrsrFlt4Out",
    39: "PrsrFlt5Out",
    41: "PrsrWaterIn",
    43: "PrsrWaterOut",
    45: "ClntFlow",
    47: "WaterFlow",
}

counter = {
    "start": 0,
    "end": 0,
    "pass": 0,
}


dword_regs = {
    "pump_swap_total_min": 0,
    "pump_swap_min": 0,
    "pump_swap_hr": 0,
    "pump_swap_hr_set": 0,
    "pump1_run_time_min": 0,
    "pump1_run_time_hr": 0,
    "pump2_run_time_min": 0,
    "pump2_run_time_hr": 0,
}


filter_runtime = {
    "runtime": {
        "filter1": {"min": 0, "hr": 0},
        "filter2": {"min": 0, "hr": 0},
        "filter3": {"min": 0, "hr": 0},
        "filter4": {"min": 0, "hr": 0},
        "filter5": {"min": 0, "hr": 0},
    },
    "filter_run_last_min": {
        "filter1": time.time(),
        "filter2": time.time(),
        "filter3": time.time(),
        "filter4": time.time(),
        "filter5": time.time(),
    },
    "address": {
        "filter1": (700, 702),
        "filter2": (704, 706),
        "filter3": (708, 710),
        "filter4": (712, 714),
        "filter5": (716, 718),
    },
}


reset_current_btn = {"status": False, "press_reset": False}


sensor_factor = {
    "Temp_ClntSply": 1,
    "Temp_ClntSplySpr": 0,
    "Temp_ClntRtn": 0,
    "Temp_WaterIn": 0,
    "Temp_WaterOut": 0,
    "Prsr_ClntSply": 0,
    "Prsr_ClntSplySpr": 0,
    "Prsr_ClntRtn": 0,
    "Prsr_ClntRtnSpr": 0,
    "Prsr_FltIn": 0,
    "Prsr_Flt1Out": 0,
    "Prsr_Flt2Out": 0,
    "Prsr_Flt3Out": 0,
    "Prsr_Flt4Out": 0,
    "Prsr_Flt5Out": 0,
    "Prsr_WtrIn": 0,
    "Prsr_WtrOut": 0,
    "PV_Wtr": 0,
    "Relative_Humid": 0,
    "Temp_Ambient": 0,
    "Dew_Point_Temp": 0,
    "Clnt_Flow": 0,
    "Wtr_Flow": 0,
    "ph": 0,
    "Cndct": 0,
    "Tbd": 0,
    "Power": 1,
    "Heat_Capacity": 1,
    "AC": 1,
}

sensor_offset = {
    "Temp_ClntSply": 1,
    "Temp_ClntSplySpr": 0,
    "Temp_ClntRtn": 0,
    "Temp_WaterIn": 0,
    "Temp_WaterOut": 0,
    "Prsr_ClntSply": 0,
    "Prsr_ClntSplySpr": 0,
    "Prsr_ClntRtn": 0,
    "Prsr_ClntRtnSpr": 0,
    "Prsr_FltIn": 0,
    "Prsr_Flt1Out": 0,
    "Prsr_Flt2Out": 0,
    "Prsr_Flt3Out": 0,
    "Prsr_Flt4Out": 0,
    "Prsr_Flt5Out": 0,
    "Prsr_WtrIn": 0,
    "Prsr_WtrOut": 0,
    "PV_Wtr": 0,
    "Relative_Humid": 0,
    "Temp_Ambient": 0,
    "Dew_Point_Temp": 0,
    "Clnt_Flow": 0,
    "Wtr_Flow": 0,
    "ph": 0,
    "Cndct": 0,
    "Tbd": 0,
    "Power": 1,
    "Heat_Capacity": 1,
    "AC": 1,
}

all_sensors_dict = {
    "Temp_ClntSply": 0,
    "Temp_ClntSplySpr": 0,
    "Temp_ClntRtn": 0,
    "Temp_WaterIn": 0,
    "Temp_WaterOut": 0,
    "Prsr_ClntSply": 0,
    "Prsr_ClntSplySpr": 0,
    "Prsr_ClntRtn": 0,
    "Prsr_FltIn": 0,
    "Prsr_Flt1Out": 0,
    "Prsr_Flt2Out": 0,
    "Prsr_Flt3Out": 0,
    "Prsr_Flt4Out": 0,
    "Prsr_Flt5Out": 0,
    "Prsr_ClntRtnSpr": 0,
    "Prsr_WtrIn": 0,
    "Prsr_WtrOut": 0,
    "PV_Wtr": 0,
    "Relative_Humid": 0,
    "Temp_Ambient": 0,
    "Dew_Point_Temp": 0,
    "Clnt_Flow": 0,
    "Wtr_Flow": 0,
    "ph": 0,
    "Cndct": 0,
    "Tbd": 0,
    "Power": 0,
    "Inv1_Sp": 0,
    "Inv2_Sp": 0,
    "AC": 0,
    "Heat_Capacity": 0,
}


thrshd_data = {
    "Thr_W_TempClntSply": 0,
    "Thr_W_Rst_TempClntSply": 0,
    "Thr_A_TempClntSply": 0,
    "Thr_A_Rst_TempClntSply": 0,
    "Thr_W_TempClntSplySpr": 0,
    "Thr_W_Rst_TempClntSplySpr": 0,
    "Thr_A_TempClntSplySpr": 0,
    "Thr_A_Rst_TempClntSplySpr": 0,
    "Thr_W_TempClntRtn": 0,
    "Thr_W_Rst_TempClntRtn": 0,
    "Thr_A_TempClntRtn": 0,
    "Thr_A_Rst_TempClntRtn": 0,
    "Thr_W_TempWaterIn_L": 0,
    "Thr_W_Rst_TempWaterIn_L": 0,
    "Thr_W_TempWaterIn_H": 0,
    "Thr_W_Rst_TempWaterIn_H": 0,
    "Thr_A_TempWaterIn_L": 0,
    "Thr_A_Rst_TempWaterIn_L": 0,
    "Thr_A_TempWaterIn_H": 0,
    "Thr_A_Rst_TempWaterIn_H": 0,
    "Thr_W_TempWaterOut_L": 0,
    "Thr_W_Rst_TempWaterOut_L": 0,
    "Thr_W_TempWaterOut_H": 0,
    "Thr_W_Rst_TempWaterOut_H": 0,
    "Thr_A_TempWaterOut_L": 0,
    "Thr_A_Rst_TempWaterOut_L": 0,
    "Thr_A_TempWaterOut_H": 0,
    "Thr_A_Rst_TempWaterOut_H": 0,
    "Thr_W_PrsrClntSply": 0,
    "Thr_W_Rst_PrsrClntSply": 0,
    "Thr_A_PrsrClntSply": 0,
    "Thr_A_Rst_PrsrClntSply": 0,
    "Thr_W_PrsrClntSplySpr": 0,
    "Thr_W_Rst_PrsrClntSplySpr": 0,
    "Thr_A_PrsrClntSplySpr": 0,
    "Thr_A_Rst_PrsrClntSplySpr": 0,
    "Thr_W_PrsrClntRtn": 0,
    "Thr_W_Rst_PrsrClntRtn": 0,
    "Thr_A_PrsrClntRtn": 0,
    "Thr_A_Rst_PrsrClntRtn": 0,
    "Thr_W_PrsrClntRtnSpr": 0,
    "Thr_W_Rst_PrsrClntRtnSpr": 0,
    "Thr_A_PrsrClntRtnSpr": 0,
    "Thr_A_Rst_PrsrClntRtnSpr": 0,
    "Thr_W_PrsrFltIn_L": 0,
    "Thr_W_Rst_PrsrFltIn_L": 0,
    "Thr_W_PrsrFltIn_H": 0,
    "Thr_W_Rst_PrsrFltIn_H": 0,
    "Thr_A_PrsrFltIn_L": 0,
    "Thr_A_Rst_PrsrFltIn_L": 0,
    "Thr_A_PrsrFltIn_H": 0,
    "Thr_A_Rst_PrsrFltIn_H": 0,
    "Thr_W_PrsrFlt1Out_H": 0,
    "Thr_W_Rst_PrsrFlt1Out_H": 0,
    "Thr_A_PrsrFlt1Out_H": 0,
    "Thr_A_Rst_PrsrFlt1Out_H": 0,
    "Thr_W_PrsrFlt2Out_H": 0,
    "Thr_W_Rst_PrsrFlt2Out_H": 0,
    "Thr_A_PrsrFlt2Out_H": 0,
    "Thr_A_Rst_PrsrFlt2Out_H": 0,
    "Thr_W_PrsrFlt3Out_H": 0,
    "Thr_W_Rst_PrsrFlt3Out_H": 0,
    "Thr_A_PrsrFlt3Out_H": 0,
    "Thr_A_Rst_PrsrFlt3Out_H": 0,
    "Thr_W_PrsrFlt4Out_H": 0,
    "Thr_W_Rst_PrsrFlt4Out_H": 0,
    "Thr_A_PrsrFlt4Out_H": 0,
    "Thr_A_Rst_PrsrFlt4Out_H": 0,
    "Thr_W_PrsrFlt5Out_H": 0,
    "Thr_W_Rst_PrsrFlt5Out_H": 0,
    "Thr_A_PrsrFlt5Out_H": 0,
    "Thr_A_Rst_PrsrFlt5Out_H": 0,
    "Thr_W_PrsrWaterIn": 0,
    "Thr_W_Rst_PrsrWaterIn": 0,
    "Thr_A_PrsrWaterIn": 0,
    "Thr_A_Rst_PrsrWaterIn": 0,
    "Thr_W_PrsrWaterOut": 0,
    "Thr_W_Rst_PrsrWaterOut": 0,
    "Thr_A_PrsrWaterOut": 0,
    "Thr_A_Rst_PrsrWaterOut": 0,
    "Thr_W_RltvHmd_L": 0,
    "Thr_W_Rst_RltvHmd_L": 0,
    "Thr_W_RltvHmd_H": 0,
    "Thr_W_Rst_RltvHmd_H": 0,
    "Thr_A_RltvHmd_L": 0,
    "Thr_A_Rst_RltvHmd_L": 0,
    "Thr_A_RltvHmd_H": 0,
    "Thr_A_Rst_RltvHmd_H": 0,
    "Thr_W_TempAmbient_L": 0,
    "Thr_W_Rst_TempAmbient_L": 0,
    "Thr_W_TempAmbient_H": 0,
    "Thr_W_Rst_TempAmbient_H": 0,
    "Thr_A_TempAmbient_L": 0,
    "Thr_A_Rst_TempAmbient_L": 0,
    "Thr_A_TempAmbient_H": 0,
    "Thr_A_Rst_TempAmbient_H": 0,
    "Thr_W_TempCds": 0,
    "Thr_W_Rst_TempCds": 0,
    "Thr_A_TempCds": 0,
    "Thr_A_Rst_TempCds": 0,
    "Thr_W_ClntFlow": 0,
    "Thr_W_Rst_ClntFlow": 0,
    "Thr_A_ClntFlow": 0,
    "Thr_A_Rst_ClntFlow": 0,
    "Thr_W_WaterFlow": 0,
    "Thr_W_Rst_WaterFlow": 0,
    "Thr_A_WaterFlow": 0,
    "Thr_A_Rst_WaterFlow": 0,
    "Thr_W_pH_L": 0,
    "Thr_W_Rst_pH_L": 0,
    "Thr_A_pH_L": 0,
    "Thr_A_Rst_pH_L": 0,
    "Thr_W_pH_H": 0,
    "Thr_W_Rst_pH_H": 0,
    "Thr_A_pH_H": 0,
    "Thr_A_Rst_pH_H": 0,
    "Thr_W_Cdct_L": 0,
    "Thr_W_Rst_Cdct_L": 0,
    "Thr_A_Cdct_L": 0,
    "Thr_A_Rst_Cdct_L": 0,
    "Thr_W_Cdct_H": 0,
    "Thr_W_Rst_Cdct_H": 0,
    "Thr_A_Cdct_H": 0,
    "Thr_A_Rst_Cdct_H": 0,
    "Thr_W_Tbt_L": 0,
    "Thr_W_Rst_Tbt_L": 0,
    "Thr_A_Tbt_L": 0,
    "Thr_A_Rst_Tbt_L": 0,
    "Thr_W_Tbt_H": 0,
    "Thr_W_Rst_Tbt_H": 0,
    "Thr_A_Tbt_H": 0,
    "Thr_A_Rst_Tbt_H": 0,
    "Thr_W_AC_H": 0,
    "Thr_W_Rst_AC_H": 0,
    "Thr_A_AC_H": 0,
    "Thr_A_Rst_AC_H": 0,
    "Delay_TempClntSply": 0,
    "Delay_TempClntSplySply": 0,
    "Delay_TempClntRtn": 0,
    "Delay_TempWaterIn": 0,
    "Delay_TempWaterOut": 0,
    "Delay_PrsrClntSply": 0,
    "Delay_PrsrClntSplySpr": 0,
    "Delay_PrsrClntRtn": 0,
    "Delay_PrsrClntRtnSpr": 0,
    "Delay_PrsrFltIn": 0,
    "Delay_PrsrFlt1Out": 0,
    "Delay_PrsrFlt2Out": 0,
    "Delay_PrsrFlt3Out": 0,
    "Delay_PrsrFlt4Out": 0,
    "Delay_PrsrFlt5Out": 0,
    "Delay_PrsrWaterIn": 0,
    "Delay_PrsrWaterOut": 0,
    "Delay_RltvHmd": 0,
    "Delay_TempAmbient": 0,
    "Delay_TempCds": 0,
    "Delay_ClntFlow": 0,
    "Delay_WaterFlow": 0,
    "Delay_pH": 0,
    "Delay_Cdct": 0,
    "Delay_Tbt": 0,
    "Delay_AC": 0,
    "Delay_WaterPV": 0,
    "Delay_EV1": 0,
    "Delay_EV2": 0,
    "Delay_EV3": 0,
    "Delay_EV4": 0,
    "Delay_Inv1_OverLoad": 0,
    "Delay_Inv2_OverLoad": 0,
    "Delay_Inv1_Error": 0,
    "Delay_Inv2_Error": 0,
    "Delay_Water_Leak": 0,
    "Delay_Water_Leak_Broken": 0,
    "Delay_ATS": 0,
    "Delay_Inverter1_Communication": 0,
    "Delay_Inverter2_Communication": 0,
    "Delay_Ambient_Sensor_Communication": 0,
    "Delay_Coolant_Flow_Meter_Communication": 0,
    "Delay_Water_Flow_Meter_Communication": 0,
    "Delay_Conductivity_Sensor_Communication": 0,
    "Delay_pH_Sensor_Communication": 0,
    "Delay_Turbidity_Sensor_Communication": 0,
    "Delay_ATS_Communication": 0,
    "Delay_Power_Meter_Communication": 0,
    "Delay_TempClntSply_broken": 0,
    "Delay_TempClntSplySpr_broken": 0,
    "Delay_TempClntRtn_broken": 0,
    "Delay_TempWaterIn_broken": 0,
    "Delay_TempWaterOut_broken": 0,
    "Delay_PrsrClntSply_broken": 0,
    "Delay_PrsrClntSplySpr_broken": 0,
    "Delay_PrsrClntRtn_broken": 0,
    "Delay_PrsrClntRtnSpr_broken": 0,
    "Delay_PrsrFltIn_broken": 0,
    "Delay_PrsrFlt1Out_broken": 0,
    "Delay_PrsrFlt2Out_broken": 0,
    "Delay_PrsrFlt3Out_broken": 0,
    "Delay_PrsrFlt4Out_broken": 0,
    "Delay_PrsrFlt5Out_broken": 0,
    "Delay_PrsrWaterIn_broken": 0,
    "Delay_PrsrWaterOut_broken": 0,
    "Delay_Clnt_Flow_broken": 0,
    "Delay_Wtr_Flow_broken": 0,
    "Delay_level1_error": 0,
    "Delay_level2_error": 0,
    "Delay_level3_error": 0,
    "Delay_power1_error": 0,
    "Delay_power2_error": 0,
}

rack_data = {
    "rack_control": {
        "Rack_1_Enable": False,
        "Rack_2_Enable": False,
        "Rack_3_Enable": False,
        "Rack_4_Enable": False,
        "Rack_5_Enable": False,
        "Rack_6_Enable": False,
        "Rack_7_Enable": False,
        "Rack_8_Enable": False,
        "Rack_9_Enable": False,
        "Rack_10_Enable": False,
        "Rack_1_Control": False,
        "Rack_2_Control": False,
        "Rack_3_Control": False,
        "Rack_4_Control": False,
        "Rack_5_Control": False,
        "Rack_6_Control": False,
        "Rack_7_Control": False,
        "Rack_8_Control": False,
        "Rack_9_Control": False,
        "Rack_10_Control": False,
    },
    "rack_pass": {
        "Rack_1_Pass": False,
        "Rack_2_Pass": False,
        "Rack_3_Pass": False,
        "Rack_4_Pass": False,
        "Rack_5_Pass": False,
        "Rack_6_Pass": False,
        "Rack_7_Pass": False,
        "Rack_8_Pass": False,
        "Rack_9_Pass": False,
        "Rack_10_Pass": False,
    },
}


status_data = {
    "TempClntSply": 0,
    "TempClntSplySpr": 0,
    "TempClntRtn": 0,
    "TempWaterIn": 0,
    "TempWaterOut": 0,
    "PrsrClntSply": 0,
    "PrsrClntSplySpr": 0,
    "PrsrClntRtn": 0,
    "PrsrFltIn": 0,
    "PrsrFlt1Out": 0,
    "PrsrFlt2Out": 0,
    "PrsrFlt3Out": 0,
    "PrsrFlt4Out": 0,
    "PrsrFlt5Out": 0,
    "PrsrClntRtnSpr": 0,
    "PrsrWaterIn": 0,
    "PrsrWaterOut": 0,
    "WaterPV": 0,
    "RltvHmd": 0,
    "TempAmbient": 0,
    "TempCds": 0,
    "ClntFlow": 0,
    "WaterFlow": 0,
    "pH": 0,
    "Cdct": 0,
    "Tbt": 0,
    "Power": 0,
    "Inv1_Freq": 0,
    "Inv2_Freq": 0,
    "AC": 0,
    "HeatCapacity": 0,
}


time_data = {
    "start": {
        "W_TempClntSply": 0,
        "W_TempClntSplySpr": 0,
        "W_TempClntRtn": 0,
        "W_TempWaterIn": 0,
        "W_TempWaterOut": 0,
        "W_PrsrClntSply": 0,
        "W_PrsrClntSplySpr": 0,
        "W_PrsrClntRtn": 0,
        "W_PrsrClntRtnSpr": 0,
        "W_PrsrFltIn": 0,
        "W_PrsrFlt1Out": 0,
        "W_PrsrFlt2Out": 0,
        "W_PrsrFlt3Out": 0,
        "W_PrsrFlt4Out": 0,
        "W_PrsrFlt5Out": 0,
        "W_PrsrWaterIn": 0,
        "W_PrsrWaterOut": 0,
        "W_PVWtr": 0,
        "W_RltvHmd": 0,
        "W_TempAmbient": 0,
        "W_TempCds": 0,
        "W_ClntFlow": 0,
        "W_WaterFlow": 0,
        "W_pH": 0,
        "W_Cdct": 0,
        "W_Tbt": 0,
        "W_AC": 0,
        "W_Power": 0,
        "W_HeatCapacity": 0,
        "A_TempClntSply": 0,
        "A_TempClntSplySpr": 0,
        "A_TempClntRtn": 0,
        "A_TempWaterIn": 0,
        "A_TempWaterOut": 0,
        "A_PrsrClntSply": 0,
        "A_PrsrClntSplySpr": 0,
        "A_PrsrClntRtn": 0,
        "A_PrsrClntRtnSpr": 0,
        "A_PrsrFltIn": 0,
        "A_PrsrFlt1Out": 0,
        "A_PrsrFlt2Out": 0,
        "A_PrsrFlt3Out": 0,
        "A_PrsrFlt4Out": 0,
        "A_PrsrFlt5Out": 0,
        "A_PrsrWaterIn": 0,
        "A_PrsrWaterOut": 0,
        "A_PVWtr": 0,
        "A_RltvHmd": 0,
        "A_TempAmbient": 0,
        "A_TempCds": 0,
        "A_ClntFlow": 0,
        "A_WaterFlow": 0,
        "A_pH": 0,
        "A_Cdct": 0,
        "A_Tbt": 0,
        "A_AC": 0,
        "A_Power": 0,
        "A_HeatCapacity": 0,
        "EV1": 0,
        "EV2": 0,
        "EV3": 0,
        "EV4": 0,
        "Inv1_OverLoad": 0,
        "Inv2_OverLoad": 0,
        "Inv1_Error": 0,
        "Inv2_Error": 0,
        "Water_Leak": 0,
        "Water_Leak_Broken": 0,
        "WaterPV": 0,
        "inv1_speed": 0,
        "inv2_speed": 0,
        "ambient_temperature": 0,
        "coolant_flow_rate": 0,
        "facility_water_flow_rate": 0,
        "conductivity": 0,
        "ph": 0,
        "turbidity": 0,
        "ATS1": 0,
        "instant_power_consumption": 0,
        "ATS": 0,
        "Temp_ClntSply": 0,
        "Temp_ClntSplySpr": 0,
        "Temp_ClntRtn": 0,
        "Temp_WaterIn": 0,
        "Temp_WaterOut": 0,
        "Prsr_ClntSply": 0,
        "Prsr_ClntSplySpr": 0,
        "Prsr_ClntRtn": 0,
        "Prsr_ClntRtnSpr": 0,
        "Prsr_FltIn": 0,
        "Prsr_Flt1Out": 0,
        "Prsr_Flt2Out": 0,
        "Prsr_Flt3Out": 0,
        "Prsr_Flt4Out": 0,
        "Prsr_Flt5Out": 0,
        "Prsr_WtrIn": 0,
        "Prsr_WtrOut": 0,
        "Clnt_Flow": 0,
        "Wtr_Flow": 0,
        "level1_error": 0,
        "level2_error": 0,
        "power1_error": 0,
        "power2_error": 0,
        "level3_error": 0,
    },
    "end": {
        "W_TempClntSply": 0,
        "W_TempClntSplySpr": 0,
        "W_TempClntRtn": 0,
        "W_TempWaterIn": 0,
        "W_TempWaterOut": 0,
        "W_PrsrClntSply": 0,
        "W_PrsrClntSplySpr": 0,
        "W_PrsrClntRtn": 0,
        "W_PrsrClntRtnSpr": 0,
        "W_PrsrFltIn": 0,
        "W_PrsrFlt1Out": 0,
        "W_PrsrFlt2Out": 0,
        "W_PrsrFlt3Out": 0,
        "W_PrsrFlt4Out": 0,
        "W_PrsrFlt5Out": 0,
        "W_PrsrWaterIn": 0,
        "W_PrsrWaterOut": 0,
        "W_PVWtr": 0,
        "W_RltvHmd": 0,
        "W_TempAmbient": 0,
        "W_TempCds": 0,
        "W_ClntFlow": 0,
        "W_WaterFlow": 0,
        "W_pH": 0,
        "W_Cdct": 0,
        "W_Tbt": 0,
        "W_AC": 0,
        "W_Power": 0,
        "W_HeatCapacity": 0,
        "A_TempClntSply": 0,
        "A_TempClntSplySpr": 0,
        "A_TempClntRtn": 0,
        "A_TempWaterIn": 0,
        "A_TempWaterOut": 0,
        "A_PrsrClntSply": 0,
        "A_PrsrClntSplySpr": 0,
        "A_PrsrClntRtn": 0,
        "A_PrsrClntRtnSpr": 0,
        "A_PrsrFltIn": 0,
        "A_PrsrFlt1Out": 0,
        "A_PrsrFlt2Out": 0,
        "A_PrsrFlt3Out": 0,
        "A_PrsrFlt4Out": 0,
        "A_PrsrFlt5Out": 0,
        "A_PrsrWaterIn": 0,
        "A_PrsrWaterOut": 0,
        "A_PVWtr": 0,
        "A_RltvHmd": 0,
        "A_TempAmbient": 0,
        "A_TempCds": 0,
        "A_ClntFlow": 0,
        "A_WaterFlow": 0,
        "A_pH": 0,
        "A_Cdct": 0,
        "A_Tbt": 0,
        "A_AC": 0,
        "A_HeatCapacity": 0,
        "A_Power": 0,
        "EV1": 0,
        "EV2": 0,
        "EV3": 0,
        "EV4": 0,
        "Inv1_OverLoad": 0,
        "Inv2_OverLoad": 0,
        "Inv1_Error": 0,
        "Inv2_Error": 0,
        "Water_Leak": 0,
        "Water_Leak_Broken": 0,
        "WaterPV": 0,
        "inv1_speed": 0,
        "inv2_speed": 0,
        "ambient_temperature": 0,
        "coolant_flow_rate": 0,
        "facility_water_flow_rate": 0,
        "conductivity": 0,
        "ph": 0,
        "turbidity": 0,
        "ATS1": 0,
        "instant_power_consumption": 0,
        "ATS": 0,
        "Temp_ClntSply": 0,
        "Temp_ClntSplySpr": 0,
        "Temp_ClntRtn": 0,
        "Temp_WaterIn": 0,
        "Temp_WaterOut": 0,
        "Prsr_ClntSply": 0,
        "Prsr_ClntSplySpr": 0,
        "Prsr_ClntRtn": 0,
        "Prsr_ClntRtnSpr": 0,
        "Prsr_FltIn": 0,
        "Prsr_Flt1Out": 0,
        "Prsr_Flt2Out": 0,
        "Prsr_Flt3Out": 0,
        "Prsr_Flt4Out": 0,
        "Prsr_Flt5Out": 0,
        "Prsr_WtrIn": 0,
        "Prsr_WtrOut": 0,
        "Clnt_Flow": 0,
        "Wtr_Flow": 0,
        "level1_error": 0,
        "level2_error": 0,
        "power1_error": 0,
        "power2_error": 0,
        "level3_error": 0,
    },
    "check": {
        "W_TempClntSply": False,
        "W_TempClntSplySpr": False,
        "W_TempClntRtn": False,
        "W_TempWaterIn": False,
        "W_TempWaterOut": False,
        "W_PrsrClntSply": False,
        "W_PrsrClntSplySpr": False,
        "W_PrsrClntRtn": False,
        "W_PrsrClntRtnSpr": False,
        "W_PrsrFltIn": False,
        "W_PrsrFlt1Out": False,
        "W_PrsrFlt2Out": False,
        "W_PrsrFlt3Out": False,
        "W_PrsrFlt4Out": False,
        "W_PrsrFlt5Out": False,
        "W_PrsrWaterIn": False,
        "W_PrsrWaterOut": False,
        "W_PVWtr": False,
        "W_RltvHmd": False,
        "W_TempAmbient": False,
        "W_TempCds": False,
        "W_ClntFlow": False,
        "W_WaterFlow": False,
        "W_pH": False,
        "W_Cdct": False,
        "W_Tbt": False,
        "W_AC": 0,
        "W_Power": False,
        "W_HeatCapacity": False,
        "A_TempClntSply": False,
        "A_TempClntSplySpr": False,
        "A_TempClntRtn": False,
        "A_TempWaterIn": False,
        "A_TempWaterOut": False,
        "A_PrsrClntSply": False,
        "A_PrsrClntSplySpr": False,
        "A_PrsrClntRtn": False,
        "A_PrsrClntRtnSpr": False,
        "A_PrsrFltIn": False,
        "A_PrsrFlt1Out": False,
        "A_PrsrFlt2Out": False,
        "A_PrsrFlt3Out": False,
        "A_PrsrFlt4Out": False,
        "A_PrsrFlt5Out": False,
        "A_PrsrWaterIn": False,
        "A_PrsrWaterOut": False,
        "A_PVWtr": False,
        "A_RltvHmd": False,
        "A_TempAmbient": False,
        "A_TempCds": False,
        "A_ClntFlow": False,
        "A_WaterFlow": False,
        "A_pH": False,
        "A_Cdct": False,
        "A_Tbt": False,
        "A_AC": False,
        "A_Power": False,
        "A_HeatCapacity": False,
        "EV1": False,
        "EV2": False,
        "EV3": False,
        "EV4": False,
        "Inv1_OverLoad": False,
        "Inv2_OverLoad": False,
        "Inv1_Error": False,
        "Inv2_Error": False,
        "Water_Leak": False,
        "Water_Leak_Broken": False,
        "WaterPV": False,
        "inv1_speed": False,
        "inv2_speed": False,
        "ambient_temperature": False,
        "coolant_flow_rate": False,
        "facility_water_flow_rate": False,
        "conductivity": False,
        "ph": False,
        "turbidity": False,
        "ATS1": False,
        "instant_power_consumption": False,
        "ATS": False,
        "Temp_ClntSply": False,
        "Temp_ClntSplySpr": False,
        "Temp_ClntRtn": False,
        "Temp_WaterIn": False,
        "Temp_WaterOut": False,
        "Prsr_ClntSply": False,
        "Prsr_ClntSplySpr": False,
        "Prsr_ClntRtn": False,
        "Prsr_ClntRtnSpr": False,
        "Prsr_FltIn": False,
        "Prsr_Flt1Out": False,
        "Prsr_Flt2Out": False,
        "Prsr_Flt3Out": False,
        "Prsr_Flt4Out": False,
        "Prsr_Flt5Out": False,
        "Prsr_WtrIn": False,
        "Prsr_WtrOut": False,
        "Clnt_Flow": False,
        "Wtr_Flow": False,
        "level1_error": 0,
        "level2_error": 0,
        "power1_error": 0,
        "power2_error": 0,
        "level3_error": 0,
    },
    "condition": {
        "low": {
            "W_TempWaterIn": False,
            "W_TempWaterOut": False,
            "W_RltvHmd": False,
            "W_TempAmbient": False,
            "W_pH": False,
            "W_Cdct": False,
            "W_Tbt": False,
            "W_PrsrFltIn": False,
            "A_TempWaterIn": False,
            "A_TempWaterOut": False,
            "A_RltvHmd": False,
            "A_TempAmbient": False,
            "A_pH": False,
            "A_Cdct": False,
            "A_Tbt": False,
            "A_PrsrFltIn": False,
        },
        "high": {
            "W_PrsrFltIn": False,
            "W_TempWaterIn": False,
            "W_TempWaterOut": False,
            "W_RltvHmd": False,
            "W_TempAmbient": False,
            "W_pH": False,
            "W_Cdct": False,
            "W_Tbt": False,
            "A_TempWaterIn": False,
            "A_TempWaterOut": False,
            "A_RltvHmd": False,
            "A_TempAmbient": False,
            "A_pH": False,
            "A_Cdct": False,
            "A_Tbt": False,
            "A_PrsrFltIn": False,
        },
    },
}


inverter_error = {
    "Inv1_OverLoad": False,
    "Inv2_OverLoad": False,
}


restart_server = {"stage": 0, "start": 0, "diff": 0}

server_error = {"start": 0, "diff": 0}


warning_data = {
    "warning": {
        "TempClntSply_High": False,
        "TempClntSplySpr_High": False,
        "TempClntRtn_High": False,
        "TempWaterIn_Low": False,
        "TempWaterIn_High": False,
        "TempWaterOut_Low": False,
        "TempWaterOut_High": False,
        "PrsrClntSply_High": False,
        "PrsrClntSplySpr_High": False,
        "PrsrClntRtn_High": False,
        "PrsrClntRtnSpr_High": False,
        "PrsrFltIn_Low": False,
        "PrsrFltIn_High": False,
        "PrsrFlt1Out_High": False,
        "PrsrFlt2Out_High": False,
        "PrsrFlt3Out_High": False,
        "PrsrFlt4Out_High": False,
        "PrsrFlt5Out_High": False,
        "PrsrWaterIn_High": False,
        "PrsrWaterOut_High": False,
        "RltvHmd_Low": False,
        "RltvHmd_High": False,
        "TempAmbient_Low": False,
        "TempAmbient_High": False,
        "TempCds_Low": False,
        "ClntFlow_Low": False,
        "WaterFlow_Low": False,
        "pH_Low": False,
        "pH_High": False,
        "Cdct_Low": False,
        "Cdct_High": False,
        "Tbt_Low": False,
        "Tbt_High": False,
        "AC_High": False,
    },
    "alert": {
        "TempClntSply_High": False,
        "TempClntSplySpr_High": False,
        "TempClntRtn_High": False,
        "TempWaterIn_Low": False,
        "TempWaterIn_High": False,
        "TempWaterOut_Low": False,
        "TempWaterOut_High": False,
        "PrsrClntSply_High": False,
        "PrsrClntSplySpr_High": False,
        "PrsrClntRtn_High": False,
        "PrsrClntRtnSpr_High": False,
        "PrsrFltIn_Low": False,
        "PrsrFltIn_High": False,
        "PrsrFlt1Out_High": False,
        "PrsrFlt2Out_High": False,
        "PrsrFlt3Out_High": False,
        "PrsrFlt4Out_High": False,
        "PrsrFlt5Out_High": False,
        "PrsrWaterIn_High": False,
        "PrsrWaterOut_High": False,
        "RltvHmd_Low": False,
        "RltvHmd_High": False,
        "TempAmbient_Low": False,
        "TempAmbient_High": False,
        "TempCds_Low": False,
        "ClntFlow_Low": False,
        "WaterFlow_Low": False,
        "pH_Low": False,
        "pH_High": False,
        "Cdct_Low": False,
        "Cdct_High": False,
        "Tbt_Low": False,
        "Tbt_High": False,
        "AC_High": False,
    },
    "error": {
        "WaterPV_Error": False,
        "Inv1_OverLoad": False,
        "Inv2_OverLoad": False,
        "Inv1_Error": False,
        "Inv2_Error": False,
        "Water_Leak": False,
        "Water_Leak_Broken": False,
        "EV1_Error": False,
        "EV2_Error": False,
        "EV3_Error": False,
        "EV4_Error": False,
        "ATS1_Error": False,
        "inv1_speed_communication": 0,
        "inv2_speed_communication": 0,
        "ambient_temperature_communication": 0,
        "coolant_flow_rate_communication": 0,
        "facility_water_flow_rate_communication": 0,
        "conductivity_communication": 0,
        "ph_communication": 0,
        "turbidity_communication": 0,
        "ATS1_communication": 0,
        "instant_power_consumption_communication": 0,
        "Temp_ClntSply_broken": False,
        "Temp_ClntSplySpr_broken": False,
        "Temp_ClntRtn_broken": False,
        "Temp_WaterIn_broken": False,
        "Temp_WaterOut_broken": False,
        "Prsr_ClntSply_broken": False,
        "Prsr_ClntSplySpr_broken": False,
        "Prsr_ClntRtn_broken": False,
        "Prsr_ClntRtnSpr_broken": False,
        "Prsr_FltIn_broken": False,
        "Prsr_Flt1Out_broken": False,
        "Prsr_Flt2Out_broken": False,
        "Prsr_Flt3Out_broken": False,
        "Prsr_Flt4Out_broken": False,
        "Prsr_Flt5Out_broken": False,
        "Prsr_WtrIn_broken": False,
        "Prsr_WtrOut_broken": False,
        "Clnt_Flow_broken": False,
        "Wtr_Flow_broken": False,
        "Low_Coolant_Level_Warning": False,
        "Inv1_error_code": False,
        "Inv2_error_code": False,
        "pc1_error": False,
        "pc2_error": False,
        "level1_error": False,
        "level2_error": False,
        "power1_error": False,
        "power2_error": False,
        "level3_error": False,
    },
}

inv_error_code = {
    "code1": 0,
    "code2": 0,
}

ats_status = {
    "ATS1": False,
    "ATS2": False,
}

level_sw = {
    "level1": None,
    "level2": None,
    "level3": None,
    "power1": None,
    "power2": None,
}


def read_split_register(r, i):
    return (r[i + 1] << 16) | r[i]


def split_double(Dword_list):
    return [(d & 0xFFFF, (d >> 16) & 0xFFFF) for d in Dword_list]


def cvt_registers_to_float(reg1, reg2):
    temp1 = [reg1, reg2]
    decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
        temp1, byteorder=Endian.Big, wordorder=Endian.Little
    )
    decoded_value_big_endian = decoder_big_endian.decode_32bit_float()
    return decoded_value_big_endian


def cvt_float_byte(value):
    float_as_bytes = struct.pack(">f", float(value))
    word1, word2 = struct.unpack(">HH", float_as_bytes)
    return word1, word2


def thr_check():
    global thrshd_data
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            thr_reg = (sum(1 for key in thrshd_data if "Thr_" in key)) * 2
            delay_reg = sum(1 for key in thrshd_data if "Delay_" in key)
            start_address = 1000
            total_registers = thr_reg
            read_num = 120

            for counted_num in range(0, total_registers, read_num):
                count = min(read_num, total_registers - counted_num)
                result = client.read_holding_registers(
                    start_address + counted_num, count, unit=modbus_slave_id
                )

                if result.isError():
                    print(f"Modbus Errorxxx: {result}")
                    continue
                else:
                    keys_list = list(thrshd_data.keys())
                    j = counted_num // 2
                    for i in range(0, count, 2):
                        if i + 1 < len(result.registers) and j < len(keys_list):
                            temp1 = [
                                result.registers[i],
                                result.registers[i + 1],
                            ]
                            decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                                temp1,
                                byteorder=Endian.Big,
                                wordorder=Endian.Little,
                            )
                            decoded_value_big_endian = (
                                decoder_big_endian.decode_32bit_float()
                            )
                            thrshd_data[keys_list[j]] = decoded_value_big_endian
                            j += 1

            result = client.read_holding_registers(
                1000 + thr_reg, delay_reg, unit=modbus_slave_id
            )

            if result.isError():
                print(f"Modbus Error: {result}")
            else:
                keys_list = list(thrshd_data.keys())
                j = int(thr_reg / 2)
                for i in range(0, delay_reg):
                    thrshd_data[keys_list[j]] = result.registers[i]
                    j += 1
    except Exception as e:
        print(f"thrshd check error：{e}")


def status_check():
    global status_data
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            ad_count = len(ad_sensor_value.keys())
            serial_count = len(serial_sensor_value.keys())
            all_count = (ad_count + serial_count) * 2

            r = client.read_holding_registers(5000, all_count, unit=modbus_slave_id)

            if r.isError():
                print(f"modbus error:{r}")
            else:
                key_list = list(status_data.keys())
                j = 0

                for i in range(0, all_count, 2):
                    temp1 = [r.registers[i], r.registers[i + 1]]
                    decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                        temp1, byteorder=Endian.Big, wordorder=Endian.Little
                    )
                    decoded_value_big_endian = decoder_big_endian.decode_32bit_float()
                    status_data[key_list[j]] = decoded_value_big_endian
                    j += 1
    except Exception as e:
        print(f"read status data error：{e}")


def check_high_warning(thr_key, rst_key, delay_key, type):
    short_key = thr_key.split("_")[2]

    prefix = "W_" if type == "W" else "A_"

    try:
        if time_data["check"][prefix + short_key]:
            if status_data[short_key] < thrshd_data[rst_key]:
                time_data["check"][prefix + short_key] = False
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_High"] = False
                else:
                    warning_data["alert"][short_key + "_High"] = False
                return False
            else:
                time_data["end"][prefix + short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][prefix + short_key]
                    - time_data["start"][prefix + short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    if prefix.startswith("W_"):
                        warning_data["warning"][short_key + "_High"] = True
                    else:
                        warning_data["alert"][short_key + "_High"] = True
                    # time_data["check"][prefix + short_key] = False
                    return True
        else:
            if status_data[short_key] > thrshd_data[thr_key]:
                time_data["start"][prefix + short_key] = time.perf_counter()
                time_data["check"][prefix + short_key] = True
            else:
                time_data["check"][prefix + short_key] = False
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_High"] = False
                else:
                    warning_data["alert"][short_key + "_High"] = False
                return False
    except Exception as e:
        print(f"high warning check error：{e}")


def check_low_warning(thr_key, rst_key, delay_key, type):
    short_key = thr_key.split("_")[2]

    prefix = "W_" if type == "W" else "A_"

    try:
        if time_data["check"][prefix + short_key]:
            if status_data[short_key] > thrshd_data[rst_key]:
                time_data["check"][prefix + short_key] = False
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_Low"] = False
                else:
                    warning_data["alert"][short_key + "_Low"] = False
                return False
            else:
                time_data["end"][prefix + short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][prefix + short_key]
                    - time_data["start"][prefix + short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    if prefix.startswith("W_"):
                        warning_data["warning"][short_key + "_Low"] = True
                    else:
                        warning_data["alert"][short_key + "_Low"] = True
                    return True
        else:
            if status_data[short_key] < thrshd_data[thr_key]:
                time_data["start"][prefix + short_key] = time.perf_counter()
                time_data["check"][prefix + short_key] = True
            else:
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_Low"] = False
                else:
                    warning_data["alert"][short_key + "_Low"] = False
                return False
    except Exception as e:
        print(f"low warning check error：{e}")


def check_both_warning_p3(
    thr_key_low, thr_key_high, rst_key_low, rst_key_high, delay_key, type
):
    short_key = thr_key_low.split("_")[2]
    status = status_data[short_key]

    prefix = "W_" if type == "W" else "A_"

    try:
        if time_data["check"][prefix + short_key]:
            if (
                thrshd_data[rst_key_low] < status and status < thrshd_data[rst_key_high]
            ) or (not bit_output_regs["inv1_en"] and not bit_output_regs["inv2_en"]):
                time_data["check"][prefix + short_key] = False
                time_data["condition"]["high"][prefix + short_key] = False
                time_data["condition"]["low"][prefix + short_key] = False

            else:
                if status > thrshd_data[thr_key_high]:
                    time_data["end"][prefix + short_key] = time.perf_counter()

                    passed_time = (
                        time_data["end"][prefix + short_key]
                        - time_data["start"][prefix + short_key]
                    )

                    if passed_time > thrshd_data[delay_key]:
                        time_data["condition"]["high"][prefix + short_key] = True

                if status < thrshd_data[thr_key_low]:
                    time_data["end"][prefix + short_key] = time.perf_counter()
                    passed_time = (
                        time_data["end"][prefix + short_key]
                        - time_data["start"][prefix + short_key]
                    )
                    if passed_time > thrshd_data[delay_key]:
                        time_data["condition"]["low"][prefix + short_key] = True
        else:
            if (
                status > thrshd_data[thr_key_high] or status < thrshd_data[thr_key_low]
            ) and (bit_output_regs["inv1_en"] or bit_output_regs["inv2_en"]):
                time_data["start"][prefix + short_key] = time.perf_counter()
                time_data["check"][prefix + short_key] = True
            else:
                time_data["condition"]["high"][prefix + short_key] = False
                time_data["condition"]["low"][prefix + short_key] = False

        if time_data["condition"]["high"][prefix + short_key]:
            if prefix.startswith("W_"):
                warning_data["warning"][short_key + "_High"] = True
            else:
                warning_data["alert"][short_key + "_High"] = True

        if time_data["condition"]["low"][prefix + short_key]:
            if prefix.startswith("W_"):
                warning_data["warning"][short_key + "_Low"] = True
            else:
                warning_data["alert"][short_key + "_Low"] = True

        if (
            not time_data["condition"]["high"][prefix + short_key]
            and not time_data["condition"]["low"][prefix + short_key]
        ):
            if prefix.startswith("W_"):
                warning_data["warning"][short_key + "_High"] = False
                warning_data["warning"][short_key + "_Low"] = False
            else:
                warning_data["alert"][short_key + "_High"] = False
                warning_data["alert"][short_key + "_Low"] = False

    except Exception as e:
        print(f"check both warning error：{e}")


def check_low_warning_f1(thr_key, rst_key, delay_key, type):
    short_key = "ClntFlow"

    prefix = "W_" if type == "W" else "A_"

    try:
        if time_data["check"][prefix + short_key]:
            if (status_data[short_key] > thrshd_data[rst_key]) or (
                not bit_output_regs["inv1_en"] and not bit_output_regs["inv2_en"]
            ):
                time_data["check"][prefix + short_key] = False
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_Low"] = False
                else:
                    warning_data["alert"][short_key + "_Low"] = False
                return False
            else:
                time_data["end"][prefix + short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][prefix + short_key]
                    - time_data["start"][prefix + short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    if prefix.startswith("W_"):
                        warning_data["warning"][short_key + "_Low"] = True
                    else:
                        warning_data["alert"][short_key + "_Low"] = True

                    return True
        else:
            if (status_data[short_key] < thrshd_data[thr_key]) and (
                bit_output_regs["inv1_en"] or bit_output_regs["inv2_en"]
            ):
                time_data["start"][prefix + short_key] = time.perf_counter()
                time_data["check"][prefix + short_key] = True
            else:
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_Low"] = False
                else:
                    warning_data["alert"][short_key + "_Low"] = False
                return False
    except Exception as e:
        print(f"low warning check error：{e}")


def check_dewPt_warning(thr_key, rst_key, delay_key, type):
    short_key = thr_key.split("_")[2]

    prefix = "W_" if type == "W" else "A_"

    t1 = warning_data["error"]["Temp_ClntSply_broken"]

    if t1:
        smaller_data = status_data["TempClntSplySpr"]
    else:
        smaller_data = status_data["TempClntSply"]

    try:
        if time_data["check"][prefix + short_key]:
            if smaller_data > status_data[short_key] + thrshd_data[rst_key]:
                time_data["check"][prefix + short_key] = False
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_Low"] = False
                else:
                    warning_data["alert"][short_key + "_Low"] = False
                return False
            else:
                time_data["end"][prefix + short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][prefix + short_key]
                    - time_data["start"][prefix + short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    # time_data["check"][prefix + short_key] = False
                    if prefix.startswith("W_"):
                        warning_data["warning"][short_key + "_Low"] = True
                    else:
                        warning_data["alert"][short_key + "_Low"] = True
                    return True
        else:
            if smaller_data < status_data[short_key] + thrshd_data[thr_key]:
                time_data["start"][prefix + short_key] = time.perf_counter()
                time_data["check"][prefix + short_key] = True
            else:
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_Low"] = False
                else:
                    warning_data["alert"][short_key + "_Low"] = False
                return False
    except Exception as e:
        print(f"check dewPt warning error：{e}")


def check_both_warning(
    thr_key_low, thr_key_high, rst_key_low, rst_key_high, delay_key, type
):
    short_key = thr_key_low.split("_")[2]
    status = status_data[short_key]

    prefix = "W_" if type == "W" else "A_"

    try:
        if time_data["check"][prefix + short_key]:
            if thrshd_data[rst_key_low] < status and status < thrshd_data[rst_key_high]:
                time_data["check"][prefix + short_key] = False
                time_data["condition"]["high"][prefix + short_key] = False
                time_data["condition"]["low"][prefix + short_key] = False

            else:
                if status > thrshd_data[thr_key_high]:
                    time_data["end"][prefix + short_key] = time.perf_counter()

                    passed_time = (
                        time_data["end"][prefix + short_key]
                        - time_data["start"][prefix + short_key]
                    )

                    if passed_time > thrshd_data[delay_key]:
                        time_data["condition"]["high"][prefix + short_key] = True

                if status < thrshd_data[thr_key_low]:
                    time_data["end"][prefix + short_key] = time.perf_counter()
                    passed_time = (
                        time_data["end"][prefix + short_key]
                        - time_data["start"][prefix + short_key]
                    )
                    if passed_time > thrshd_data[delay_key]:
                        time_data["condition"]["low"][prefix + short_key] = True

        else:
            if status > thrshd_data[thr_key_high] or status < thrshd_data[thr_key_low]:
                time_data["start"][prefix + short_key] = time.perf_counter()
                time_data["check"][prefix + short_key] = True

        if time_data["condition"]["high"][prefix + short_key]:
            if prefix.startswith("W_"):
                warning_data["warning"][short_key + "_High"] = True
            else:
                warning_data["alert"][short_key + "_High"] = True

        if time_data["condition"]["low"][prefix + short_key]:
            if prefix.startswith("W_"):
                warning_data["warning"][short_key + "_Low"] = True
            else:
                warning_data["alert"][short_key + "_Low"] = True

        if (
            not time_data["condition"]["high"][prefix + short_key]
            and not time_data["condition"]["low"][prefix + short_key]
        ):
            if prefix.startswith("W_"):
                warning_data["warning"][short_key + "_High"] = False
                warning_data["warning"][short_key + "_Low"] = False
            else:
                warning_data["alert"][short_key + "_High"] = False
                warning_data["alert"][short_key + "_Low"] = False

    except Exception as e:
        print(f"check both warning error：{e}")


def check_delay_EV(delay_key):
    short_key = delay_key.split("_")[1]

    try:
        if time_data["check"][short_key]:
            if (bit_output_regs[short_key] and bit_input_regs[short_key + "_Open"]) or (
                not bit_output_regs[short_key] and bit_input_regs[short_key + "_Close"]
            ):
                time_data["check"][short_key] = False
                warning_data["error"][short_key + "_Error"] = False
            else:
                time_data["end"][short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][short_key] - time_data["start"][short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    warning_data["error"][short_key + "_Error"] = True
        else:
            if (
                bit_output_regs[short_key] and not bit_input_regs[short_key + "_Open"]
            ) or (
                not bit_output_regs[short_key]
                and not bit_input_regs[short_key + "_Close"]
            ):
                time_data["start"][short_key] = time.perf_counter()
                time_data["check"][short_key] = True
            else:
                warning_data["error"][short_key + "_Error"] = False

    except Exception as e:
        print(f"check delay ev error：{e}")


def check_ol(error_key):
    short_key = error_key.replace("Delay_", "")

    try:
        if time_data["check"][short_key]:
            if not inverter_error[short_key]:
                time_data["check"][short_key] = False
                warning_data["error"][short_key] = False
            else:
                time_data["end"][short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][short_key] - time_data["start"][short_key]
                )

                if passed_time > thrshd_data[error_key]:
                    warning_data["error"][short_key] = True
        else:
            if inverter_error[short_key]:
                time_data["start"][short_key] = time.perf_counter()
                time_data["check"][short_key] = True
            else:
                warning_data["error"][short_key] = False
    except Exception as e:
        print(f"inverter overload error：{e}")


def check_waterleak(error_key):
    short_key = error_key.replace("Delay_", "")

    try:
        if time_data["check"][short_key]:
            if not bit_input_regs[short_key]:
                time_data["check"][short_key] = False
                warning_data["error"][short_key] = False
            else:
                time_data["end"][short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][short_key] - time_data["start"][short_key]
                )

                if passed_time > thrshd_data[error_key]:
                    warning_data["error"][short_key] = True
        else:
            if bit_input_regs[short_key]:
                time_data["start"][short_key] = time.perf_counter()
                time_data["check"][short_key] = True
            else:
                warning_data["error"][short_key] = False
    except Exception as e:
        print(f"check error：{e}")


def check_ATS(delay_key):
    try:
        if time_data["check"]["ATS"]:
            if ats_status["ATS1"]:
                warning_data["error"]["ATS1_Error"] = False
                time_data["check"]["ATS"] = False
                return False
            else:
                time_data["end"]["ATS"] = time.perf_counter()

                passed_time = time_data["end"]["ATS"] - time_data["start"]["ATS"]

                if passed_time > thrshd_data[delay_key]:
                    warning_data["error"]["ATS1_Error"] = True
                    return True
        else:
            if not ats_status["ATS1"]:
                time_data["start"]["ATS"] = time.perf_counter()
                time_data["check"]["ATS"] = True
            else:
                warning_data["error"]["ATS1_Error"] = False
                return False
    except Exception as e:
        print(f"ats check error：{e}")


def check_level(error_key, value_key):
    short_key = error_key.replace("Delay_", "")

    try:
        if time_data["check"][short_key]:
            if level_sw[value_key]:
                time_data["check"][short_key] = False
                warning_data["error"][short_key] = False
            else:
                time_data["end"][short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][short_key] - time_data["start"][short_key]
                )

                if passed_time > thrshd_data[error_key]:
                    warning_data["error"][short_key] = True
        else:
            if not level_sw[value_key] and level_sw[value_key] is not None:
                time_data["start"][short_key] = time.perf_counter()
                time_data["check"][short_key] = True
            else:
                warning_data["error"][short_key] = False
    except Exception as e:
        print(f"check inverter error：{e}")


def check_inv(error_key):
    short_key = error_key.replace("Delay_", "")

    try:
        if time_data["check"][short_key]:
            if bit_input_regs[short_key]:
                time_data["check"][short_key] = False
                warning_data["error"][short_key] = False
            else:
                time_data["end"][short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][short_key] - time_data["start"][short_key]
                )

                if passed_time > thrshd_data[error_key]:
                    warning_data["error"][short_key] = True
        else:
            if not bit_input_regs[short_key] and bit_input_regs[short_key] is not None:
                time_data["start"][short_key] = time.perf_counter()
                time_data["check"][short_key] = True
            else:
                warning_data["error"][short_key] = False
    except Exception as e:
        print(f"check inverter error：{e}")


def check_pressure_diff_error(thr_key, rst_key, delay_key, type):
    short_key = thr_key.split("_")[2]

    if type == "W":
        prefix = "W_"
    elif type == "A":
        prefix = "A_"

    try:
        if time_data["check"][prefix + short_key]:
            if (status_data["PrsrFltIn"] - status_data[short_key]) < thrshd_data[
                rst_key
            ]:
                time_data["check"][prefix + short_key] = False
                if prefix.startswith("W_"):
                    warning_data["warning"][short_key + "_High"] = False
                else:
                    warning_data["alert"][short_key + "_High"] = False
                return False
            else:
                time_data["end"][prefix + short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][prefix + short_key]
                    - time_data["start"][prefix + short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    if prefix.startswith("W_"):
                        warning_data["warning"][short_key + "_High"] = True
                    else:
                        warning_data["alert"][short_key + "_High"] = True
                    return True
        else:
            if (status_data["PrsrFltIn"] - status_data[short_key]) > thrshd_data[
                thr_key
            ]:
                time_data["start"][prefix + short_key] = time.perf_counter()
                time_data["check"][prefix + short_key] = True
            else:
                warning_data[short_key + "_High"] = False
                return False
    except Exception as e:
        print(f"inlet outlet warning error：{e}")


def check_comm(short_key, delay_key):
    try:
        if time_data["check"][short_key]:
            if not raw_485_communication[short_key]:
                time_data["check"][short_key] = False
                warning_data["error"][short_key + "_communication"] = False
            else:
                time_data["end"][short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][short_key] - time_data["start"][short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    warning_data["error"][short_key + "_communication"] = True
        else:
            if raw_485_communication[short_key]:
                time_data["start"][short_key] = time.perf_counter()
                time_data["check"][short_key] = True
            else:
                warning_data["error"][short_key + "_communication"] = False
    except Exception as e:
        print(f"communication error：{e}")


def check_broken(key):
    broken_mapping = {
        "Temp_ClntSply": "Delay_TempClntSply_broken",
        "Temp_ClntSplySpr": "Delay_TempClntSplySpr_broken",
        "Temp_ClntRtn": "Delay_TempClntRtn_broken",
        "Temp_WaterIn": "Delay_TempWaterIn_broken",
        "Temp_WaterOut": "Delay_TempWaterOut_broken",
        "Prsr_ClntSply": "Delay_PrsrClntSply_broken",
        "Prsr_ClntSplySpr": "Delay_PrsrClntSplySpr_broken",
        "Prsr_ClntRtn": "Delay_PrsrClntRtn_broken",
        "Prsr_ClntRtnSpr": "Delay_PrsrClntRtnSpr_broken",
        "Prsr_FltIn": "Delay_PrsrFltIn_broken",
        "Prsr_Flt1Out": "Delay_PrsrFlt1Out_broken",
        "Prsr_Flt2Out": "Delay_PrsrFlt2Out_broken",
        "Prsr_Flt3Out": "Delay_PrsrFlt3Out_broken",
        "Prsr_Flt4Out": "Delay_PrsrFlt4Out_broken",
        "Prsr_Flt5Out": "Delay_PrsrFlt5Out_broken",
        "Prsr_WtrIn": "Delay_PrsrWaterIn_broken",
        "Prsr_WtrOut": "Delay_PrsrWaterOut_broken",
        "Clnt_Flow": "Delay_Clnt_Flow_broken",
        "Wtr_Flow": "Delay_Wtr_Flow_broken",
    }

    delay_key = broken_mapping[key]
    error_key = f"{key}_broken"

    if "Temp" in key:
        try:
            if time_data["check"][key]:
                if sensor_raw[key] < 1000 and sensor_raw[key] > -100:
                    time_data["check"][key] = False
                    warning_data["error"][error_key] = False
                else:
                    time_data["end"][key] = time.perf_counter()

                    passed_time = time_data["end"][key] - time_data["start"][key]

                    if passed_time > thrshd_data[delay_key]:
                        warning_data["error"][error_key] = True

            else:
                if sensor_raw[key] > 1000 or sensor_raw[key] < -100:
                    time_data["start"][key] = time.perf_counter()
                    time_data["check"][key] = True
                else:
                    warning_data["error"][error_key] = False
        except Exception as e:
            print(f"broken temp error：{e}")

    elif "Prsr" in key:
        try:
            if time_data["check"][key]:
                if sensor_raw[key] > 1200:
                    time_data["check"][key] = False
                    warning_data["error"][error_key] = False
                else:
                    time_data["end"][key] = time.perf_counter()

                    passed_time = time_data["end"][key] - time_data["start"][key]

                    if passed_time > thrshd_data[delay_key]:
                        warning_data["error"][error_key] = True
            else:
                if sensor_raw[key] < 1200:
                    time_data["start"][key] = time.perf_counter()
                    time_data["check"][key] = True
                else:
                    warning_data["error"][error_key] = False
        except Exception as e:
            print(f"broken prsr error：{e}")

    if not ver_switch["flow_switch"]:
        if key == "Clnt_Flow":
            try:
                if time_data["check"][key]:
                    if (
                        serial_sensor_value[key] > 1000
                        and serial_sensor_value[key] < 20000
                    ):
                        time_data["check"][key] = False
                        warning_data["error"][error_key] = False
                    else:
                        time_data["end"][key] = time.perf_counter()

                        passed_time = time_data["end"][key] - time_data["start"][key]

                        if passed_time > thrshd_data[delay_key]:
                            warning_data["error"][error_key] = True
                else:
                    if (
                        serial_sensor_value[key] < 1000
                        or serial_sensor_value[key] > 20000
                    ):
                        time_data["start"][key] = time.perf_counter()
                        time_data["check"][key] = True
                    else:
                        warning_data["error"][error_key] = False
            except Exception as e:
                print(f"broken flow error：{e}")

    if not ver_switch["flow2_switch"]:
        if key == "Wtr_Flow":
            try:
                if time_data["check"][key]:
                    if (
                        serial_sensor_value[key] > 1000
                        and serial_sensor_value[key] < 20000
                    ):
                        time_data["check"][key] = False
                        warning_data["error"][error_key] = False
                    else:
                        time_data["end"][key] = time.perf_counter()

                        passed_time = time_data["end"][key] - time_data["start"][key]

                        if passed_time > thrshd_data[delay_key]:
                            warning_data["error"][error_key] = True
                else:
                    if (
                        serial_sensor_value[key] < 1000
                        or serial_sensor_value[key] > 20000
                    ):
                        time_data["start"][key] = time.perf_counter()
                        time_data["check"][key] = True
                    else:
                        warning_data["error"][error_key] = False
            except Exception as e:
                print(f"broken flow error：{e}")


def check_waterpv_error(delay_key):
    short_key = delay_key.replace("Delay_", "")

    status_water = status_data["WaterPV"]
    with ModbusTcpClient(
        host=modbus_host, port=modbus_port, unit=modbus_slave_id
    ) as client:
        r = client.read_holding_registers((20480 + 6380), 1)
        sd_water = r.registers[0]
        sd_water = int(sd_water / 16000 * 100)

    try:
        if time_data["check"][short_key]:
            if status_water + 10 >= sd_water >= status_water - 10:
                time_data["check"][short_key] = False
                warning_data["error"]["WaterPV_Error"] = False
                return False
            else:
                time_data["end"][short_key] = time.perf_counter()

                passed_time = (
                    time_data["end"][short_key] - time_data["start"][short_key]
                )

                if passed_time > thrshd_data[delay_key]:
                    warning_data["error"]["WaterPV_Error"] = True
                    return True
        else:
            if status_water - 10 < sd_water or sd_water > status_water + 10:
                time_data["start"][short_key] = time.perf_counter()
                time_data["check"][short_key] = True
            else:
                warning_data["error"]["WaterPV_Error"] = False
                return False
    except Exception as e:
        print(f"water pv error：{e}")


def set_warning_registers(f1_issue, mode):
    global thrshd_data, status_data, x, warning_light

    thr_check()
    status_check()

    check_comm("inv1_speed", "Delay_Inverter1_Communication")
    check_comm("inv2_speed", "Delay_Inverter2_Communication")
    check_comm("ambient_temperature", "Delay_Ambient_Sensor_Communication")
    check_comm("coolant_flow_rate", "Delay_Coolant_Flow_Meter_Communication")
    check_comm("facility_water_flow_rate", "Delay_Water_Flow_Meter_Communication")
    check_comm("conductivity", "Delay_Conductivity_Sensor_Communication")
    check_comm("ph", "Delay_pH_Sensor_Communication")
    check_comm("turbidity", "Delay_Turbidity_Sensor_Communication")
    check_comm("ATS1", "Delay_ATS_Communication")
    check_comm("instant_power_consumption", "Delay_Power_Meter_Communication")

    check_high_warning(
        "Thr_W_TempClntSply",
        "Thr_W_Rst_TempClntSply",
        "Delay_TempClntSply",
        "W",
    )

    check_high_warning(
        "Thr_A_TempClntSply",
        "Thr_A_Rst_TempClntSply",
        "Delay_TempClntSply",
        "A",
    )

    check_high_warning(
        "Thr_W_TempClntSplySpr",
        "Thr_W_Rst_TempClntSplySpr",
        "Delay_TempClntSplySply",
        "W",
    )

    check_high_warning(
        "Thr_A_TempClntSplySpr",
        "Thr_A_Rst_TempClntSplySpr",
        "Delay_TempClntSplySply",
        "A",
    )

    check_high_warning(
        "Thr_W_TempClntRtn",
        "Thr_W_Rst_TempClntRtn",
        "Delay_TempClntRtn",
        "W",
    )
    check_high_warning(
        "Thr_A_TempClntRtn",
        "Thr_A_Rst_TempClntRtn",
        "Delay_TempClntRtn",
        "A",
    )

    check_both_warning(
        "Thr_W_TempWaterIn_L",
        "Thr_W_TempWaterIn_H",
        "Thr_W_Rst_TempWaterIn_L",
        "Thr_W_Rst_TempWaterIn_H",
        "Delay_TempWaterIn",
        "W",
    )
    check_both_warning(
        "Thr_A_TempWaterIn_L",
        "Thr_A_TempWaterIn_H",
        "Thr_A_Rst_TempWaterIn_L",
        "Thr_A_Rst_TempWaterIn_H",
        "Delay_TempWaterIn",
        "A",
    )

    check_both_warning(
        "Thr_W_TempWaterOut_L",
        "Thr_W_TempWaterOut_H",
        "Thr_W_Rst_TempWaterOut_L",
        "Thr_W_Rst_TempWaterOut_H",
        "Delay_TempWaterOut",
        "W",
    )

    check_both_warning(
        "Thr_A_TempWaterOut_L",
        "Thr_A_TempWaterOut_H",
        "Thr_A_Rst_TempWaterOut_L",
        "Thr_A_Rst_TempWaterOut_H",
        "Delay_TempWaterOut",
        "A",
    )

    check_high_warning(
        "Thr_W_PrsrClntSply",
        "Thr_W_Rst_PrsrClntSply",
        "Delay_PrsrClntSply",
        "W",
    )

    check_high_warning(
        "Thr_A_PrsrClntSply",
        "Thr_A_Rst_PrsrClntSply",
        "Delay_PrsrClntSply",
        "A",
    )

    check_high_warning(
        "Thr_W_PrsrClntSplySpr",
        "Thr_W_Rst_PrsrClntSplySpr",
        "Delay_PrsrClntSplySpr",
        "W",
    )

    check_high_warning(
        "Thr_A_PrsrClntSplySpr",
        "Thr_A_Rst_PrsrClntSplySpr",
        "Delay_PrsrClntSplySpr",
        "A",
    )

    check_high_warning(
        "Thr_W_PrsrClntRtn",
        "Thr_W_Rst_PrsrClntRtn",
        "Delay_PrsrClntRtn",
        "W",
    )

    check_high_warning(
        "Thr_A_PrsrClntRtn",
        "Thr_A_Rst_PrsrClntRtn",
        "Delay_PrsrClntRtn",
        "A",
    )

    check_high_warning(
        "Thr_W_PrsrClntRtnSpr",
        "Thr_W_Rst_PrsrClntRtnSpr",
        "Delay_PrsrClntRtnSpr",
        "W",
    )

    check_high_warning(
        "Thr_A_PrsrClntRtnSpr",
        "Thr_A_Rst_PrsrClntRtnSpr",
        "Delay_PrsrClntRtnSpr",
        "A",
    )

    check_both_warning_p3(
        "Thr_W_PrsrFltIn_L",
        "Thr_W_PrsrFltIn_H",
        "Thr_W_Rst_PrsrFltIn_L",
        "Thr_W_Rst_PrsrFltIn_H",
        "Delay_PrsrFltIn",
        "W",
    )

    check_both_warning_p3(
        "Thr_A_PrsrFltIn_L",
        "Thr_A_PrsrFltIn_H",
        "Thr_A_Rst_PrsrFltIn_L",
        "Thr_A_Rst_PrsrFltIn_H",
        "Delay_PrsrFltIn",
        "A",
    )

    check_pressure_diff_error(
        "Thr_W_PrsrFlt1Out_H",
        "Thr_W_Rst_PrsrFlt1Out_H",
        "Delay_PrsrFlt1Out",
        "W",
    )

    check_pressure_diff_error(
        "Thr_A_PrsrFlt1Out_H",
        "Thr_A_Rst_PrsrFlt1Out_H",
        "Delay_PrsrFlt1Out",
        "A",
    )

    check_pressure_diff_error(
        "Thr_W_PrsrFlt2Out_H",
        "Thr_W_Rst_PrsrFlt2Out_H",
        "Delay_PrsrFlt2Out",
        "W",
    )

    check_pressure_diff_error(
        "Thr_A_PrsrFlt2Out_H",
        "Thr_A_Rst_PrsrFlt2Out_H",
        "Delay_PrsrFlt2Out",
        "A",
    )

    check_pressure_diff_error(
        "Thr_W_PrsrFlt3Out_H",
        "Thr_W_Rst_PrsrFlt3Out_H",
        "Delay_PrsrFlt3Out",
        "W",
    )

    check_pressure_diff_error(
        "Thr_A_PrsrFlt3Out_H",
        "Thr_A_Rst_PrsrFlt3Out_H",
        "Delay_PrsrFlt3Out",
        "A",
    )

    check_pressure_diff_error(
        "Thr_W_PrsrFlt4Out_H",
        "Thr_W_Rst_PrsrFlt4Out_H",
        "Delay_PrsrFlt4Out",
        "W",
    )

    check_pressure_diff_error(
        "Thr_A_PrsrFlt4Out_H",
        "Thr_A_Rst_PrsrFlt4Out_H",
        "Delay_PrsrFlt4Out",
        "A",
    )

    check_pressure_diff_error(
        "Thr_W_PrsrFlt5Out_H",
        "Thr_W_Rst_PrsrFlt5Out_H",
        "Delay_PrsrFlt5Out",
        "W",
    )

    check_pressure_diff_error(
        "Thr_A_PrsrFlt5Out_H",
        "Thr_A_Rst_PrsrFlt5Out_H",
        "Delay_PrsrFlt5Out",
        "A",
    )

    check_high_warning(
        "Thr_W_PrsrWaterIn",
        "Thr_W_Rst_PrsrWaterIn",
        "Delay_PrsrWaterIn",
        "W",
    )

    check_high_warning(
        "Thr_A_PrsrWaterIn",
        "Thr_A_Rst_PrsrWaterIn",
        "Delay_PrsrWaterIn",
        "A",
    )

    check_high_warning(
        "Thr_W_PrsrWaterOut",
        "Thr_W_Rst_PrsrWaterOut",
        "Delay_PrsrWaterOut",
        "W",
    )

    check_high_warning(
        "Thr_A_PrsrWaterOut",
        "Thr_A_Rst_PrsrWaterOut",
        "Delay_PrsrWaterOut",
        "A",
    )

    check_both_warning(
        "Thr_W_RltvHmd_L",
        "Thr_W_RltvHmd_H",
        "Thr_W_Rst_RltvHmd_L",
        "Thr_W_Rst_RltvHmd_H",
        "Delay_RltvHmd",
        "W",
    )

    check_both_warning(
        "Thr_A_RltvHmd_L",
        "Thr_A_RltvHmd_H",
        "Thr_A_Rst_RltvHmd_L",
        "Thr_A_Rst_RltvHmd_H",
        "Delay_RltvHmd",
        "A",
    )

    check_both_warning(
        "Thr_W_TempAmbient_L",
        "Thr_W_TempAmbient_H",
        "Thr_W_Rst_TempAmbient_L",
        "Thr_W_Rst_TempAmbient_H",
        "Delay_TempAmbient",
        "W",
    )

    check_both_warning(
        "Thr_A_TempAmbient_L",
        "Thr_A_TempAmbient_H",
        "Thr_A_Rst_TempAmbient_L",
        "Thr_A_Rst_TempAmbient_H",
        "Delay_TempAmbient",
        "A",
    )

    check_low_warning(
        "Thr_W_WaterFlow",
        "Thr_W_Rst_WaterFlow",
        "Delay_WaterFlow",
        "W",
    )

    check_low_warning(
        "Thr_A_WaterFlow",
        "Thr_A_Rst_WaterFlow",
        "Delay_WaterFlow",
        "A",
    )

    check_both_warning(
        "Thr_W_pH_L",
        "Thr_W_pH_H",
        "Thr_W_Rst_pH_L",
        "Thr_W_Rst_pH_H",
        "Delay_pH",
        "W",
    )

    check_both_warning(
        "Thr_A_pH_L",
        "Thr_A_pH_H",
        "Thr_A_Rst_pH_L",
        "Thr_A_Rst_pH_H",
        "Delay_pH",
        "A",
    )

    check_both_warning(
        "Thr_W_Cdct_L",
        "Thr_W_Cdct_H",
        "Thr_W_Rst_Cdct_L",
        "Thr_W_Rst_Cdct_H",
        "Delay_Cdct",
        "W",
    )

    check_both_warning(
        "Thr_A_Cdct_L",
        "Thr_A_Cdct_H",
        "Thr_A_Rst_Cdct_L",
        "Thr_A_Rst_Cdct_H",
        "Delay_Cdct",
        "A",
    )

    check_both_warning(
        "Thr_W_Tbt_L",
        "Thr_W_Tbt_H",
        "Thr_W_Rst_Tbt_L",
        "Thr_W_Rst_Tbt_H",
        "Delay_Tbt",
        "W",
    )

    check_both_warning(
        "Thr_A_Tbt_L",
        "Thr_A_Tbt_H",
        "Thr_A_Rst_Tbt_L",
        "Thr_A_Rst_Tbt_H",
        "Delay_Tbt",
        "A",
    )

    check_high_warning(
        "Thr_W_AC_H",
        "Thr_W_Rst_AC_H",
        "Delay_AC",
        "W",
    )

    check_high_warning(
        "Thr_A_AC_H",
        "Thr_A_Rst_AC_H",
        "Delay_AC",
        "A",
    )

    check_low_warning_f1(
        "Thr_W_ClntFlow",
        "Thr_W_Rst_ClntFlow",
        "Delay_ClntFlow",
        "W",
    )

    check_low_warning_f1(
        "Thr_A_ClntFlow",
        "Thr_A_Rst_ClntFlow",
        "Delay_ClntFlow",
        "A",
    )

    check_delay_EV("Delay_EV1")
    check_delay_EV("Delay_EV2")
    check_delay_EV("Delay_EV3")
    check_delay_EV("Delay_EV4")

    check_ol("Delay_Inv1_OverLoad")
    check_ol("Delay_Inv2_OverLoad")
    check_inv("Delay_Inv1_Error")
    check_inv("Delay_Inv2_Error")

    check_waterleak("Delay_Water_Leak")
    check_waterleak("Delay_Water_Leak_Broken")

    check_waterpv_error("Delay_WaterPV")
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            r = client.read_coils((8192 + 10), 2, unit=modbus_slave_id)

            ats_status["ATS1"] = r.bits[0]
            ats_status["ATS2"] = r.bits[1]
    except Exception as e:
        print(f"ATS issue:{e}")

    if not bit_output_regs["mc1"]:
        warning_data["error"]["inv1_speed_communication"] = True

    if not bit_output_regs["mc2"]:
        warning_data["error"]["inv2_speed_communication"] = True

    check_ATS("Delay_ATS")

    check_dewPt_warning(
        "Thr_W_TempCds",
        "Thr_W_Rst_TempCds",
        "Delay_TempCds",
        "W",
    )

    check_dewPt_warning(
        "Thr_A_TempCds",
        "Thr_A_Rst_TempCds",
        "Delay_TempCds",
        "A",
    )

    check_level("Delay_level1_error", "level1")
    check_level("Delay_level2_error", "level2")
    check_level("Delay_power1_error", "power1")
    check_level("Delay_power2_error", "power2")
    check_level("Delay_level3_error", "level3")

    if warning_data["alert"]["TempCds_Low"]:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils((8192 + 12), [True])
        except Exception as e:
            print(f"dewpt error document error: {e}")
    else:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils((8192 + 12), [False])
        except Exception as e:
            print(f"dewpt error document error: {e}")

    warning_key = list(warning_data["warning"].keys())
    warning_key_len = len(warning_data["warning"].keys())
    warning_reg = (warning_key_len // 16) + (1 if warning_key_len % 16 != 0 else 0)
    value_w = [0] * warning_reg
    for i in range(0, warning_key_len):
        key = warning_key[i]
        # warning_data["warning"][key] = False
        # warning_data["warning"][key] = True
        if warning_data["warning"][key]:
            value_w[i // 16] |= 1 << (i % 16)

    alert_key = list(warning_data["alert"].keys())
    alert_key_len = len(warning_data["alert"].keys())
    alert_reg = (alert_key_len // 16) + (1 if alert_key_len % 16 != 0 else 0)
    value_a = [0] * alert_reg
    for i in range(0, alert_key_len):
        key = alert_key[i]
        # warning_data["alert"][key] = False
        # warning_data["alert"][key] = True
        if warning_data["alert"][key]:
            value_a[i // 16] |= 1 << (i % 16)

    error_key = list(warning_data["error"].keys())
    err_key_len = len(warning_data["error"].keys())
    err_reg = (err_key_len // 16) + (1 if err_key_len % 16 != 0 else 0)
    value_e = [0] * err_reg
    for i in range(0, err_key_len):
        key = error_key[i]
        # warning_data["error"][key] = False
        # warning_data["error"][key] = True
        # warning_data["error"]["inv1_speed_communication"] = False
        if warning_data["error"][key]:
            value_e[i // 16] |= 1 << (i % 16)

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(1700, value_w)
            client.write_registers(1705, value_a)
            client.write_registers(1708, value_e)
    except Exception as e:
        print(f"store in 16 bits error{e}")

    ignore_key = ["ATS1_Error"]

    sensor_key_map = {
        "Temp_ClntSplySpr": ["TempClntSplySpr_High", "Temp_ClntSplySpr_broken"],
        "Prsr_ClntSplySpr": ["Prsr_ClntSplySpr_broken", "PrsrClntSplySpr_High"],
        "Prsr_ClntRtnSpr": ["Prsr_ClntRtnSpr_broken", "PrsrClntRtnSpr_High"],
    }

    for sensor, keys in sensor_key_map.items():
        if sensor_factor.get(sensor) == 0:
            ignore_key.extend(keys)

    if ver_switch["flow_switch"]:
        ignore_key.append("Clnt_Flow_broken")
    else:
        ignore_key.append("coolant_flow_rate_communication")

    if ver_switch["flow2_switch"]:
        ignore_key.append("Wtr_Flow_broken")
    else:
        ignore_key.append("facility_water_flow_rate_communication")

    if ver_switch["function_switch"]:
        ignore_key.append("PrsrClntRtnSpr_High")
        ignore_key.append("Prsr_ClntRtnSpr_broken")

    if onLinux:
        try:
            if mode == "inspection":
                bit_output_regs["led_err"] = False
            elif (
                any(
                    value
                    for key, value in warning_data["warning"].items()
                    if key not in ignore_key
                )
                or any(
                    value
                    for key, value in warning_data["alert"].items()
                    if key not in ignore_key
                )
                or any(
                    value
                    for key, value in warning_data["error"].items()
                    if key not in ignore_key
                )
            ):
                bit_output_regs["led_err"] = warning_light
                warning_light = not warning_light
            else:
                bit_output_regs["led_err"] = False

        except Exception as e:
            print(f"warning light error:{e}")


def check_both_overload():
    if inverter_error["Inv1_OverLoad"] and inverter_error["Inv2_OverLoad"]:
        close_ev1()
        close_ev2()
        close_ev3()
        close_ev4()
        bit_output_regs["inv1_en"] = False
        bit_output_regs["inv2_en"] = False


def open_ev1():
    bit_output_regs["EV1"] = True


def close_ev1():
    bit_output_regs["EV1"] = False


def open_ev2():
    bit_output_regs["EV2"] = True


def close_ev2():
    bit_output_regs["EV2"] = False


def open_ev3():
    bit_output_regs["EV3"] = True


def close_ev3():
    bit_output_regs["EV3"] = False


def open_ev4():
    bit_output_regs["EV4"] = True


def close_ev4():
    bit_output_regs["EV4"] = False


def set_pump1_speed(speed):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register((20480 + 6300), speed)

    except Exception as e:
        print(f"set pump1 speed error: {e}")


def set_pump2_speed(speed):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register((20480 + 6340), speed)

    except Exception as e:
        print(f"set pump2 speed error: {e}")


def set_water_pv(pv):
    try:
        new_pv = int(pv / 100 * 16000)
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(20480 + 6380, new_pv)

    except Exception as e:
        print(f"set water pv error: {e}")


def cause_ol(oc_issue, mode):
    global previous_inv1, previous_inv2

    if oc_detection["M20"]:
        inverter_error["Inv1_OverLoad"] = True

    if oc_detection["M21"]:
        inverter_error["Inv2_OverLoad"] = True

    if oc_issue:
        if previous_inv1:
            inverter_error["Inv1_OverLoad"] = True

        if previous_inv2:
            inverter_error["Inv2_OverLoad"] = True

        if mode == "auto" and not bit_output_regs["mc1"] and not bit_output_regs["mc2"]:
            inverter_error["Inv1_OverLoad"] = True
            inverter_error["Inv2_OverLoad"] = True


def check_mc():
    if (
        not inverter_error["Inv1_OverLoad"]
        or not bit_input_regs["Inv1_Error"]
        or not warning_data["alert"]["ClntFlow_Low"]
    ):
        bit_output_regs["mc1"] = True
    else:
        bit_output_regs["mc1"] = False

    if (
        not inverter_error["Inv2_OverLoad"]
        or not bit_input_regs["Inv2_Error"]
        or not warning_data["alert"]["ClntFlow_Low"]
    ):
        bit_output_regs["mc2"] = True
    else:
        bit_output_regs["mc2"] = False


def uint16_to_int16(value):
    if value >= 32768:
        return value - 65536
    return value


def reset_mc():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coils(800, [False])
    except Exception as e:
        print(f"reset mc error:{e}")
    inverter_error["Inv1_OverLoad"] = False
    inverter_error["Inv2_OverLoad"] = False


def reset_btn_false():
    reset_current_btn["status"] = False
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coils((8192 + 800), [False])
    except Exception as e:
        print(f"reset btn error:{e}")


def clear_p1_speed():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(246, [0, 0])
    except Exception as e:
        print(f"clear p1 speed error:{e}")


def clear_p2_speed():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(222, [0, 0])
    except Exception as e:
        print(f"clear p2 speed error:{e}")


def inspect_ev(ev1, ev2, ev3, ev4):
    evs = [ev1, ev2, ev3, ev4]
    for i, ev in enumerate(evs, start=1):
        status = "open" if "Open" in ev else "close"
        status_input = "Open" if "Open" in ev else "Close"
        is_open = bit_input_regs[f"EV{i}_{status_input}"]

        if is_open and status == "open":
            inspection_data["result"][f"ev{i}_{status}"] = False
        elif not is_open and status == "open":
            inspection_data["result"][f"ev{i}_{status}"] = True
        elif is_open and status == "close":
            inspection_data["result"][f"ev{i}_{status}"] = False
        elif not is_open and status == "close":
            inspection_data["result"][f"ev{i}_{status}"] = True


def write_measured_data(number, data):
    registers = []

    word1, word2 = cvt_float_byte(data)
    registers.append(word2)
    registers.append(word1)

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers((900 + number), registers)
    except Exception as e:
        print(f"send messure p1:{e}")


def change_progress(key, status):
    if status == "standby":
        inspection_data["progress"][key] = 4

    elif status == "finish":
        inspection_data["progress"][key] = 2

    elif status == "skip":
        inspection_data["progress"][key] = 5

    elif status == "cancel":
        inspection_data["progress"][key] = 1


def cancel_inspection():
    try:
        value_list_status = list(inspection_data["progress"].values())
        value_list_status = [1 if value == 4 else value for value in value_list_status]
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(800, value_list_status)
    except Exception as e:
        print(f"result write-in:{e}")

    for key, status in inspection_data["progress"].items():
        if status == 1:
            inspection_data["result"][key] = False

    try:
        value_list_result = [
            1 if value else 0 for value in inspection_data["result"].values()
        ]
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(750, value_list_result)
    except Exception as e:
        print(f"result write-in:{e}")

    inspection_data["step"] = 1
    inspection_data["start_time"] = 0
    inspection_data["mid_time"] = 0
    inspection_data["end_time"] = 0

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(973, 2)
    except Exception as e:
        print(f"set inspect action error:{e}")

    print("被切掉模式")


def check_last_mode_from_inspection(mode_last):
    one_time = True
    if mode_last == "inspection":
        if one_time:
            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_coils((8192 + 600), 1, unit=modbus_slave_id)
                    inspection_data["force_change_mode"] = r.bits[0]
            except Exception as e:
                print(f"read force change mode error:{e}")
            one_time = False
    else:
        inspection_data["force_change_mode"] = False


def go_back_to_last_mode(mode, water_pv_set):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(950, 1)

            client.write_coil(0, inspection_data["prev"]["inv1"])
            client.write_coil(1, inspection_data["prev"]["inv2"])

            set_water_pv(water_pv_set)

            if mode == "manual":
                client.write_coils((8192 + 517), [False])
                client.write_coils((8192 + 505), [True])
            elif mode == "engineer":
                client.write_coils((8192 + 517), [False])
                client.write_coils((8192 + 516), [True])
            elif mode == "auto":
                client.write_coils((8192 + 517), [False])
                client.write_coils((8192 + 505), [False])
            elif mode == "stop":
                client.write_coils((8192 + 517), [False])
                client.write_coils((8192 + 514), [False])
            else:
                client.write_coils((8192 + 517), [False])
                client.write_coils((8192 + 505), [True])

    except Exception as e:
        print(f"respec error:{e}")


def reset_inspect_btn():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(900, 3)
            inspection_data["start_btn"] = 3
    except Exception as e:
        print(f"close inspection:{e}")


def send_progress(number, key):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers((800 + number), inspection_data["progress"][key])
    except Exception as e:
        print(f"result write-in:{e}")


def send_all(number, key):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers((800 + number), inspection_data["progress"][key])

            result = [1 if inspection_data["result"][key] else 0]
            client.write_registers((750 + number), result)
    except Exception as e:
        print(f"result write-in:{e}")


def change_inspect_time():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(950, 2)

    except Exception as e:
        print(f"change_inspect_time:{e}")


def control():
    global check_server2, server2_occur_stop, pre_check_server2

    mode_last = ""
    pump1_run_last_min = time.time()
    pump2_run_last_min = time.time()
    mode = ""
    global \
        previous_inv, \
        f1_issue, \
        previous_inv1, \
        previous_inv2, \
        change_back_mode, \
        oc_issue, \
        diff, \
        f1_data, \
        pump_signial, \
        water_pv_set
    global one_time_stop, auto_flag, port
    global \
        count_f1, \
        p1_data, \
        p2_data, \
        zero_flag, \
        rtu_flag, \
        previous_ver, \
        oc_trigger, \
        p1_error_box, \
        p2_error_box
    clnt_flow_data = deque(maxlen=20)
    wrt_flow_data = deque(maxlen=20)

    while True:
        try:
            restart_server["start"] = time.time()
            server_error["start"] = time.time()
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    value_list = [raw_485_data[key] for key in raw_485_data]
                    new_list = []

                    for value in value_list:
                        r1, r2 = cvt_float_byte(value)
                        new_list.append(r2)
                        new_list.append(r1)
                    client.write_registers(18, new_list)

            except Exception as e:
                print(f"485 error:{e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_coil((8192 + 10), raw_485_data["ATS1"])
                    client.write_coil((8192 + 11), raw_485_data["ATS2"])
            except Exception as e:
                print(f"485 ATS 1&2 error:{e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_coils((8192 + 801), 4)

                    ver_switch["function_switch"] = r.bits[0]
                    ver_switch["flow_switch"] = r.bits[1]
                    ver_switch["flow2_switch"] = r.bits[2]
                    ver_switch["median_switch"] = r.bits[3]

                    if previous_ver is None:
                        rtu_flag = True
                    elif previous_ver != ver_switch["function_switch"]:
                        rtu_flag = True
                    previous_ver = ver_switch["function_switch"]
            except Exception as e:
                print(f"check version: {e}")

            if ver_switch["function_switch"]:
                port = "/dev/ttyS1"
            else:
                port = "/dev/ttyS0"

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_coils((8192 + 800), 1)
                    reset_current_btn["status"] = r.bits[0]
            except Exception as e:
                print(f"check reset btn reset:{e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_holding_registers(900, 1)
                    inspection_data["start_btn"] = r.registers[0]
            except Exception as e:
                print(f"check inspection btn reset:{e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_discrete_inputs(0, 12, unit=modbus_slave_id)

                    keys = list(bit_input_regs.keys())
                    for i in range(0, 12):
                        bit_input_regs[keys[i]] = r.bits[i]
            except Exception as e:
                print(f"read input error {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    value_list = list(inv_error_code.values())
                    client.write_registers(1750, value_list)

            except Exception as e:
                print(f"inv error code: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    ad_count = len(ad_sensor_value.keys())
                    serial_count = len(serial_sensor_value.keys()) - 1
                    all_count = ad_count + serial_count * 2

                    all_sensors = client.read_holding_registers(
                        0, all_count, unit=modbus_slave_id
                    )

                    if all_sensors.isError():
                        print(f"Modbus Error: {all_sensors}")
                    else:
                        keys_list = list(ad_sensor_value.keys())

                        for i in range(0, ad_count):
                            value = all_sensors.registers[i]
                            value_translate = uint16_to_int16(value)
                            sensor_raw[keys_list[i]] = value_translate

                    key_list = list(sensor_raw.keys())

                    for key in key_list:
                        if (
                            ("Temp" in key or "Prsr" in key)
                            and key != "Temp_Ambient"
                            and key != "Dew_Point_Temp"
                        ):
                            check_broken(key)

                    for key in key_list:
                        if (
                            "Prsr" in key
                            and key != "Prsr_WtrOut"
                            and key != "Prsr_ClntRtn"
                            and key != "Prsr_ClntRtnSpr"
                        ):
                            if 6400 > sensor_raw[key] > 6080:
                                sensor_raw[key] = 6400
                        elif key == "Prsr_WtrOut":
                            if 3200 > sensor_raw[key] > 3040:
                                sensor_raw[key] = 3200

                    ad_sensor_value["Temp_ClntSply"] = (
                        float(sensor_raw["Temp_ClntSply"]) / 10.0
                    )
                    ad_sensor_value["Temp_ClntSplySpr"] = (
                        float(sensor_raw["Temp_ClntSplySpr"]) / 10.0
                    )
                    ad_sensor_value["Temp_ClntRtn"] = (
                        float(sensor_raw["Temp_ClntRtn"]) / 10.0
                    )
                    ad_sensor_value["Temp_WaterIn"] = (
                        float(sensor_raw["Temp_WaterIn"]) / 10.0
                    )
                    ad_sensor_value["Temp_WaterOut"] = (
                        float(sensor_raw["Temp_WaterOut"]) / 10.0
                    )
                    ad_sensor_value["Prsr_ClntSply"] = (
                        float(sensor_raw["Prsr_ClntSply"]) - 6400
                    ) / 25600
                    ad_sensor_value["Prsr_ClntSplySpr"] = (
                        float(sensor_raw["Prsr_ClntSplySpr"]) - 6400
                    ) / 25600.0
                    ad_sensor_value["Prsr_ClntRtn"] = (
                        float(sensor_raw["Prsr_ClntRtn"] - 6400)
                    ) / 25600.0
                    ad_sensor_value["Prsr_FltIn"] = (
                        float(sensor_raw["Prsr_FltIn"]) - 6400
                    ) / 25600.0
                    ad_sensor_value["Prsr_Flt1Out"] = (
                        float(sensor_raw["Prsr_Flt1Out"]) - 6400
                    ) / 25600.0
                    ad_sensor_value["Prsr_Flt2Out"] = (
                        float(sensor_raw["Prsr_Flt2Out"]) - 6400
                    ) / 25600.0
                    ad_sensor_value["Prsr_Flt3Out"] = (
                        float(sensor_raw["Prsr_Flt3Out"]) - 6400
                    ) / 25600.0
                    ad_sensor_value["Prsr_Flt4Out"] = (
                        float(sensor_raw["Prsr_Flt4Out"]) - 6400
                    ) / 25600.0
                    ad_sensor_value["Prsr_Flt5Out"] = (
                        float(sensor_raw["Prsr_Flt5Out"]) - 6400
                    ) / 25600.0
                    ad_sensor_value["Prsr_ClntRtnSpr"] = (
                        float(sensor_raw["Prsr_ClntRtnSpr"] - 6400)
                    ) / 25600.0
                    ad_sensor_value["Prsr_WtrIn"] = (
                        float(sensor_raw["Prsr_WtrIn"]) - 6400
                    ) / 25600
                    ad_sensor_value["Prsr_WtrOut"] = (
                        float(sensor_raw["Prsr_WtrOut"]) - 3200
                    ) / 12800
                    ad_sensor_value["PV_Wtr"] = (
                        float(sensor_raw["PV_Wtr"]) / 16000.0 * 100.0
                    )

                    keys_list = list(serial_sensor_value.keys())
                    j = 0
                    for i in range(ad_count, all_count, 2):
                        temp1 = [all_sensors.registers[i], all_sensors.registers[i + 1]]
                        decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                            temp1, byteorder=Endian.Big, wordorder=Endian.Little
                        )
                        try:
                            decoded_value = decoder_big_endian.decode_32bit_float()
                            if decoded_value != decoded_value:
                                print(f"key {keys_list[j]} results NaN")
                            else:
                                serial_sensor_value[keys_list[j]] = decoded_value
                        except Exception as e:
                            print(f"{keys_list[j]} value error：{e}")
                        j += 1

                    if not ver_switch["flow_switch"]:
                        try:
                            f1 = client.read_holding_registers((20480 + 6740), 1)

                            if not f1.isError():
                                serial_sensor_value["Clnt_Flow"] = f1.registers[0]
                                if serial_sensor_value["Clnt_Flow"] > 32767:
                                    serial_sensor_value["Clnt_Flow"] = (
                                        65535 - serial_sensor_value["Clnt_Flow"]
                                    )
                                if 3200 > serial_sensor_value["Clnt_Flow"] > 3040:
                                    serial_sensor_value["Clnt_Flow"] = 3200
                                sensor_raw["Clnt_Flow"] = serial_sensor_value[
                                    "Clnt_Flow"
                                ]
                                check_broken("Clnt_Flow")
                                serial_sensor_value["Clnt_Flow"] = (
                                    (serial_sensor_value["Clnt_Flow"] - 3200)
                                    / 12800
                                    * 1650
                                )
                            else:
                                print("f1 error")

                        except Exception as e:
                            print(f"check version f1: {e}")

                    if not ver_switch["flow2_switch"]:
                        try:
                            f2 = client.read_holding_registers((20480 + 6780), 1)

                            if not f2.isError():
                                serial_sensor_value["Wtr_Flow"] = f2.registers[0]
                                if serial_sensor_value["Wtr_Flow"] > 32767:
                                    serial_sensor_value["Wtr_Flow"] = (
                                        65535 - serial_sensor_value["Wtr_Flow"]
                                    )
                                if 3200 > serial_sensor_value["Wtr_Flow"] > 3040:
                                    serial_sensor_value["Wtr_Flow"] = 3200
                                sensor_raw["Wtr_Flow"] = serial_sensor_value["Wtr_Flow"]
                                check_broken("Wtr_Flow")
                                serial_sensor_value["Wtr_Flow"] = (
                                    (serial_sensor_value["Wtr_Flow"] - 3200)
                                    / 12800
                                    * 1650
                                )
                            else:
                                print("f2 error")

                        except Exception as e:
                            print(f"check version f2: {e}")

            except Exception as e:
                print(f"translate thrshd raw data error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    adjust_len = (
                        len(sensor_factor.keys()) + len(sensor_offset.keys())
                    ) * 2
                    sensor_adjs = client.read_holding_registers(
                        1400, adjust_len, unit=modbus_slave_id
                    )

                    if sensor_adjs.isError():
                        print(f"Modbus Error: {sensor_adjs}")
                    else:
                        keys_list = list(sensor_factor.keys())

                        for i in range(0, adjust_len, 4):
                            temp1 = [
                                sensor_adjs.registers[i],
                                sensor_adjs.registers[i + 1],
                            ]
                            decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                                temp1, byteorder=Endian.Big, wordorder=Endian.Little
                            )
                            decoded_value_big_endian = (
                                decoder_big_endian.decode_32bit_float()
                            )
                            sensor_factor[keys_list[i // 4]] = decoded_value_big_endian

                        for i in range(2, adjust_len, 4):
                            temp1 = [
                                sensor_adjs.registers[i],
                                sensor_adjs.registers[i + 1],
                            ]
                            decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                                temp1, byteorder=Endian.Big, wordorder=Endian.Little
                            )
                            decoded_value_big_endian = (
                                decoder_big_endian.decode_32bit_float()
                            )
                            sensor_offset[keys_list[i // 4]] = decoded_value_big_endian

                    for key in ad_sensor_value.keys():
                        all_sensors_dict[key] = (
                            ad_sensor_value[key] * sensor_factor[key]
                            + sensor_offset[key]
                        )

                    if not ver_switch["median_switch"]:
                        clnt_flow_data.append(serial_sensor_value["Clnt_Flow"])
                        if len(clnt_flow_data) > 20:
                            clnt_flow_data.popleft()
                        clnt_median = statistics.median(clnt_flow_data)
                        serial_sensor_value["Clnt_Flow"] = clnt_median

                        wrt_flow_data.append(serial_sensor_value["Wtr_Flow"])
                        if len(wrt_flow_data) > 20:
                            wrt_flow_data.popleft()
                        wrt_median = statistics.median(wrt_flow_data)
                        serial_sensor_value["Wtr_Flow"] = wrt_median

                    for key in serial_sensor_value.keys():
                        if (
                            key != "Inv1_Sp"
                            and key != "Inv2_Sp"
                            and key != "Heat_Capacity"
                        ):
                            all_sensors_dict[key] = (
                                serial_sensor_value[key] * sensor_factor[key]
                                + sensor_offset[key]
                            )

                    if not bit_output_regs["mc1"]:
                        all_sensors_dict["Inv1_Sp"] = 0
                        all_sensors_dict["Inv2_Sp"] = (
                            0.1664 * serial_sensor_value["Inv2_Sp"] + 0.0818
                        )
                    elif not bit_output_regs["mc2"]:
                        all_sensors_dict["Inv1_Sp"] = (
                            0.1664 * serial_sensor_value["Inv1_Sp"] + 0.0818
                        )
                        all_sensors_dict["Inv2_Sp"] = 0
                    else:
                        all_sensors_dict["Inv1_Sp"] = (
                            0.1664 * serial_sensor_value["Inv1_Sp"] + 0.0818
                        )
                        all_sensors_dict["Inv2_Sp"] = (
                            0.1664 * serial_sensor_value["Inv2_Sp"] + 0.0818
                        )

                    r = (
                        all_sensors_dict["Wtr_Flow"]
                        * 1.667
                        / 100
                        * 4.18
                        * (
                            all_sensors_dict["Temp_WaterOut"]
                            - all_sensors_dict["Temp_WaterIn"]
                        )
                    )

                    all_sensors_dict["Heat_Capacity"] = (
                        r * sensor_factor["Heat_Capacity"]
                        + sensor_offset["Heat_Capacity"]
                    )

            except Exception as e:
                print(f"translate adjust raw data error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_coils((8192 + 500), 1)

                    if r.bits[0]:
                        key_list = list(all_sensors_dict.keys())
                        for key in key_list:
                            if "Temp" in key:
                                all_sensors_dict[key] = (
                                    all_sensors_dict[key] * 9.0 / 5.0 + 32.0
                                )

                            if "Prsr" in key:
                                all_sensors_dict[key] = all_sensors_dict[key] * 0.145038

                            if "Flow" in key:
                                all_sensors_dict[key] = all_sensors_dict[key] * 0.2642
            except Exception as e:
                print(f"change to imperial error: {e}")

            registers = []
            for key in all_sensors_dict.keys():
                value = all_sensors_dict[key]

                word1, word2 = cvt_float_byte(value)
                registers.append(word2)
                registers.append(word1)
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(5000, registers)

            except Exception as e:
                print(f"write into thrshd error: {e}")

            check_mc()

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_coils((8192 + 520), 4, unit=modbus_slave_id)

                    keys = list(bit_output_regs.keys())
                    y = 0
                    for i in range(6, 10):
                        bit_output_regs[keys[i]] = r.bits[y]
                        y += 1
            except Exception as e:
                print(f"read ev1-ev4 error: {e}")

            water_pv_set = 0

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_coils((8192 + 617), 2, unit=modbus_slave_id)

                    bit_output_regs["mc1"] = r.bits[0]
                    bit_output_regs["mc2"] = r.bits[1]
            except Exception as e:
                print(f"read mc error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    result = client.read_holding_registers(246, 2, unit=modbus_slave_id)
                    word_regs["inv1_speed_set"] = cvt_registers_to_float(
                        result.registers[0], result.registers[1]
                    )
            except Exception as e:
                print(f"read speed1 error: {e}")

            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_discrete_inputs(12, 4, unit=modbus_slave_id)
                    level_sw["level1"] = r.bits[0]
                    level_sw["level2"] = r.bits[1]
                    level_sw["power1"] = r.bits[2]
                    level_sw["power2"] = r.bits[3]

                    r2 = client.read_discrete_inputs(18, 1, unit=modbus_slave_id)
                    level_sw["level3"] = r.bits[0]
            except Exception as e:
                print(f"read level issue:{e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    result = client.read_holding_registers(222, 2, unit=modbus_slave_id)
                    word_regs["inv2_speed_set"] = cvt_registers_to_float(
                        result.registers[0], result.registers[1]
                    )
            except Exception as e:
                print(f"read speed2 error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_holding_registers(352, 2, unit=modbus_slave_id)

                    water_pv_set = int(
                        cvt_registers_to_float(r.registers[0], r.registers[1])
                    )
            except Exception as e:
                print(f"read water pv error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_holding_registers(50, 1, unit=modbus_slave_id)

                    word_regs["pid_pump_out"] = r.registers[0]
            except Exception as e:
                print(f"read pid pump out error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    result = client.read_coils((8192 + 514), 1)

                    if result.isError():
                        print(f"Modbus Error: {result}")
                    else:
                        if not result.bits[0]:
                            mode = "stop"
                        else:
                            result = client.read_coils((8192 + 516), 1)

                            if result.bits[0]:
                                mode = "engineer"
                            else:
                                r = client.read_coils((8192 + 517), 1)

                                if r.bits[0]:
                                    mode = "inspection"
                                else:
                                    result = client.read_coils((8192 + 505), 1)

                                    if result.isError():
                                        print(f"Modbus Error: {result}")
                                    else:
                                        if not result.bits[0]:
                                            mode = "auto"
                                        else:
                                            mode = "manual"
            except Exception as e:
                print(f"read mode & control data: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_discrete_inputs(16, 2, unit=modbus_slave_id)
                    if not r.isError():
                        oc_detection["M20"] = r.bits[0]
                        oc_detection["M21"] = r.bits[1]
            except Exception as e:
                print(f"check oc detection error:{e}")

            cause_ol(oc_issue, mode)

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_holding_registers(980, 2, unit=modbus_slave_id)

                    valve_setting["t1"] = r.registers[0]
                    valve_setting["ta"] = r.registers[1]

            except Exception as e:
                print(f"read valve setting error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    if (
                        status_data["TempClntSply"] > valve_setting["t1"]
                        or status_data["TempAmbient"] > valve_setting["ta"]
                    ):
                        client.write_coils((8192 + 751), [True])
                    else:
                        client.write_coils((8192 + 751), [False])

            except Exception as e:
                print(f"control valve setting error: {e}")

            if mode in ["auto", "stop"]:
                if (
                    warning_data["alert"]["ClntFlow_Low"]
                    and warning_data["alert"]["PrsrFltIn_Low"]
                ):
                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            warning_data["error"]["Low_Coolant_Level_Warning"] = True
                            client.write_coils((8192 + 514), [False])

                    except Exception as e:
                        print(f"change to stop error:{e}")
                elif warning_data["error"]["Low_Coolant_Level_Warning"]:
                    if count_f1 > 5:
                        warning_data["error"]["Low_Coolant_Level_Warning"] = False
                        count_f1 = 0
                    else:
                        count_f1 += 1

            if reset_current_btn["status"]:
                inverter_error["Inv1_OverLoad"] = False
                inverter_error["Inv2_OverLoad"] = False
                warning_data["alert"]["AC_High"] = False
                warning_data["warning"]["AC_High"] = False
                reset_btn_false()

            if mode != "auto":
                if warning_data["alert"]["AC_High"] or (
                    oc_detection["M20"] or oc_detection["M21"]
                ):
                    oc_issue = True

                    if oc_detection["M20"]:
                        previous_inv1 = True
                        bit_output_regs["inv1_en"] = False
                        bit_output_regs["mc1"] = False
                        close_ev1()
                        close_ev2()
                        clear_p1_speed()
                    else:
                        previous_inv1 = False

                    if oc_detection["M21"]:
                        previous_inv2 = True
                        bit_output_regs["mc2"] = False
                        bit_output_regs["inv2_en"] = False
                        close_ev3()
                        close_ev4()
                        clear_p2_speed()
                    else:
                        previous_inv2 = False

                    if bit_output_regs["inv1_en"]:
                        previous_inv1 = True
                        bit_output_regs["inv1_en"] = False
                        bit_output_regs["mc1"] = False
                        close_ev1()
                        close_ev2()
                        clear_p1_speed()

                    if bit_output_regs["inv2_en"]:
                        previous_inv2 = True
                        bit_output_regs["mc2"] = False
                        bit_output_regs["inv2_en"] = False
                        close_ev3()
                        close_ev4()
                        clear_p2_speed()

                    if previous_inv1:
                        bit_output_regs["inv1_en"] = False
                        bit_output_regs["mc1"] = False
                        close_ev1()
                        close_ev2()
                        clear_p1_speed()
                        print("OC 異常 -> 關 1")

                    if previous_inv2:
                        bit_output_regs["mc2"] = False
                        bit_output_regs["inv2_en"] = False
                        close_ev3()
                        close_ev4()
                        clear_p2_speed()
                        print("OC 異常 -> 關 2")

                elif (
                    not warning_data["alert"]["AC_High"]
                    and not oc_detection["M20"]
                    and not oc_detection["M21"]
                ) and oc_issue:
                    if (
                        not inverter_error["Inv1_OverLoad"]
                        and not inverter_error["Inv2_OverLoad"]
                    ):
                        print("成功 reset")

                        reset_mc()
                        oc_issue = False
                    else:
                        if previous_inv1:
                            bit_output_regs["inv1_en"] = False
                            bit_output_regs["mc1"] = False
                            close_ev1()
                            close_ev2()
                            clear_p1_speed()
                            print("OC 異常 -> 維持關 1")

                        if previous_inv2:
                            bit_output_regs["mc2"] = False
                            bit_output_regs["inv2_en"] = False
                            close_ev3()
                            close_ev4()
                            clear_p2_speed()
                            print("OC 異常 -> 持續關 2")

                else:
                    oc_issue = False
                    previous_inv1 = False
                    previous_inv2 = False

            if mode == "manual":
                one_time_stop = False
                check_last_mode_from_inspection(mode_last)
                if inspection_data["force_change_mode"]:
                    cancel_inspection()
                reset_inspect_btn()
                change_inspect_time()
                diff = 0
                inspection_data["step"] = 1

                # print(f"列印：{word_regs}")

                if inverter_error["Inv1_OverLoad"]:
                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            client.write_registers(246, [0, 0])
                    except Exception as e:
                        print(f"p1 speed error:{e}")

                    if word_regs["inv1_speed_set"] > 0:
                        pass

                    if word_regs["inv2_speed_set"] > 0:
                        print("開二")
                        open_ev3()
                        open_ev4()
                        if bit_input_regs["EV3_Open"] and bit_input_regs["EV4_Open"]:
                            bit_output_regs["inv2_en"] = True
                            da2_ch1 = (
                                (float(word_regs["inv2_speed_set"]) - 25)
                                / 75.0
                                * 16000.0
                            )
                            set_pump2_speed(int(da2_ch1))
                    else:
                        close_ev3()
                        close_ev4()
                        bit_output_regs["inv2_en"] = False
                        set_pump2_speed(0)

                if inverter_error["Inv2_OverLoad"]:
                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            client.write_registers(222, [0, 0])
                    except Exception as e:
                        print(f"p1 speed error:{e}")

                    if word_regs["inv1_speed_set"] > 0:
                        print("開一")
                        open_ev1()
                        open_ev2()
                        if bit_input_regs["EV1_Open"] and bit_input_regs["EV2_Open"]:
                            bit_output_regs["inv1_en"] = True
                            da1_ch1 = (
                                (float(word_regs["inv1_speed_set"]) - 25)
                                / 75.0
                                * 16000.0
                            )
                            set_pump1_speed(int(da1_ch1))
                    else:
                        close_ev1()
                        close_ev2()
                        bit_output_regs["inv1_en"] = False
                        set_pump1_speed(0)

                    if word_regs["inv2_speed_set"] > 0:
                        pass

                if (
                    not inverter_error["Inv1_OverLoad"]
                    and not inverter_error["Inv2_OverLoad"]
                ):
                    if word_regs["inv1_speed_set"] == word_regs["inv2_speed_set"]:
                        pump_signial = "both"

                        if word_regs["inv1_speed_set"] > 0:
                            open_ev1()
                            open_ev2()
                            bit_output_regs["inv1_en"] = True
                            da1_ch1 = (
                                (float(word_regs["inv1_speed_set"]) - 25)
                                / 75.0
                                * 16000.0
                            )
                            set_pump1_speed(int(da1_ch1))
                        else:
                            close_ev1()
                            close_ev2()
                            bit_output_regs["inv1_en"] = False
                            set_pump1_speed(0)

                        if word_regs["inv2_speed_set"] > 0:
                            open_ev3()
                            open_ev4()

                            bit_output_regs["inv2_en"] = True
                            da2_ch1 = (
                                (float(word_regs["inv2_speed_set"]) - 25)
                                / 75.0
                                * 16000.0
                            )
                            set_pump2_speed(int(da2_ch1))
                        else:
                            close_ev3()
                            close_ev4()
                            bit_output_regs["inv2_en"] = False
                            set_pump2_speed(0)

                        if (
                            word_regs["inv1_speed_set"] == 0
                            and word_regs["inv2_speed_set"] == 0
                        ):
                            close_ev1()
                            close_ev2()
                            close_ev3()
                            close_ev4()
                            bit_output_regs["inv1_en"] = False
                            bit_output_regs["inv2_en"] = False
                            set_pump1_speed(0)
                            set_pump2_speed(0)

                    else:
                        if word_regs["inv1_speed_set"] > 0:
                            open_ev1()
                            open_ev2()
                            close_ev3()
                            close_ev4()

                            bit_output_regs["inv1_en"] = False
                            bit_output_regs["inv2_en"] = False

                            if (
                                bit_input_regs["EV1_Open"]
                                and bit_input_regs["EV2_Open"]
                                and bit_input_regs["EV3_Close"]
                                and bit_input_regs["EV4_Close"]
                            ):
                                bit_output_regs["inv1_en"] = True
                                da1_ch1 = (
                                    (float(word_regs["inv1_speed_set"]) - 25)
                                    / 75.0
                                    * 16000.0
                                )
                                set_pump1_speed(int(da1_ch1))

                                if pump_signial == "both":
                                    if mode_last == "auto":
                                        auto_flag = True

                                    if auto_flag:
                                        set_pump2_speed(int(da1_ch1))

                                    if (
                                        bit_input_regs["EV3_Close"]
                                        and bit_input_regs["EV4_Close"]
                                    ):
                                        bit_output_regs["inv2_en"] = False
                                        set_pump2_speed(0)
                                        pump_signial = "single"
                                        auto_flag = False
                                else:
                                    bit_output_regs["inv2_en"] = False
                                    set_pump2_speed(0)
                                    pump_signial = "single"

                        elif (
                            word_regs["inv1_speed_set"] <= 0
                            and word_regs["inv2_speed_set"] > 0
                        ):
                            close_ev1()
                            close_ev2()
                            open_ev3()
                            open_ev4()

                            bit_output_regs["inv1_en"] = False
                            bit_output_regs["inv2_en"] = False

                            if (
                                bit_input_regs["EV1_Close"]
                                and bit_input_regs["EV2_Close"]
                                and bit_input_regs["EV3_Open"]
                                and bit_input_regs["EV4_Open"]
                            ):
                                bit_output_regs["inv2_en"] = True
                                da2_ch1 = (
                                    (float(word_regs["inv2_speed_set"]) - 25)
                                    / 75.0
                                    * 16000.0
                                )
                                set_pump2_speed(int(da2_ch1))

                                if pump_signial == "both":
                                    if mode_last == "auto":
                                        auto_flag = True

                                    if auto_flag:
                                        set_pump1_speed(int(da2_ch1))

                                    if (
                                        bit_input_regs["EV1_Close"]
                                        and bit_input_regs["EV2_Close"]
                                    ):
                                        bit_output_regs["inv1_en"] = False
                                        set_pump1_speed(0)
                                        pump_signial = "single"
                                else:
                                    bit_output_regs["inv1_en"] = False
                                    set_pump1_speed(0)
                                    pump_signial = "single"

                        else:
                            close_ev1()
                            close_ev2()
                            close_ev3()
                            close_ev4()
                            bit_output_regs["inv1_en"] = False
                            bit_output_regs["inv2_en"] = False
                            set_pump1_speed(0)
                            set_pump2_speed(0)

                set_water_pv(water_pv_set)
                mode_last = mode
                change_back_mode = mode
            elif mode == "auto":
                one_time_stop = False
                check_last_mode_from_inspection(mode_last)
                if inspection_data["force_change_mode"]:
                    cancel_inspection()
                check_both_overload()
                diff = 0
                change_inspect_time()
                reset_inspect_btn()
                inspection_data["step"] = 1
                pump_signial = "both"
                if not oc_issue:
                    open_ev1()
                    open_ev2()
                    open_ev3()
                    open_ev4()

                    if bit_output_regs["inv1_en"] or bit_output_regs["inv2_en"]:
                        bit_output_regs["inv1_en"] = True
                        bit_output_regs["inv2_en"] = True
                        set_pump1_speed(word_regs["pid_pump_out"])
                        set_pump2_speed(word_regs["pid_pump_out"])
                    else:
                        if not bit_output_regs["mc1"]:
                            if (
                                bit_input_regs["EV3_Open"]
                                and bit_input_regs["EV4_Open"]
                            ):
                                bit_output_regs["inv2_en"] = True
                                set_pump2_speed(word_regs["pid_pump_out"])

                        if not bit_output_regs["mc2"]:
                            if (
                                bit_input_regs["EV1_Open"]
                                and bit_input_regs["EV2_Open"]
                            ):
                                bit_output_regs["inv1_en"] = True
                                set_pump1_speed(word_regs["pid_pump_out"])

                        if bit_output_regs["mc1"] and bit_output_regs["mc2"]:
                            if (
                                bit_input_regs["EV1_Open"]
                                and bit_input_regs["EV2_Open"]
                                and bit_input_regs["EV3_Open"]
                                and bit_input_regs["EV4_Open"]
                            ):
                                bit_output_regs["inv1_en"] = True
                                bit_output_regs["inv2_en"] = True
                                set_pump1_speed(word_regs["pid_pump_out"])
                                set_pump2_speed(word_regs["pid_pump_out"])
                else:
                    print("正在 OC 中")

                if (
                    warning_data["alert"]["AC_High"]
                    or oc_detection["M20"]
                    or oc_detection["M21"]
                ):
                    oc_issue = True

                    if warning_data["alert"]["AC_High"]:
                        bit_output_regs["mc1"] = False
                        bit_output_regs["mc2"] = False
                        print("OC 異常 -> AUTO 全關")

                    if oc_detection["M20"]:
                        bit_output_regs["mc1"] = False
                        print("OC 異常 -> AUTO 關一")

                    if oc_detection["M21"]:
                        bit_output_regs["mc2"] = False
                        print("OC 異常 -> AUTO 關二")

                elif (
                    not warning_data["alert"]["AC_High"]
                    and not oc_detection["M20"]
                    and not oc_detection["M21"]
                ) and oc_issue:
                    if (
                        not inverter_error["Inv1_OverLoad"]
                        and not inverter_error["Inv2_OverLoad"]
                    ):
                        print("成功 reset")

                        reset_mc()
                        oc_issue = False
                    else:
                        if oc_detection["M20"]:
                            bit_output_regs["mc1"] = False
                            print("OC 異常 -> AUTO 持續觀一")

                        if oc_detection["M21"]:
                            bit_output_regs["mc2"] = False
                            print("OC 異常 -> AUTO 持續觀二")

                        if not oc_detection["M20"] and not oc_detection["M21"]:
                            bit_output_regs["mc1"] = False
                            bit_output_regs["mc2"] = False
                            print("OC 異常 -> AUTO 持續全關")

                else:
                    oc_issue = False

                change_back_mode = mode
                mode_last = "auto"
            elif mode == "stop":
                pump_signial = "single"
                check_last_mode_from_inspection(mode_last)
                if inspection_data["force_change_mode"]:
                    cancel_inspection()
                diff = 0
                change_inspect_time()
                reset_inspect_btn()
                inspection_data["step"] = 1
                bit_output_regs["inv1_en"] = False
                bit_output_regs["inv2_en"] = False
                close_ev1()
                close_ev2()
                close_ev3()
                close_ev4()

                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        client.write_registers(246, [0, 0])
                except Exception as e:
                    print(f"pump speed setting error:{e}")

                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        client.write_registers(222, [0, 0])
                except Exception as e:
                    print(f"pump speed setting error:{e}")

                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        low_auto_set = client.read_holding_registers(974, 1)
                        r = client.read_coils((8192 + 515), 1, unit=modbus_slave_id)
                        if r.bits[0]:
                            set_water_pv(low_auto_set.registers[0])
                except Exception as e:
                    print(f"read ev error:{e}")
                mode_last = mode
                change_back_mode = mode
            elif mode == "engineer":
                one_time_stop = False
                check_last_mode_from_inspection(mode_last)
                if inspection_data["force_change_mode"]:
                    cancel_inspection()
                reset_inspect_btn()
                change_inspect_time()
                diff = 0
                inspection_data["step"] = 1

                if inverter_error["Inv1_OverLoad"]:
                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            client.write_registers(246, [0, 0])
                    except Exception as e:
                        print(f"p1 speed error:{e}")

                    if (
                        word_regs["inv1_speed_set"] == 0
                        and word_regs["inv2_speed_set"] == 0
                    ):
                        close_ev1()
                        close_ev2()
                        bit_output_regs["inv1_en"] = False
                        bit_output_regs["inv2_en"] = False
                        set_pump1_speed(0)
                        set_pump2_speed(0)
                    else:
                        if word_regs["inv1_speed_set"] > 0:
                            pass

                        if word_regs["inv2_speed_set"] > 0:
                            print("開二")
                            open_ev3()
                            open_ev4()
                            if (
                                bit_input_regs["EV3_Open"]
                                and bit_input_regs["EV4_Open"]
                            ):
                                bit_output_regs["inv2_en"] = True
                                da2_ch1 = (
                                    (float(word_regs["inv2_speed_set"]) - 25)
                                    / 75.0
                                    * 16000.0
                                )
                                set_pump2_speed(int(da2_ch1))
                        else:
                            close_ev3()
                            close_ev4()
                            bit_output_regs["inv2_en"] = False
                            set_pump2_speed(0)

                if inverter_error["Inv2_OverLoad"]:
                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            client.write_registers(222, [0, 0])
                    except Exception as e:
                        print(f"p1 speed error:{e}")

                    if (
                        word_regs["inv1_speed_set"] == 0
                        and word_regs["inv2_speed_set"] == 0
                    ):
                        close_ev3()
                        close_ev4()
                        bit_output_regs["inv1_en"] = False
                        bit_output_regs["inv2_en"] = False
                        set_pump1_speed(0)
                        set_pump2_speed(0)
                    else:
                        if word_regs["inv1_speed_set"] > 0:
                            print("開一")
                            open_ev1()
                            open_ev2()
                            if (
                                bit_input_regs["EV1_Open"]
                                and bit_input_regs["EV2_Open"]
                            ):
                                bit_output_regs["inv1_en"] = True
                                da1_ch1 = (
                                    (float(word_regs["inv1_speed_set"]) - 25)
                                    / 75.0
                                    * 16000.0
                                )
                                set_pump1_speed(int(da1_ch1))
                        else:
                            close_ev1()
                            close_ev2()
                            bit_output_regs["inv1_en"] = False
                            set_pump1_speed(0)

                        if word_regs["inv2_speed_set"] > 0:
                            pass

                if (
                    not inverter_error["Inv1_OverLoad"]
                    and not inverter_error["Inv2_OverLoad"]
                ):
                    if (
                        word_regs["inv1_speed_set"] == 0
                        and word_regs["inv2_speed_set"] == 0
                    ):
                        bit_output_regs["inv1_en"] = False
                        bit_output_regs["inv2_en"] = False
                        set_pump1_speed(0)
                        set_pump2_speed(0)
                    else:
                        if word_regs["inv1_speed_set"] == word_regs["inv2_speed_set"]:
                            pump_signial = "both"
                            if word_regs["inv1_speed_set"] > 0:
                                open_ev1()
                                open_ev2()
                                bit_output_regs["inv1_en"] = True
                                da1_ch1 = (
                                    (float(word_regs["inv1_speed_set"]) - 25)
                                    / 75.0
                                    * 16000.0
                                )
                                set_pump1_speed(int(da1_ch1))
                            else:
                                close_ev1()
                                close_ev2()
                                bit_output_regs["inv1_en"] = False
                                set_pump1_speed(0)

                            if word_regs["inv2_speed_set"] > 0:
                                open_ev3()
                                open_ev4()
                                bit_output_regs["inv2_en"] = True
                                da2_ch1 = (
                                    (float(word_regs["inv2_speed_set"]) - 25)
                                    / 75.0
                                    * 16000.0
                                )
                                set_pump2_speed(int(da2_ch1))
                            else:
                                close_ev3()
                                close_ev4()
                                bit_output_regs["inv2_en"] = False
                                set_pump2_speed(0)

                        else:
                            if word_regs["inv1_speed_set"] > 0:
                                open_ev1()
                                open_ev2()
                                close_ev3()
                                close_ev4()
                                bit_output_regs["inv1_en"] = False
                                bit_output_regs["inv2_en"] = False

                                if (
                                    bit_input_regs["EV1_Open"]
                                    and bit_input_regs["EV2_Open"]
                                    and bit_input_regs["EV3_Close"]
                                    and bit_input_regs["EV4_Close"]
                                ):
                                    bit_output_regs["inv1_en"] = True

                                    da1_ch1 = (
                                        (float(word_regs["inv1_speed_set"]) - 25)
                                        / 75.0
                                        * 16000.0
                                    )
                                    set_pump1_speed(int(da1_ch1))

                                    if pump_signial == "both":
                                        if mode_last == "auto":
                                            auto_flag = True

                                        if auto_flag:
                                            set_pump2_speed(int(da1_ch1))

                                        if (
                                            bit_input_regs["EV3_Close"]
                                            and bit_input_regs["EV4_Close"]
                                        ):
                                            bit_output_regs["inv2_en"] = False
                                            set_pump2_speed(0)
                                            pump_signial = "single"
                                    else:
                                        bit_output_regs["inv2_en"] = False
                                        set_pump2_speed(0)
                                        pump_signial = "single"

                            elif (
                                word_regs["inv1_speed_set"] <= 0
                                and word_regs["inv2_speed_set"] > 0
                            ):
                                close_ev1()
                                close_ev2()
                                open_ev3()
                                open_ev4()

                                bit_output_regs["inv1_en"] = False
                                bit_output_regs["inv2_en"] = False

                                if (
                                    bit_input_regs["EV1_Close"]
                                    and bit_input_regs["EV2_Close"]
                                    and bit_input_regs["EV3_Open"]
                                    and bit_input_regs["EV4_Open"]
                                ):
                                    bit_output_regs["inv2_en"] = True
                                    da2_ch1 = (
                                        (float(word_regs["inv2_speed_set"]) - 25)
                                        / 75
                                        * 16000
                                    )
                                    set_pump2_speed(int(da2_ch1))

                                    if pump_signial == "both":
                                        if mode_last == "auto":
                                            auto_flag = True

                                        if auto_flag:
                                            set_pump1_speed(int(da2_ch1))

                                        if (
                                            bit_input_regs["EV1_Close"]
                                            and bit_input_regs["EV2_Close"]
                                        ):
                                            bit_output_regs["inv1_en"] = False
                                            set_pump1_speed(0)
                                            pump_signial = "single"
                                    else:
                                        bit_output_regs["inv1_en"] = False
                                        set_pump1_speed(0)
                                        pump_signial = "single"
                            else:
                                bit_output_regs["inv1_en"] = False
                                bit_output_regs["inv2_en"] = False
                                set_pump1_speed(0)
                                set_pump2_speed(0)

                set_water_pv(water_pv_set)
                mode_last = mode
                change_back_mode = mode
            elif mode == "inspection":
                one_time_stop = False
                ev_open_time = 30
                read_flow_time = 15
                water_open_time = 30
                pump_open_time = 10
                comm_check_time = 18
                mode_last = mode
                global count
                change_inspect_time()

                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        r = client.read_holding_registers(740, 3)
                        ev_open_time = r.registers[0]
                        water_open_time = r.registers[1]
                        pump_open_time = r.registers[2]
                except Exception as e:
                    print(f"read inspection time error:{e}")

                if inspection_data["start_btn"] == 2:
                    print("被 cancel")

                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            progress = [
                                1 if value == 4 else value
                                for value in inspection_data["progress"].values()
                            ]
                            client.write_registers(800, progress)
                    except Exception as e:
                        print(f"result write-in:{e}")

                    for key, status in inspection_data["progress"].items():
                        if status == 1:
                            inspection_data["result"][key] = False

                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            result = [
                                1 if value else 0
                                for value in inspection_data["result"].values()
                            ]
                            client.write_registers(750, result)
                    except Exception as e:
                        print(f"result write-in:{e}")

                    reset_inspect_btn()
                    go_back_to_last_mode(change_back_mode, water_pv_set)

                    mode_last = mode

                    inspection_data["step"] = 1
                    inspection_data["start_time"] = 0
                    inspection_data["mid_time"] = 0
                    inspection_data["end_time"] = 0
                    diff = 0
                    print("結束")

                elif inspection_data["start_btn"] == 1:
                    try:
                        if inspection_data["step"] == 1:
                            print("1. 全部重置")
                            journal_logger.info("1. 全部重置")

                            inspection_data["start_time"] = time.time()

                            inspection_data["prev"]["inv1"] = bit_output_regs["inv1_en"]
                            inspection_data["prev"]["inv2"] = bit_output_regs["inv2_en"]

                            for key in inspection_data["result"]:
                                if key == "f1" or "_com" in key:
                                    inspection_data["result"][key] = []
                                else:
                                    inspection_data["result"][key] = False

                            for key in inspection_data["progress"]:
                                change_progress(key, "cancel")

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    client.write_registers(
                                        800, [3] * len(inspection_data["progress"])
                                    )
                            except Exception as e:
                                print(f"reset inspection error:{e}")

                            bit_output_regs["inv1_en"] = False
                            bit_output_regs["inv2_en"] = False

                            count += 1

                            if count > 3:
                                inspection_data["step"] += 1

                        if inspection_data["step"] == 2:
                            print(f"2. 開一二，關三四：等 {ev_open_time} 秒")
                            journal_logger.info(
                                f"2. 開一二，關三四：等 {ev_open_time} 秒"
                            )

                            open_ev1()
                            open_ev2()
                            close_ev3()
                            close_ev4()

                            change_progress("ev1_open", "standby")
                            change_progress("ev2_open", "standby")
                            change_progress("ev3_close", "standby")
                            change_progress("ev4_close", "standby")
                            change_progress("p1_speed", "standby")

                            bit_output_regs["inv2_en"] = False

                            inspection_data["end_time"] = time.time()
                            diff = (
                                inspection_data["end_time"]
                                - inspection_data["start_time"]
                            )
                            if diff >= ev_open_time:
                                inspection_data["step"] += 1
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]

                            send_progress(0, "ev1_open")
                            send_progress(1, "ev2_open")
                            send_progress(6, "ev3_close")
                            send_progress(7, "ev4_close")
                            send_progress(8, "p1_speed")

                        if inspection_data["step"] == 3:
                            print(f"3. 測 EV，開 INV1：等 {pump_open_time} 秒")
                            journal_logger.info(
                                f"3. 測 EV，開 INV1：等 {pump_open_time} 秒"
                            )

                            open_ev1()
                            open_ev2()
                            close_ev3()
                            close_ev4()

                            change_progress("ev1_open", "finish")
                            change_progress("ev2_open", "finish")
                            change_progress("ev3_close", "finish")
                            change_progress("ev4_close", "finish")

                            inspect_ev("EV1_Open", "EV2_Open", "EV3_Close", "EV4_Close")

                            inspection_data["end_time"] = time.time()
                            diff = (
                                inspection_data["end_time"]
                                - inspection_data["mid_time"]
                            )

                            if (
                                inspection_data["result"]["ev1_open"]
                                and inspection_data["result"]["ev2_open"]
                            ):
                                inspection_data["step"] = 5
                                bit_output_regs["inv1_en"] = False
                                inspection_data["result"]["p1_speed"] = True
                                change_progress("p1_speed", "skip")
                                send_all(8, "p1_speed")
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]
                                print("跳到步驟五")

                            if inspection_data["step"] == 3:
                                bit_output_regs["inv1_en"] = True
                                p1_s = (float(50) - 25) / 75.0 * 16000.0
                                set_pump1_speed(int(p1_s))

                            p1_error_box.append(warning_data["error"]["Inv1_Error"])
                            p1_error_box.append(warning_data["alert"]["AC_High"])
                            p1_error_box.append(oc_detection["M20"])

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    r = client.read_holding_registers(5054, 2)
                                    pump1_speed = cvt_registers_to_float(
                                        r.registers[0], r.registers[1]
                                    )
                                    p1_data.append(pump1_speed)
                            except Exception as e:
                                print(f"p1 error: {e}")

                            if diff >= pump_open_time:
                                inspection_data["step"] += 1
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]

                            send_all(0, "ev1_open")
                            send_all(1, "ev2_open")
                            send_all(6, "ev3_close")
                            send_all(7, "ev4_close")

                        if inspection_data["step"] == 4:
                            print("4. 測 Pump1")
                            journal_logger.info("4. 測 Pump1")

                            if any(p1_error_box):
                                inspection_data["step"] = 5
                                bit_output_regs["inv1_en"] = False
                                change_progress("p1_speed", "skip")
                                inspection_data["result"]["p1_speed"] = True
                                send_all(8, "p1_speed")
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]
                            else:
                                bit_output_regs["inv1_en"] = True

                                try:
                                    max_p1 = max(p1_data)

                                    inspection_data["result"]["p1_speed"] = not (
                                        55 > max_p1 > 45
                                    )

                                    print(f"pump1 結果：{max_p1}")

                                    write_measured_data(1, max_p1)
                                    change_progress("p1_speed", "finish")

                                    inspection_data["step"] += 1
                                    inspection_data["end_time"] = time.time()
                                    inspection_data["mid_time"] = inspection_data[
                                        "end_time"
                                    ]
                                except Exception as e:
                                    print(f"pump1 speed read error:{e}")

                                send_all(8, "p1_speed")

                        if inspection_data["step"] == 5:
                            print("5. 測 f1")
                            journal_logger.info("5. 測 f1")

                            if (
                                warning_data["alert"]["ClntFlow_Low"]
                                or warning_data["error"][
                                    "coolant_flow_rate_communication"
                                ]
                            ):
                                inspection_data["result"]["f1"].append(True)
                            else:
                                inspection_data["result"]["f1"].append(False)

                            f1_data.append(status_data["ClntFlow"])
                            change_progress("f1", "standby")

                            bit_output_regs["inv1_en"] = False

                            send_progress(11, "f1")

                            inspection_data["end_time"] = time.time()
                            diff = (
                                inspection_data["end_time"]
                                - inspection_data["mid_time"]
                            )
                            if diff > read_flow_time:
                                inspection_data["step"] += 1
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]

                        if inspection_data["step"] == 6:
                            print(f"6. 開 water：等 {water_open_time} 秒")
                            journal_logger.info(f"6. 開 water：等 {water_open_time} 秒")

                            max_f1 = max(f1_data)

                            if warning_data["error"]["coolant_flow_rate_communication"]:
                                max_f1 = 0

                            write_measured_data(7, max_f1)
                            print(f"F1 結果：{max_f1}")

                            set_water_pv(50)

                            change_progress("water_pv", "standby")
                            change_progress("f2", "standby")

                            send_progress(10, "water_pv")
                            send_progress(12, "f2")

                            inspection_data["end_time"] = time.time()
                            diff = (
                                inspection_data["end_time"]
                                - inspection_data["mid_time"]
                            )
                            if diff >= water_open_time:
                                inspection_data["step"] += 1
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]

                        if inspection_data["step"] == 7:
                            print("7. 測 water pv＋f2")
                            journal_logger.info("7. 測 water pv＋f2")

                            f1_data = []

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    r = client.read_holding_registers(5034, 2)

                                    water = cvt_registers_to_float(
                                        r.registers[0], r.registers[1]
                                    )
                                    inspection_data["result"]["water_pv"] = not (
                                        55 > water > 45
                                    )

                                print(f"water 結果：{water}")
                                change_progress("water_pv", "finish")

                                write_measured_data(5, water)

                                if (
                                    warning_data["alert"]["WaterFlow_Low"]
                                    or warning_data["error"][
                                        "facility_water_flow_rate_communication"
                                    ]
                                ):
                                    inspection_data["result"]["f2"] = True

                                change_progress("f2", "finish")

                                f2 = status_data["WaterFlow"]

                                if warning_data["error"][
                                    "facility_water_flow_rate_communication"
                                ]:
                                    f2 = 0

                                write_measured_data(9, f2)

                                inspection_data["step"] += 0.5

                            except Exception as e:
                                print(f"read water pv error:{e}")

                            send_all(10, "water_pv")
                            send_all(12, "f2")

                        if inspection_data["step"] == 7.5:
                            print(f"7.5. 開 Pump2：等 {ev_open_time} 秒")
                            journal_logger.info(f"7.5. 開 Pump2：等 {ev_open_time} 秒")

                            close_ev1()
                            close_ev2()
                            open_ev3()
                            open_ev4()

                            change_progress("ev1_close", "standby")
                            change_progress("ev2_close", "standby")
                            change_progress("ev3_open", "standby")
                            change_progress("ev4_open", "standby")
                            change_progress("p2_speed", "standby")

                            inspection_data["end_time"] = time.time()
                            diff = (
                                inspection_data["end_time"]
                                - inspection_data["mid_time"]
                            )
                            if diff > ev_open_time:
                                inspection_data["step"] += 0.5
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]

                            send_progress(4, "ev1_close")
                            send_progress(5, "ev2_close")
                            send_progress(2, "ev3_open")
                            send_progress(3, "ev4_open")
                            send_progress(9, "p2_speed")

                        if inspection_data["step"] == 8:
                            print(f"8. 測 EV，開 INV2：等 {pump_open_time} 秒")
                            journal_logger.info(
                                f"8. 測 EV，開 INV2：等 {pump_open_time} 秒"
                            )

                            close_ev1()
                            close_ev2()
                            open_ev3()
                            open_ev4()

                            change_progress("ev1_close", "finish")
                            change_progress("ev2_close", "finish")
                            change_progress("ev3_open", "finish")
                            change_progress("ev4_open", "finish")

                            inspect_ev("EV1_Close", "EV2_Close", "EV3_Open", "EV4_Open")

                            inspection_data["end_time"] = time.time()
                            diff = (
                                inspection_data["end_time"]
                                - inspection_data["mid_time"]
                            )

                            if (
                                inspection_data["result"]["ev3_open"]
                                and inspection_data["result"]["ev4_open"]
                            ):
                                inspection_data["step"] = 9.5
                                bit_output_regs["inv2_en"] = False
                                inspection_data["result"]["p2_speed"] = True
                                inspection_data["result"]["f1"] = True
                                change_progress("p2_speed", "skip")
                                change_progress("f1", "finish")
                                send_all(9, "p2_speed")
                                send_all(11, "f1")

                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]

                            if inspection_data["step"] == 8:
                                bit_output_regs["inv2_en"] = True
                                p2_s = (float(50) - 25) / 75.0 * 16000.0
                                set_pump2_speed(int(p2_s))

                            p2_error_box.append(warning_data["error"]["Inv2_Error"])
                            p2_error_box.append(warning_data["alert"]["AC_High"])
                            p2_error_box.append(oc_detection["M21"])

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    r = client.read_holding_registers(5056, 2)

                                    pump2_speed = cvt_registers_to_float(
                                        r.registers[0], r.registers[1]
                                    )
                                    p2_data.append(pump2_speed)

                            except Exception as e:
                                print(f"p2 error: {e}")

                            if diff > pump_open_time:
                                inspection_data["step"] += 1
                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]

                            send_all(4, "ev1_close")
                            send_all(5, "ev2_close")
                            send_all(2, "ev3_open")
                            send_all(3, "ev4_open")

                        if inspection_data["step"] == 9:
                            print("9. 測 P2＋F1")
                            journal_logger.info("9. 測 P2＋F1")

                            if any(p2_error_box):
                                inspection_data["step"] = 9.5
                                bit_output_regs["inv2_en"] = False
                                inspection_data["result"]["p2_speed"] = True
                                inspection_data["result"]["f1"] = True
                                change_progress("p2_speed", "skip")
                                change_progress("f1", "finish")
                                send_all(9, "p2_speed")
                                send_all(11, "f1")

                                inspection_data["mid_time"] = inspection_data[
                                    "end_time"
                                ]
                            else:
                                bit_output_regs["inv2_en"] = True

                                try:
                                    p2_max = max(p2_data)
                                    inspection_data["result"]["p2_speed"] = not (
                                        55 > p2_max > 45
                                    )
                                    print(f"pump2 結果：{p2_max}")

                                    change_progress("p2_speed", "finish")
                                    write_measured_data(3, p2_max)

                                    if (
                                        warning_data["alert"]["ClntFlow_Low"]
                                        or warning_data["error"][
                                            "coolant_flow_rate_communication"
                                        ]
                                    ):
                                        inspection_data["result"]["f1"].append(True)
                                    else:
                                        inspection_data["result"]["f1"].append(False)

                                    inspection_data["result"]["f1"] = all(
                                        inspection_data["result"]["f1"]
                                    )
                                    inspection_data["progress"]["f1"] = 2

                                    inspection_data["step"] += 0.5
                                    inspection_data["end_time"] = time.time()
                                    inspection_data["mid_time"] = inspection_data[
                                        "end_time"
                                    ]
                                except Exception as e:
                                    print(f"pump2 speed read error:{e}")
                                send_all(9, "p2_speed")
                                send_all(11, "f1")

                            for level in level_sw:
                                change_progress(level, "standby")

                        if inspection_data["step"] == 9.5:
                            print("9.5. 測 liquid & power")
                            journal_logger.info("9.5. 測 liquid & power")
                            k = 0
                            for level in level_sw:
                                inspection_data["result"][level] = not level_sw[level]

                                change_progress(level, "finish")
                                send_all(42 + k, level)
                                k += 1

                            x = 0
                            for key in inspection_data["result"]:
                                if "Temp_" in key or "Prsr_" in key or "Flow_" in key:
                                    change_progress(key, "standby")
                                    send_progress(13 + x, key)
                                    x += 1

                            inspection_data["step"] += 0.5

                        if inspection_data["step"] == 10:
                            print("10. 測 broken")
                            journal_logger.info("10. 測 broken")

                            i = 0
                            j = 0
                            z = 0
                            for key in inspection_data["result"]:
                                if "Temp_" in key:
                                    raw_key = key.replace("_broken", "")
                                    if (
                                        sensor_raw[raw_key] > 1000
                                        or sensor_raw[raw_key] < -100
                                    ):
                                        inspection_data["result"][key] = True
                                    else:
                                        inspection_data["result"][key] = False

                                    change_progress(key, "finish")

                                    for (
                                        register,
                                        status_key,
                                    ) in measured_data_mapping.items():
                                        write_measured_data(
                                            register, status_data[status_key]
                                        )

                                    send_all(13 + i, key)
                                    i += 1

                                if "Prsr_" in key:
                                    raw_key = key.replace("_broken", "")
                                    if sensor_raw[raw_key] < 1200:
                                        inspection_data["result"][key] = True
                                    else:
                                        inspection_data["result"][key] = False
                                    change_progress(key, "finish")
                                    send_all(18 + j, key)
                                    j += 1

                                if "Flow_" in key:
                                    raw_key = key.replace("_broken", "")
                                    if (
                                        sensor_raw[raw_key] < 1000
                                        or sensor_raw[raw_key] > 20000
                                    ):
                                        inspection_data["result"][key] = True
                                    else:
                                        inspection_data["result"][key] = False
                                    inspection_data["progress"][key] = 2
                                    change_progress(key, "finish")
                                    send_all(30 + z, key)
                                    z += 1

                            n = 0

                            for key, value in raw_485_communication.items():
                                key_name = f"{key}_com"
                                change_progress(key_name, "standby")
                                send_progress(32 + n, key_name)
                                n += 1

                            inspection_data["step"] += 1
                            inspection_data["end_time"] = time.time()
                            inspection_data["mid_time"] = inspection_data["end_time"]

                        if inspection_data["step"] == 11:
                            print(f"11. 測 comm {comm_check_time} 秒")
                            journal_logger.info(f"11. 測 comm {comm_check_time} 秒")

                            inspection_data["end_time"] = time.time()
                            diff = (
                                inspection_data["end_time"]
                                - inspection_data["mid_time"]
                            )

                            if int(diff) % 4 == 0 and diff <= comm_check_time:
                                for key, value in raw_485_communication.items():
                                    key_name = f"{key}_com"
                                    inspection_data["result"][key_name].append(
                                        not value
                                    )

                            if int(diff) > comm_check_time:
                                k = 0
                                inspection_data["step"] = 12
                                for key, value in raw_485_communication.items():
                                    key_name = f"{key}_com"
                                    inspection_data["result"][key_name] = not any(
                                        inspection_data["result"][key_name]
                                    )
                                    change_progress(key_name, "finish")
                                    send_all(32 + k, key_name)
                                    k += 1

                        if inspection_data["step"] == 12:
                            print("12. 最後收尾")
                            journal_logger.info("12. 最後收尾")

                            p1_data = []
                            f1_data = []
                            p2_data = []
                            p1_error_box = []
                            p2_error_box = []

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    client.write_registers(
                                        800,
                                        list(inspection_data["progress"].values()),
                                    )

                            except Exception as e:
                                print(f"result write-in:{e}")

                            for key, status in inspection_data["progress"].items():
                                if status == 1:
                                    inspection_data["result"][key] = False

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    value_list_result = [
                                        1 if value else 0
                                        for value in inspection_data["result"].values()
                                    ]
                                    client.write_registers(750, value_list_result)

                            except Exception as e:
                                print(f"result write-in:{e}")

                            reset_inspect_btn()

                            go_back_to_last_mode(change_back_mode, water_pv_set)
                            mode_last = mode

                            inspection_data["step"] = 1
                            inspection_data["start_time"] = 0
                            inspection_data["mid_time"] = 0
                            inspection_data["end_time"] = 0
                            diff = 0

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    client.write_register(973, 2)
                            except Exception as e:
                                print(f"reset error: {e}")

                            print("結束囉")

                    except Exception as e:
                        print(f"inspect error:{e}")

            if (
                mode == "engineer"
                and word_regs["inv1_speed_set"] == 0
                and word_regs["inv2_speed_set"] == 0
            ):
                pass
            else:
                if not bit_output_regs["mc1"]:
                    close_ev1()
                    close_ev2()
                    bit_output_regs["inv1_en"] = False

                if not bit_output_regs["mc2"]:
                    close_ev3()
                    close_ev4()
                    bit_output_regs["inv2_en"] = False

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_coils((8192 + 700), [oc_issue, f1_issue])
            except Exception as e:
                print(f"write oc issue error: {e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    if sensor_factor["Temp_ClntSplySpr"] == 0:
                        client.write_coils((8192 + 2002), [False, False])
                        client.write_coils((8192 + 2073), [False])

                    if sensor_factor["Prsr_ClntSplySpr"] == 0:
                        client.write_coils((8192 + 2012), [False, False])
                        client.write_coils((8192 + 2078), [False])

                    if sensor_factor["Prsr_ClntRtnSpr"] == 0:
                        client.write_coils((8192 + 2016), [False, False])
                        client.write_coils((8192 + 2082), [False])
            except Exception as e:
                print(f"t1sp p1sp trap: {e}")

            if warning_data["error"]["Inv1_Error"]:
                bit_output_regs["inv1_en"] = False
                bit_output_regs["EV1"] = False
                bit_output_regs["EV2"] = False

            if warning_data["error"]["Inv2_Error"]:
                bit_output_regs["inv2_en"] = False
                bit_output_regs["EV3"] = False
                bit_output_regs["EV4"] = False

            try:
                value = list(bit_output_regs.values())
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_coils(0, value)

            except Exception as e:
                print(f"set output data error: {e}")

            if bit_output_regs["inv1_en"]:
                pump1_run_current_time = time.time()

                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        r = client.read_holding_registers(270, 4, unit=modbus_slave_id)
                        rt1_min = read_split_register(r.registers, 0)
                        rt1_hr = read_split_register(r.registers, 2)
                        dword_regs["pump1_run_time_min"] = rt1_min
                        dword_regs["pump1_run_time_hr"] = rt1_hr

                except Exception as e:
                    print(f"read pump1 runtime error: {e}")

                if pump1_run_current_time - pump1_run_last_min >= 60:
                    dword_regs["pump1_run_time_min"] += 1
                    dword_regs["pump1_run_time_hr"] = int(
                        dword_regs["pump1_run_time_min"] / 60
                    )
                    pump1_run_last_min = pump1_run_current_time

                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            rt1_min = split_double([dword_regs["pump1_run_time_min"]])
                            rt1_hr = split_double([dword_regs["pump1_run_time_hr"]])

                            client.write_registers(270, rt1_min)
                            client.write_registers(272, rt1_hr)

                            client.write_registers(200, rt1_hr)

                    except Exception as e:
                        print(f"read pump1 runtime error: {e}")
            else:
                pump1_run_last_min = time.time()

            if bit_output_regs["inv2_en"]:
                pump2_run_current_time = time.time()
                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        r = client.read_holding_registers(274, 4, unit=modbus_slave_id)

                        rt2_min = read_split_register(r.registers, 0)
                        rt2_hr = read_split_register(r.registers, 2)

                        dword_regs["pump2_run_time_min"] = rt2_min
                        dword_regs["pump2_run_time_hr"] = rt2_hr
                except Exception as e:
                    print(f"read pump2 runtime error: {e}")

                if pump2_run_current_time - pump2_run_last_min >= 60:
                    dword_regs["pump2_run_time_min"] += 1
                    dword_regs["pump2_run_time_hr"] = int(
                        dword_regs["pump2_run_time_min"] / 60
                    )
                    pump2_run_last_min = pump2_run_current_time
                    registers = []
                    try:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            rt2_min = split_double([dword_regs["pump2_run_time_min"]])
                            rt2_hr = split_double([dword_regs["pump2_run_time_hr"]])

                            client.write_registers(274, rt2_min)
                            client.write_registers(276, rt2_hr)

                            client.write_registers(202, rt2_hr)

                    except Exception as e:
                        print(f"read pump2 runtime error: {e}")
            else:
                pump2_run_last_min = time.time()

            if word_regs["inv1_speed_set"] > 0 or word_regs["inv2_speed_set"] > 0:
                try:
                    for filter_name, (min_reg, hr_reg) in filter_runtime[
                        "address"
                    ].items():
                        current_time = time.time()

                        try:
                            with ModbusTcpClient(
                                host=modbus_host, port=modbus_port
                            ) as client:
                                r = client.read_holding_registers(
                                    min_reg, 4, unit=modbus_slave_id
                                )
                                if not r.isError():
                                    previous_min = read_split_register(r.registers, 0)
                                    previous_hr = read_split_register(r.registers, 2)

                                    filter_runtime["runtime"][filter_name]["min"] = (
                                        previous_min
                                    )
                                    filter_runtime["runtime"][filter_name]["hr"] = (
                                        previous_hr
                                    )
                                else:
                                    print(
                                        f"Failed to read register {min_reg} for {filter_name}"
                                    )
                        except Exception as e:
                            print(
                                f"Error reading filter runtime for {filter_name}: {e}"
                            )

                        if (
                            current_time
                            - filter_runtime["filter_run_last_min"][filter_name]
                            >= 60
                        ):
                            filter_runtime["runtime"][filter_name]["min"] += 1
                            filter_runtime["runtime"][filter_name]["hr"] = int(
                                filter_runtime["runtime"][filter_name]["min"] / 60
                            )
                            filter_runtime["filter_run_last_min"][filter_name] = (
                                current_time
                            )

                            try:
                                with ModbusTcpClient(
                                    host=modbus_host, port=modbus_port
                                ) as client:
                                    filter_min = split_double(
                                        [filter_runtime["runtime"][filter_name]["min"]]
                                    )
                                    filter_hr = split_double(
                                        [filter_runtime["runtime"][filter_name]["hr"]]
                                    )

                                    client.write_registers(min_reg, filter_min)
                                    client.write_registers(hr_reg, filter_hr)

                                    client.write_registers(hr_reg, filter_hr)
                            except Exception as e:
                                print(f"read filter runtime error: {e}")
                except Exception as e:
                    print(f"filter error:{e}")

            set_warning_registers(f1_issue, mode)

            time.sleep(1)
        except Exception as e:
            print(f"TCP Client Error: {e}")

        try:
            try:
                global server1_count
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_holding_registers(300, 1, unit=modbus_slave_id)

                    server1_count = r.registers[0]
                    if r.registers[0] > 30000:
                        server1_count = 0
                        client.write_register(300, server1_count)

                    else:
                        server1_count += 1
                        client.write_register(300, server1_count)

            except Exception as e:
                print(f"main server count error:{e}")

            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_holding_registers(301, 1, unit=modbus_slave_id)
                    check_server2 = r.registers[0]

                    # print(f"主機二：{pre_check_server2} => {check_server2}")
                    # print(f"停滯時間：{server_error["diff"]}")
                    # print(f"確認異常：{server2_occur_stop}")

                    if zero_flag:
                        server_error["diff"] = 0
                        zero_flag = False

                    if check_server2 == pre_check_server2:
                        server_error["diff"] += time.time() - server_error["start"]
                    else:
                        server_error["diff"] = 0

                    if server_error["diff"] >= 300:
                        if restart_server["stage"] == 0:
                            restart_server["stage"] = 1
                        else:
                            pass
                    else:
                        restart_server["stage"] = 0

                    if server_error["diff"] >= 5:
                        server2_occur_stop = True
                        pre_check_server2 = check_server2
                        warning_data["error"]["pc2_error"] = True
                    else:
                        server2_occur_stop = False
                        pre_check_server2 = check_server2
                        warning_data["error"]["pc2_error"] = False

            except Exception as e:
                print(f"server 1 check error:{e}")

            if server2_occur_stop:
                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        if restart_server["stage"] == 1:
                            client.write_coils(13, [True])
                            print("按10秒 on")

                            restart_server["diff"] += (
                                time.time() - restart_server["start"]
                            )

                            if restart_server["diff"] > 10:
                                restart_server["stage"] = 2

                        elif restart_server["stage"] == 2:
                            client.write_coils(13, [False])
                            print("按1秒 off")
                            restart_server["diff"] += (
                                time.time() - restart_server["start"]
                            )
                            if restart_server["diff"] > 16:
                                restart_server["stage"] = 3

                        elif restart_server["stage"] == 3:
                            client.write_coils(13, [True])
                            print("按1秒 on")
                            restart_server["diff"] += (
                                time.time() - restart_server["start"]
                            )
                            if restart_server["diff"] > 18:
                                restart_server["stage"] = 4

                        elif restart_server["stage"] == 4:
                            client.write_coils(13, [False])
                            restart_server["diff"] = 0
                            restart_server["start"] = 0
                            zero_flag = True
                            print("回歸 off")
                except Exception as e:
                    print(f"server 2 restart error:{e}")
        except Exception as e:
            print(f"monitor and counting Error: {e}")


duration = 1


def rtu_thread():
    client = ModbusSerialClient(
        method="rtu", 
        port="/dev/ttyS1",
        baudrate=19200,
        parity="E",
        stopbits=1,
        bytesize=8,
        timeout=0.5,
    )
    try:
        while True:
            global port, ver_switch, rtu_flag

            try:
                if rtu_flag:
                    client = ModbusSerialClient(
                        method="rtu",
                        port=port,
                        baudrate=19200,
                        parity="E",
                        stopbits=1,
                        bytesize=8,
                        timeout=0.5,
                    )
                    rtu_flag = False

                if not client.connect():
                    for key in raw_485_data.keys():
                        raw_485_data[key] = 0
                        raw_485_communication[key] = True
                    print("Failed to connect to Modbus server")
                    journal_logger.info("Failed to connect to Modbus server")
                    time.sleep(2)
                    continue

                try:
                    response = client.read_holding_registers(0, 2, unit=4)

                    rh = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["relative_humidity"] = rh

                except Exception as e:
                    print(f"Relative Humidity error: {e}")
                    journal_logger.info(f"Relative Humidity error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(2, 2, unit=4)

                    t3 = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["ambient_temperature"] = t3
                    raw_485_communication["ambient_temperature"] = False

                except Exception as e:
                    raw_485_communication["ambient_temperature"] = True
                    journal_logger.info(f"Ambient Temperature error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(8, 2, unit=4)

                    dewPt = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["dew_point_temperature"] = dewPt

                except Exception as e:
                    journal_logger.info(f"Dew Point Temperature error: {e}")

                time.sleep(duration)

                if ver_switch["flow_switch"]:
                    try:
                        response = client.read_holding_registers(1, 1, unit=5)

                        f1 = response.registers[0]
                        raw_485_data["coolant_flow_rate"] = f1
                        raw_485_communication["coolant_flow_rate"] = False

                    except Exception as e:
                        raw_485_communication["coolant_flow_rate"] = True
                        journal_logger.info(f"Coolant Flow Rate error: {e}")

                    time.sleep(duration)
                else:
                    raw_485_data["coolant_flow_rate"] = 0
                    raw_485_communication["coolant_flow_rate"] = False

                if ver_switch["flow2_switch"]:
                    try:
                        response = client.read_holding_registers(1, 1, unit=6)

                        f2 = response.registers[0]
                        raw_485_data["facility_water_flow_rate"] = f2
                        raw_485_communication["facility_water_flow_rate"] = False

                    except Exception as e:
                        raw_485_communication["facility_water_flow_rate"] = True
                        journal_logger.info(f"Facility Water Flow Rate error: {e}")

                    time.sleep(duration)
                else:
                    raw_485_data["facility_water_flow_rate"] = 0
                    raw_485_communication["facility_water_flow_rate"] = False

                try:
                    response = client.read_holding_registers(0, 2, unit=9)

                    pH = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["ph"] = pH
                    raw_485_communication["ph"] = False

                except Exception as e:
                    raw_485_communication["ph"] = True
                    journal_logger.info(f"pH error: {e}")

                time.sleep(duration)
                try:
                    response = client.read_holding_registers(0, 2, unit=9)

                    pH = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["ph"] = pH
                    raw_485_communication["ph"] = False

                except Exception as e:
                    raw_485_communication["ph"] = True
                    journal_logger.info(f"pH error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(0, 2, unit=7)

                    CON = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["conductivity"] = CON
                    raw_485_communication["conductivity"] = False

                except Exception as e:
                    raw_485_communication["conductivity"] = True
                    journal_logger.info(f"Conductivity error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(0, 2, unit=8)

                    Tur = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["turbidity"] = Tur
                    raw_485_communication["turbidity"] = False

                except Exception as e:
                    raw_485_communication["turbidity"] = True
                    journal_logger.info(f"Turbidity error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(0, 2, unit=8)

                    Tur = cvt_registers_to_float(
                        response.registers[0], response.registers[1]
                    )
                    raw_485_data["turbidity"] = Tur
                    raw_485_communication["turbidity"] = False

                except Exception as e:
                    raw_485_communication["turbidity"] = True
                    journal_logger.info(f"Turbidity error: {e}")

                time.sleep(duration)

                if not ver_switch["function_switch"]:
                    try:
                        response = client.read_holding_registers(3059, 2, unit=3)
                        pw = cvt_registers_to_float(
                            response.registers[1], response.registers[0]
                        )
                        pw = abs(pw)
                        raw_485_data["instant_power_consumption"] = pw
                        raw_485_communication["instant_power_consumption"] = False

                    except Exception as e:
                        raw_485_communication["instant_power_consumption"] = True
                        journal_logger.info(f"Instant Power Consumption error: {e}")
                else:
                    try:
                        response = client.read_holding_registers(324, 2, unit=3)

                        pw = cvt_registers_to_float(
                            response.registers[0], response.registers[1]
                        )
                        raw_485_data["instant_power_consumption"] = pw
                        raw_485_communication["instant_power_consumption"] = False

                    except Exception as e:
                        raw_485_communication["instant_power_consumption"] = True
                        journal_logger.info(f"Instant Power Consumption error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(304, 1, unit=1)

                    inv1 = response.registers[0]
                    raw_485_data["inv1_speed"] = inv1
                    raw_485_communication["inv1_speed"] = False

                except Exception as e:
                    raw_485_communication["inv1_speed"] = True
                    journal_logger.info(f"Inv1 Speed error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(204, 1, unit=1)

                    inv1_result = response.registers[0]
                    if inv1_result > 0:
                        warning_data["error"]["Inv1_error_code"] = True
                        inv_error_code["code1"] = inv1_result
                    else:
                        warning_data["error"]["Inv1_error_code"] = False
                        inv_error_code["code1"] = 0
                except Exception as e:
                    journal_logger.info(f"Inv1 Speed code error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(304, 1, unit=2)

                    inv2 = response.registers[0]
                    raw_485_data["inv2_speed"] = inv2
                    raw_485_communication["inv2_speed"] = False

                except Exception as e:
                    raw_485_communication["inv2_speed"] = True
                    journal_logger.info(f"Inv2 Speed error: {e}")

                time.sleep(duration)

                try:
                    response = client.read_holding_registers(204, 1, unit=2)

                    inv2_result = response.registers[0]
                    if inv2_result > 0:
                        warning_data["error"]["Inv2_error_code"] = True
                        inv_error_code["code2"] = inv2_result
                    else:
                        warning_data["error"]["Inv2_error_code"] = False
                        inv_error_code["code2"] = 0

                except Exception as e:
                    journal_logger.info(f"Inv2 Speed code error: {e}")

                time.sleep(duration)

                if not ver_switch["function_switch"]:
                    try:
                        response = client.read_holding_registers(3009, 2, unit=3)

                        ac = cvt_registers_to_float(
                            response.registers[1], response.registers[0]
                        )
                        ac = abs(ac)
                        raw_485_data["average_current"] = ac

                    except Exception as e:
                        journal_logger.info(f"Average Current error: {e}")
                else:
                    try:
                        response = client.read_holding_registers(294, 2, unit=3)

                        ac = cvt_registers_to_float(
                            response.registers[0], response.registers[1]
                        )
                        raw_485_data["average_current"] = ac

                    except Exception as e:
                        journal_logger.info(f"Average Current error: {e}")

                time.sleep(duration)

                if not ver_switch["function_switch"]:
                    try:
                        ats_read = client.read_input_registers(40, 1, unit=10)

                        ats = ats_read.registers[0]
                        ats1 = ats & 0x0001
                        raw_485_data["ATS1"] = ats1 == 1

                        ats2 = (ats >> 9) & 0x0001
                        raw_485_data["ATS2"] = ats2 == 1
                        raw_485_communication["ATS1"] = False
                    except Exception as e:
                        raw_485_communication["ATS1"] = True
                        journal_logger.info(f"ATS error: {e}")

                else:
                    try:
                        response = client.read_discrete_inputs(6, 9, unit=10)

                        ats1 = bool(response.bits[0])
                        ats2 = bool(response.bits[8])
                        print(f"ATS1: {ats1}")
                        raw_485_data["ATS1"] = ats1 == 1
                        raw_485_data["ATS2"] = ats2 == 1
                        raw_485_communication["ATS1"] = False

                    except Exception as e:
                        raw_485_communication["ATS1"] = True
                        journal_logger.info(f"ATS error: {e}")

                time.sleep(duration)
                journal_logger.info(f"485 數據：{raw_485_data}")
                journal_logger.info(f"485 通訊：{raw_485_communication}")
            except Exception as e:
                print(f"enclosed: {e}")
    except Exception as e:
        print(f"485 issue: {e}")
    finally:
        client.close()


def rack_thread():
    host = {
        "rack1": "192.168.3.10",
        "rack2": "192.168.3.11",
        "rack3": "192.168.3.12",
        "rack4": "192.168.3.13",
        "rack5": "192.168.3.14",
        "rack6": "192.168.3.15",
        "rack7": "192.168.3.16",
        "rack8": "192.168.3.17",
        "rack9": "192.168.3.18",
        "rack10": "192.168.3.19",
    }

    while True:
        try:
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    r = client.read_coils((8192 + 710), 20)
                    for x, key in enumerate(rack_data["rack_control"].keys()):
                        rack_data["rack_control"][key] = r.bits[x]
            except Exception as e:
                print(f"rack control error: {e}")
                # journal_logger.info(f"rack control error: {e}")
                time.sleep(1)
                continue

            try:
                for i in range(10):
                    enable_key = f"Rack_{i + 1}_Enable"
                    control_key = f"Rack_{i + 1}_Control"
                    ip_key = f"rack{i + 1}"
                    rack_ip = host[ip_key]
                    pass_key = f"Rack_{i + 1}_Pass"

                    if rack_data["rack_control"][enable_key]:
                        try:
                            with ModbusTcpClient(
                                host=rack_ip, port=modbus_port, timeout=0.5
                            ) as client:
                                if rack_data["rack_control"][control_key]:
                                    client.write_register(0, 4095)
                                else:
                                    client.write_register(0, 0)
                                rack_data["rack_pass"][pass_key] = True
                        except Exception as e:
                            rack_data["rack_pass"][pass_key] = False
                            print(f"rack input error: {e}")
                            # journal_logger.info(f"rack input error: {e}")
            except Exception as e:
                print(f"rack key error: {e}")

            try:
                coil_values = list(rack_data["rack_pass"].values())
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_coils((8192 + 730), coil_values)
            except Exception as e:
                print(f"pass error: {e}")
        except Exception as e:
            print(f"enclosed: {e}")

        time.sleep(2)


rack_thread_obj = threading.Thread(target=rack_thread)
rack_thread_obj.daemon = True
rack_thread_obj.start()

thread = threading.Thread(target=control)
thread.daemon = True
thread.start()


if onLinux:
    rtu_thread_obj = threading.Thread(target=rtu_thread)
    rtu_thread_obj.daemon = True
    rtu_thread_obj.start()

try:
    while True:
        time.sleep(30)
except KeyboardInterrupt:
    print("程序已终止")

except Exception as e:
    print(f"異常：{e}")

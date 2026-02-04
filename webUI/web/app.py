import csv
import datetime as dt
import glob
import ipaddress
import json
import logging
import math
import os
import struct
import subprocess
import time
from io import BytesIO
import zipfile

# import psutil

from collections import OrderedDict
from datetime import datetime
from logging.handlers import RotatingFileHandler
import threading
import platform
import pyzipper
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv, set_key
from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    send_file,
)
from flask_cors import CORS

from flask_login import LoginManager, current_user, login_required, logout_user
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
app = Flask(__name__)
CORS(app)

log_path = os.getcwd()
web_path = f"{log_path}/web"
snmp_path = os.path.dirname(log_path)

upload_path = "/home/user/"
app.config["UPLOAD_FOLDER"] = upload_path

key = os.environ.get("SECRET_KEY")
app.secret_key = key
cipher_suite = Fernet(key.encode())

if platform.system() == "Linux":
    onLinux = True
else:
    onLinux = False

warning_toggle = os.environ.get("WARNING_TOGGLE") == "True"
alert_toggle = os.environ.get("ALERT_TOGGLE") == "True"
error_toggle = os.environ.get("ERROR_TOGGLE") == "True"
log_repeat = os.environ.get("NOLOGREPEAT") == "False"

previous_warning_states = {}
previous_alert_states = {}
previous_error_states = {}
prev_plc_error = False
if onLinux:
    from web.auth import (
        USER_DATA,
        User,
        auth_bp,
        user_login_info,
    )
else:
    from auth import (
        USER_DATA,
        User,
        auth_bp,
        user_login_info,
    )

app.register_blueprint(auth_bp)

if onLinux:
    from web.scc_app import scc_bp
else:
    from scc_app import scc_bp

app.register_blueprint(scc_bp)

login_manager = LoginManager()
login_manager.init_app(app)

journal_dir = f"{log_path}/logs/journal"
if not os.path.exists(journal_dir):
    os.makedirs(journal_dir)

max_bytes = 4 * 1024 * 1024 * 1024
backup_count = 1

file_name = "journal.log"
log_file = os.path.join(journal_dir, file_name)
journal_handler = RotatingFileHandler(
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

log_dir = f"{log_path}/logs/error"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

file_name = "errorlog.log"
log_file = os.path.join(log_dir, file_name)
errlog_handler = ConcurrentTimedRotatingFileHandler(
    log_file,
    when="midnight",
    backupCount=1100,
    encoding="UTF-8",
)
errlog_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
errlog_handler.setFormatter(formatter)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(errlog_handler)

log_dir = f"{log_path}/logs/operation"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


file_name = "oplog.log"
log_file = os.path.join(log_dir, file_name)

oplog_handler = ConcurrentTimedRotatingFileHandler(
    log_file,
    when="midnight",
    backupCount=1100,
    encoding="UTF-8",
    delay=False,
)
oplog_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
oplog_handler.setFormatter(formatter)
op_logger = logging.getLogger("custom")
op_logger.setLevel(logging.INFO)
op_logger.addHandler(oplog_handler)






@login_manager.user_loader
def load_user(user_id):
    users = USER_DATA
    if user_id in users:
        user_identity["ID"] = user_id
        return User(user_id)
    return None


if log_repeat:
    repeat = True
else:
    repeat = False


modbus_host = os.environ.get("MODBUS_IP")
# modbus_host = "127.0.0.1"

modbus_port = 502
modbus_slave_id = 1
modbus_address = 0

pc2_active = False
get_data_timeout = 5
tcount_log = 0
error_data = []
signal_records = []
downtime_signal_records = []
imperial_thrshd_factory = {}
imperial_valve_factory = {}
mode_input = {}
export_data = {}


sensorData = {
    "value": {
        "temp_clntSply": 0,
        "temp_clntSplySpr": 0,
        "temp_clntRtn": 0,
        "temp_waterIn": 0,
        "temp_waterOut": 0,
        "prsr_clntSply": 0,
        "prsr_clntSplySpr": 0,
        "prsr_clntRtn": 0,
        "prsr_fltIn": 0,
        "prsr_flt1Out": 0,
        "prsr_flt2Out": 0,
        "prsr_flt3Out": 0,
        "prsr_flt4Out": 0,
        "prsr_flt5Out": 0,
        "prsr_clntRtnSpr": 0,
        "prsr_wtrIn": 0,
        "prsr_wtrOut": 0,
        "WaterPV": 0,
        "rltHmd": 0,
        "temp_ambient": 0,
        "dewPt": 0,
        "flow_clnt": 0,
        "flow_wtr": 0,
        "pH": 0,
        "cdct": 0,
        "tbd": 0,
        "power": 0,
        "inv1_freq": 0,
        "inv2_freq": 0,
        "AC": 0,
        "heat_capacity": 0,
    },
    "warning_notice": {
        "temp_clntSply": False,
        "temp_clntSplySpr": False,
        "temp_clntRtn": False,
        "temp_waterIn": False,
        "temp_waterOut": False,
        "prsr_clntSply": False,
        "prsr_clntSplySpr": False,
        "prsr_clntRtn": False,
        "prsr_clntRtnSpr": False,
        "prsr_fltIn": False,
        "prsr_flt1Out": False,
        "prsr_flt2Out": False,
        "prsr_flt3Out": False,
        "prsr_flt4Out": False,
        "prsr_flt5Out": False,
        "prsr_wtrIn": False,
        "prsr_wtrOut": False,
        "relative_humid": False,
        "temp_ambient": False,
        "dew_point_temp": False,
        "clnt_flow": False,
        "wtr_flow": False,
        "ph": False,
        "cndct": False,
        "tbd": False,
        "AC": False,
    },
    "alert_notice": {
        "temp_clntSply": False,
        "temp_clntSplySpr": False,
        "temp_clntRtn": False,
        "temp_waterIn": False,
        "temp_waterOut": False,
        "prsr_clntSply": False,
        "prsr_clntSplySpr": False,
        "prsr_clntRtn": False,
        "prsr_clntRtnSpr": False,
        "prsr_fltIn": False,
        "prsr_flt1Out": False,
        "prsr_flt2Out": False,
        "prsr_flt3Out": False,
        "prsr_flt4Out": False,
        "prsr_flt5Out": False,
        "prsr_wtrIn": False,
        "prsr_wtrOut": False,
        "relative_humid": False,
        "temp_ambient": False,
        "dew_point_temp": False,
        "clnt_flow": False,
        "wtr_flow": False,
        "ph": False,
        "cndct": False,
        "tbd": False,
        "AC": False,
    },
    "warning": {
        "temp_clntSply_high": False,
        "temp_clntSplySpr_high": False,
        "temp_clntRtn_high": False,
        "temp_waterIn_low": False,
        "temp_waterIn_high": False,
        "temp_waterOut_low": False,
        "temp_waterOut_high": False,
        "prsr_clntSply_high": False,
        "prsr_clntSplySpr_high": False,
        "prsr_clntRtn_high": False,
        "prsr_clntRtnSpr_high": False,
        "prsr_fltIn_low": False,
        "prsr_fltIn_high": False,
        "prsr_flt1Out_high": False,
        "prsr_flt2Out_high": False,
        "prsr_flt3Out_high": False,
        "prsr_flt4Out_high": False,
        "prsr_flt5Out_high": False,
        "prsr_wtrIn_high": False,
        "prsr_wtrOut_high": False,
        "relative_humid_low": False,
        "relative_humid_high": False,
        "temp_ambient_low": False,
        "temp_ambient_high": False,
        "dew_point_temp_low": False,
        "clnt_flow_low": False,
        "wtr_flow_low": False,
        "ph_low": False,
        "ph_high": False,
        "cndct_low": False,
        "cndct_high": False,
        "tbd_low": False,
        "tbd_high": False,
        "AC_high": False,
    },
    "alert": {
        "temp_clntSply_high": False,
        "temp_clntSplySpr_high": False,
        "temp_clntRtn_high": False,
        "temp_waterIn_low": False,
        "temp_waterIn_high": False,
        "temp_waterOut_low": False,
        "temp_waterOut_high": False,
        "prsr_clntSply_high": False,
        "prsr_clntSplySpr_high": False,
        "prsr_clntRtn_high": False,
        "prsr_clntRtnSpr_high": False,
        "prsr_fltIn_low": False,
        "prsr_fltIn_high": False,
        "prsr_flt1Out_high": False,
        "prsr_flt2Out_high": False,
        "prsr_flt3Out_high": False,
        "prsr_flt4Out_high": False,
        "prsr_flt5Out_high": False,
        "prsr_wtrIn_high": False,
        "prsr_wtrOut_high": False,
        "relative_humid_low": False,
        "relative_humid_high": False,
        "temp_ambient_low": False,
        "temp_ambient_high": False,
        "dew_point_temp_low": False,
        "clnt_flow_low": False,
        "wtr_flow_low": False,
        "ph_low": False,
        "ph_high": False,
        "cndct_low": False,
        "cndct_high": False,
        "tbd_low": False,
        "tbd_high": False,
        "AC_high": False,
    },
    "error": {
        "Water_PV_Error": False,
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
        "ATS1": False,
        "Inv1_Com": False,
        "Inv2_Com": False,
        "Ambient_Sensor_Com": False,
        "Clnt_Flow_Com": False,
        "Wtr_Flow_Com": False,
        "Cndct_Sensor_Com": False,
        "ph_Com": False,
        "Tbd_Com": False,
        "ATS_Com": False,
        "Power_Meter_Com": False,
        "TempClntSply_broken": False,
        "TempClntSplySpr_broken": False,
        "TempClntRtn_broken": False,
        "TempWaterIn_broken": False,
        "TempWaterOut_broken": False,
        "PrsrClntSply_broken": False,
        "PrsrClntSplySpr_broken": False,
        "PrsrClntRtn_broken": False,
        "PrsrClntRtnSpr_broken": False,
        "PrsrFltIn_broken": False,
        "PrsrFlt1Out_broken": False,
        "PrsrFlt2Out_broken": False,
        "PrsrFlt3Out_broken": False,
        "PrsrFlt4Out_broken": False,
        "PrsrFlt5Out_broken": False,
        "PrsrWaterIn_broken": False,
        "PrsrWaterOut_broken": False,
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
        "PLC": False,
    },
    "err_log": {
        "warning": {
            "temp_clntSply_high": "M100 Coolant Supply Temperature Over Range (High) Warning (T1)",
            "temp_clntSplySpr_high": "M101 Coolant Supply Temperature Spare Over Range (High) Warning (T1 sp)",
            "temp_clntRtn_high": "M102 Coolant Return Temperature Over Range (High) Warning (T2)",
            "temp_waterIn_low": "M103 Facility Water Supply Temperature Over Range (Low) Warning (T4)",
            "temp_waterIn_high": "M104 Facility Water Supply Temperature Over Range (High) Warning (T4)",
            "temp_waterOut_low": "M105 Facility Water Return Temperature Over Range (Low) Warning (T5)",
            "temp_waterOut_high": "M106 Facility Water Return Temperature Over Range (High) Warning (T5)",
            "prsr_clntSply_high": "M107 Coolant Supply Pressure Over Range (High) Warning (P1)",
            "prsr_clntSplySpr_high": "M108 Coolant Supply Pressure Spare Over Range (High) Warning (P1 sp)",
            "prsr_clntRtn_high": "M109 Coolant Return Pressure Over Range (High) Warning (P2)",
            "prsr_fltIn_low": "M110 Filter Inlet Pressure Over Range (Low) Warning (P3)",
            "prsr_fltIn_high": "M111 Filter Inlet Pressure Over Range (High) Warning (P3)",
            "prsr_flt1Out_high": "M112 Filter1 Outlet Pressure Over Range (High) Warning (P4)",
            "prsr_flt2Out_high": "M113 Filter2 Outlet Pressure Over Range (High) Warning (P5)",
            "prsr_flt3Out_high": "M114 Filter3 Outlet Pressure Over Range (High) Warning (P6)",
            "prsr_flt4Out_high": "M115 Filter4 Outlet Pressure Over Range (High) Warning (P7)",
            "prsr_flt5Out_high": "M116 Filter5 Outlet Pressure Over Range (High) Warning (P8)",
            "prsr_wtrIn_high": "M117 Facility Water Supply Pressure Over Range (High) Warning (P10)",
            "prsr_wtrOut_high": "M118 Facility Water Return Pressure Over Range (High) Warning (P11)",
            "relative_humid_low": "M119 Relative Humidity Over Range (Low) Warning (RH)",
            "relative_humid_high": "M120 Relative Humidity Over Range (High) Warning (RH)",
            "temp_ambient_low": "M121 Ambient Temperature Over Range (Low) Warning (T a)",
            "temp_ambient_high": "M122 Ambient Temperature Over Range (High) Warning (T a)",
            "dew_point_temp_low": "M123 Condensation Warning (T Dp)",
            "clnt_flow_low": "M124 Coolant Flow Rate (Low) Warning (F1)",
            "wtr_flow_low": "M125 Facility Water Flow Rate (Low) Warning (F2)",
            "ph_low": "M126 pH Over Range (Low) Warning (PH)",
            "ph_high": "M127 pH Over Range (High) Warning (PH)",
            "cndct_low": "M128 Conductivity Over Range (Low) Warning (CON)",
            "cndct_high": "M129 Conductivity Over Range (High) Warning (CON)",
            "tbd_low": "M130 Turbidity Over Range (Low) Warning (Tur)",
            "tbd_high": "M131 Turbidity Over Range (High) Warning (Tur)",
            "AC_high": "M132 Average Current Over Range (High) Warning",
            "prsr_clntRtnSpr_high": "M133 Coolant Return Pressure Spare Over Range (High) Warning (P2 sp)",
        },
        "alert": {
            "temp_clntSply_high": "M200 Coolant Supply Temperature Over Range (High) Alert (T1)",
            "temp_clntSplySpr_high": "M201 Coolant Supply Temperature Spare Over Range (High) Alert (T1 sp)",
            "temp_clntRtn_high": "M202 Coolant Return Temperature Over Range (High) Alert (T2)",
            "temp_waterIn_low": "M203 Facility Water Supply Temperature Over Range (Low) Alert (T4)",
            "temp_waterIn_high": "M204 Facility Water Supply Temperature Over Range (High) Alert (T4)",
            "temp_waterOut_low": "M205 Facility Water Return Temperature Over Range (Low) Alert (T5)",
            "temp_waterOut_high": "M206 Facility Water Return Temperature Over Range (High) Alert (T5)",
            "prsr_clntSply_high": "M207 Coolant Supply Pressure Over Range (High) Alert (P1)",
            "prsr_clntSplySpr_high": "M208 Coolant Supply Pressure Spare Over Range (High) Alert (P1 sp)",
            "prsr_clntRtn_high": "M209 Coolant Return Pressure Over Range (High) Alert (P2)",
            "prsr_fltIn_low": "M210 Filter Inlet Pressure Over Range (Low) Alert (P3)",
            "prsr_fltIn_high": "M211 Filter Inlet Pressure Over Range (High) Alert (P3)",
            "prsr_flt1Out_high": "M212 Filter1 Outlet Pressure Over Range (High) Alert (P4)",
            "prsr_flt2Out_high": "M213 Filter2 Outlet Pressure Over Range (High) Alert (P5)",
            "prsr_flt3Out_high": "M214 Filter3 Outlet Pressure Over Range (High) Alert (P6)",
            "prsr_flt4Out_high": "M215 Filter4 Outlet Pressure Over Range (High) Alert (P7)",
            "prsr_flt5Out_high": "M216 Filter5 Outlet Pressure Over Range (High) Alert (P8)",
            "prsr_wtrIn_high": "M217 Facility Water Supply Pressure Over Range (High) Alert (P10)",
            "prsr_wtrOut_high": "M218 Facility Water Return Pressure Over Range (High) Alert (P11)",
            "relative_humid_low": "M219 Relative Humidity Over Range (Low) Alert (RH)",
            "relative_humid_high": "M220 Relative Humidity Over Range (High) Alert (RH)",
            "temp_ambient_low": "M221 Ambient Temperature Over Range (Low) Alert (T a)",
            "temp_ambient_high": "M222 Ambient Temperature Over Range (High) Alert (T a)",
            "dew_point_temp_low": "M223 Condensation Alert (T Dp)",
            "clnt_flow_low": "M224 Coolant Flow Rate (Low) Alert (F1)",
            "wtr_flow_low": "M225 Facility Water Flow Rate (Low) Alert (F2)",
            "ph_low": "M226 pH Over Range (Low) Alert (PH)",
            "ph_high": "M227 pH Over Range (High) Alert (PH)",
            "cndct_low": "M228 Conductivity Over Range (Low) Alert (CON)",
            "cndct_high": "M229 Conductivity Over Range (High) Alert (CON)",
            "tbd_low": "M230 Turbidity Over Range (Low) Alert (Tur)",
            "tbd_high": "M231 Turbidity Over Range (High) Alert (Tur)",
            "AC_high": "M232 Average Current Over Range (High) Alert",
            "prsr_clntRtnSpr_high": "M233 Coolant Return Pressure Spare Over Range (High) Alert (P2 sp)",
        },
        "error": {
            "Water_PV_Error": "M300 Facility Water Proportional Valve (PV1) Disconnection",
            "Inv1_OverLoad": "M301 Coolant Pump1 Inverter Overload",
            "Inv2_OverLoad": "M302 Coolant Pump2 Inverter Overload",
            "Inv1_Error": "M303 Coolant Pump1 Inverter Error",
            "Inv2_Error": "M304 Coolant Pump2 Inverter Error",
            "Water_Leak": "M305 Facility Water Leakage",
            "Water_Leak_Broken": "M306 Facility Water Leakage Sensor Broken",
            "EV1_Error": "M307 Coolant Pump1 Outlet Electrical Valve (EV1) Error",
            "EV2_Error": "M308 Coolant Pump1 Inlet Electrical Valve (EV2) Error",
            "EV3_Error": "M309 Coolant Pump2 Outlet Electrical Valve (EV3) Error",
            "EV4_Error": "M310 Coolant Pump2 Inlet Electrical Valve (EV4) Error",
            "ATS1": "M311 Factory Power Status",
            "Inv1_Com": "M312 Inverter1 Communication Error",
            "Inv2_Com": "M313 Inverter2 Communication Error",
            "Ambient_Sensor_Com": "M314 Ambient Sensor (T a) Communication Error",
            "Clnt_Flow_Com": "M315 Coolant Flow Meter (F1) Communication Error",
            "Wtr_Flow_Com": "M316 Water Flow Meter (F2) Communication Error",
            "Cndct_Sensor_Com": "M317 Conductivity (CON) Sensor Communication Error",
            "ph_Com": "M318 pH (PH) Sensor Communication Error",
            "Tbd_Com": "M319 Turbidity (Tur) Sensor Communication Error",
            "ATS_Com": "M320 ATS Communication Error",
            "Power_Meter_Com": "M321 Power Meter Communication Error",
            "TempClntSply_broken": "M322 Coolant Supply Temperature (T1) Broken Error",
            "TempClntSplySpr_broken": "M323 Coolant Supply Temperature (Spare) (T1 sp) Broken Error",
            "TempClntRtn_broken": "M324 Coolant Return Temperature (T2) Broken Error",
            "TempWaterIn_broken": "M325 Facility Water Supply Temperature (T4) Broken Error",
            "TempWaterOut_broken": "M326 Facility Water Return Temperature (T5) Broken Error",
            "PrsrClntSply_broken": "M327 Coolant Supply Pressure (P1) Broken Error",
            "PrsrClntSplySpr_broken": "M328 Coolant Supply Pressure (Spare) (P1 sp) Broken Error",
            "PrsrClntRtn_broken": "M329 Coolant Return Pressure (P2) Broken Error",
            "PrsrFltIn_broken": "M330 Filter Inlet Pressure (P3) Broken Error",
            "PrsrFlt1Out_broken": "M331 Filter1 Outlet Pressure (P4) Broken Error",
            "PrsrFlt2Out_broken": "M332 Filter2 Outlet Pressure (P5) Broken Error",
            "PrsrFlt3Out_broken": "M333 Filter3 Outlet Pressure (P6) Broken Error",
            "PrsrFlt4Out_broken": "M334 Filter4 Outlet Pressure (P7) Broken Error",
            "PrsrFlt5Out_broken": "M335 Filter5 Outlet Pressure (P8) Broken Error",
            "PrsrWaterIn_broken": "M336 Facility Water Supply Pressure (P10) Broken Error",
            "PrsrWaterOut_broken": "M337 Facility Water Return Pressure (P11) Broken Error",
            "Clnt_Flow_broken": "M338 Coolant Flow Rate (F1) Broken Error",
            "Wtr_Flow_broken": "M339 Facility Water Flow Rate (F2) Broken Error",
            "Low_Coolant_Level_Warning": "M340 Stop Due to Low Coolant Level",
            "Inv1_error_code": "M341 Inverter1 Error",
            "Inv2_error_code": "M342 Inverter2 Error",
            "pc1_error": "M343 PC1 Error",
            "pc2_error": "M344 PC2 Error",
            "PrsrClntRtnSpr_broken": "M345 Coolant Return Pressure (Spare) (P2 sp) Broken Error",
            "level1_error": "M346 Liquid Coolant Level 1 Error",
            "level2_error": "M347 Liquid Coolant Level 2 Error",
            "power1_error": "M348 Power Supply 1 Error",
            "power2_error": "M349 Power Supply 2 Error",
            "level3_error": "M350 Liquid Coolant Level 2 Error",
            "PLC": "M351 PLC Communication Broken Error",
        },
    },
    "unit": {
        "unit_temp": "",
        "unit_pressure": "",
        "unit_flow": "",
    },
    "filter": {"all_filter_sw": False},
    "valve": {"EV1": False, "EV2": False, "EV3": False, "EV4": False},
    "collapse": {
        "temp_spare": False,
        "prsr_spare": False,
        "p2_spare": False,
        "t1_no_error": False,
        "p1_no_error": False,
        "p2_no_error": False,
    },
    "ev": {
        "EV1_Open": False,
        "EV1_Close": False,
        "EV2_Open": False,
        "EV2_Close": False,
        "EV3_Open": False,
        "EV3_Close": False,
        "EV4_Open": False,
        "EV4_Close": False,
    },
    "rack_status": {
        "rack1_status": 0,
        "rack2_status": 0,
        "rack3_status": 0,
        "rack4_status": 0,
        "rack5_status": 0,
        "rack6_status": 0,
        "rack7_status": 0,
        "rack8_status": 0,
        "rack9_status": 0,
        "rack10_status": 0,
    },
    "rack_no_connection": {
        "rack1_status": False,
        "rack2_status": False,
        "rack3_status": False,
        "rack4_status": False,
        "rack5_status": False,
        "rack6_status": False,
        "rack7_status": False,
        "rack8_status": False,
        "rack9_status": False,
        "rack10_status": False,
        "rack1_leak": False,
        "rack2_leak": False,
        "rack3_leak": False,
        "rack4_leak": False,
        "rack5_leak": False,
        "rack6_leak": False,
        "rack7_leak": False,
        "rack8_leak": False,
        "rack9_leak": False,
        "rack10_leak": False,
    },
    "rack_leak": {
        "rack1_leak": False,
        "rack2_leak": False,
        "rack3_leak": False,
        "rack4_leak": False,
        "rack5_leak": False,
        "rack6_leak": False,
        "rack7_leak": False,
        "rack8_leak": False,
        "rack9_leak": False,
        "rack10_leak": False,
    },
    "rack_broken": {
        "rack1_broken": False,
        "rack2_broken": False,
        "rack3_broken": False,
        "rack4_broken": False,
        "rack5_broken": False,
        "rack6_broken": False,
        "rack7_broken": False,
        "rack8_broken": False,
        "rack9_broken": False,
        "rack10_broken": False,
    },
    "ats_status": {
        "ATS1": False,
        "ATS2": False,
    },
    "level_sw": {
        "level1": None,
        "level2": None,
        "level3": None,
        "power1": None,
        "power2": None,
    },
}

ctr_data = {
    "value": {
        "opMod": "manual",
        "oil_temp_set": 0,
        "oil_pressure_set": 0,
        "pump1_speed": 0,
        "pump2_speed": 0,
        "water_PV": 0,
        "resultMode": "Auto",
        "resultTemp": 0,
        "resultPressure": 0,
        "resultP1": 0,
        "resultP2": 0,
        "resultWater": 0,
    },
    "text": {
        "Pump1_run_time": 0,
        "Pump2_run_time": 0,
    },
    "mc": {
        "mc1_sw": False,
        "mc2_sw": False,
        "resultMC1": False,
        "resultMC2": False,
    },
    "inv": {
        "inv1": False,
        "inv2": False,
    },
    "checkbox": {"filter_unlock_sw": True, "all_filter_sw": False},
    "unit": {"unit_temp": "", "unit_prsr": ""},
    "valve": {
        "ev1_sw": False,
        "ev2_sw": False,
        "ev3_sw": False,
        "ev4_sw": False,
        "resultEV1": False,
        "resultEV2": False,
        "resultEV3": False,
        "resultEV4": False,
    },
    "filter": {
        "f1": 0,
        "f2": 0,
        "f3": 0,
        "f4": 0,
        "f5": 0,
    },
    "downtime_error": {
        "oc_issue": False,
        "f1_issue": False,
    },
    "inspect_action": False,
    "rack_set": {
        "rack1_sw": False,
        "rack2_sw": False,
        "rack3_sw": False,
        "rack4_sw": False,
        "rack5_sw": False,
        "rack6_sw": False,
        "rack7_sw": False,
        "rack8_sw": False,
        "rack9_sw": False,
        "rack10_sw": False,
        "rack1_sw_result": False,
        "rack2_sw_result": False,
        "rack3_sw_result": False,
        "rack4_sw_result": False,
        "rack5_sw_result": False,
        "rack6_sw_result": False,
        "rack7_sw_result": False,
        "rack8_sw_result": False,
        "rack9_sw_result": False,
        "rack10_sw_result": False,
    },
    "rack_visibility": {
        "rack1_enable": False,
        "rack2_enable": False,
        "rack3_enable": False,
        "rack4_enable": False,
        "rack5_enable": False,
        "rack6_enable": False,
        "rack7_enable": False,
        "rack8_enable": False,
        "rack9_enable": False,
        "rack10_enable": False,
    },
    "rack_pass": {
        "rack1_pass": False,
        "rack2_pass": False,
        "rack3_pass": False,
        "rack4_pass": False,
        "rack5_pass": False,
        "rack6_pass": False,
        "rack7_pass": False,
        "rack8_pass": False,
        "rack9_pass": False,
        "rack10_pass": False,
    },
    "stop_valve_close": False,
}

thrshd = OrderedDict(
    {
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
        "W_TempClntSply_trap": False,
        "A_TempClntSply_trap": False,
        "W_TempClntSplySpr_trap": False,
        "A_TempClntSplySpr_trap": False,
        "W_TempClntRtn_trap": False,
        "A_TempClntRtn_trap": False,
        "W_TempWaterIn_trap": False,
        "A_TempWaterIn_trap": False,
        "W_TempWaterOut_trap": False,
        "A_TempWaterOut_trap": False,
        "W_PrsrClntSply_trap": False,
        "A_PrsrClntSply_trap": False,
        "W_PrsrClntSplySpr_trap": False,
        "A_PrsrClntSplySpr_trap": False,
        "W_PrsrClntRtn_trap": False,
        "A_PrsrClntRtn_trap": False,
        "W_PrsrClntRtnSpr_trap": False,
        "A_PrsrClntRtnSpr_trap": False,
        "W_PrsrFltIn_trap": False,
        "A_PrsrFltIn_trap": False,
        "W_PrsrFlt1Out_trap": False,
        "A_PrsrFlt1Out_trap": False,
        "W_PrsrFlt2Out_trap": False,
        "A_PrsrFlt2Out_trap": False,
        "W_PrsrFlt3Out_trap": False,
        "A_PrsrFlt3Out_trap": False,
        "W_PrsrFlt4Out_trap": False,
        "A_PrsrFlt4Out_trap": False,
        "W_PrsrFlt5Out_trap": False,
        "A_PrsrFlt5Out_trap": False,
        "W_PrsrWaterIn_trap": False,
        "A_PrsrWaterIn_trap": False,
        "W_PrsrWaterOut_trap": False,
        "A_PrsrWaterOut_trap": False,
        "W_RltvHmd_trap": False,
        "A_RltvHmd_trap": False,
        "W_TempAmbient_trap": False,
        "A_TempAmbient_trap": False,
        "W_TempCds_trap": False,
        "A_TempCds_trap": False,
        "W_ClntFlow_trap": False,
        "A_ClntFlow_trap": False,
        "W_WaterFlow_trap": False,
        "A_WaterFlow_trap": False,
        "W_pH_trap": False,
        "A_pH_trap": False,
        "W_Cdct_trap": False,
        "A_Cdct_trap": False,
        "W_Tbt_trap": False,
        "A_Tbt_trap": False,
        "W_AC_trap": False,
        "A_AC_trap": False,
        "E_WaterPV_trap": False,
        "E_EV1_trap": False,
        "E_EV2_trap": False,
        "E_EV3_trap": False,
        "E_EV4_trap": False,
        "E_Inv1_OverLoad_trap": False,
        "E_Inv2_OverLoad_trap": False,
        "E_Inv1_Error_trap": False,
        "E_Inv2_Error_trap": False,
        "E_Water_Leak_trap": False,
        "E_Water_Leak_Broken_trap": False,
        "E_ATS_trap": False,
        "E_Inverter1_Communication_trap": False,
        "E_Inverter2_Communication_trap": False,
        "E_Ambient_Sensor_Communication_trap": False,
        "E_Coolant_Flow_Meter_Communication_trap": False,
        "E_Water_Flow_Meter_Communication_trap": False,
        "E_Conductivity_Sensor_Communication_trap": False,
        "E_pH_Sensor_Communication_trap": False,
        "E_Turbidity_Sensor_Communication_trap": False,
        "E_ATS_Communication_trap": False,
        "E_Power_Meter_Communication_trap": False,
        "E_TempClntSply_broken_trap": False,
        "E_TempClntSplySpr_broken_trap": False,
        "E_TempClntRtn_broken_trap": False,
        "E_TempWaterIn_broken_trap": False,
        "E_TempWaterOut_broken_trap": False,
        "E_PrsrClntSply_broken_trap": False,
        "E_PrsrClntSplySpr_broken_trap": False,
        "E_PrsrClntRtn_broken_trap": False,
        "E_PrsrClntRtnSpr_broken_trap": False,
        "E_PrsrFltIn_broken_trap": False,
        "E_PrsrFlt1Out_broken_trap": False,
        "E_PrsrFlt2Out_broken_trap": False,
        "E_PrsrFlt3Out_broken_trap": False,
        "E_PrsrFlt4Out_broken_trap": False,
        "E_PrsrFlt5Out_broken_trap": False,
        "E_PrsrWaterIn_broken_trap": False,
        "E_PrsrWaterOut_broken_trap": False,
        "E_Clnt_Flow_broken_trap": False,
        "E_Wtr_Flow_broken_trap": False,
        "E_Low_Coolant_Level_Warning_trap": False,
        "E_Inv1_error_code_trap": False,
        "E_Inv2_error_code_trap": False,
        "E_pc1_error_trap": False,
        "E_pc2_error_trap": False,
        "E_level1_error_trap": False,
        "E_level2_error_trap": False,
        "E_level3_error_trap": False,
        "E_power1_error_trap": False,
        "E_power2_error_trap": False,
        "E_plc_trap": False,
    }
)

sensor_adjust = OrderedDict(
    {
        "Temp_ClntSply_Factor": 1,
        "Temp_ClntSply_Offset": 0,
        "Temp_ClntSplySpr_Factor": 1,
        "Temp_ClntSplySpr_Offset": 0,
        "Temp_ClntRtn_Factor": 1,
        "Temp_ClntRtn_Offset": 0,
        "Temp_WaterIn_Factor": 1,
        "Temp_WaterIn_Offset": 0,
        "Temp_WaterOut_Factor": 1,
        "Temp_WaterOut_Offset": 0,
        "Prsr_ClntSply_Factor": 1,
        "Prsr_ClntSply_Offset": 0,
        "Prsr_ClntSplySpr_Factor": 1,
        "Prsr_ClntSplySpr_Offset": 0,
        "Prsr_ClntRtn_Factor": 1,
        "Prsr_ClntRtn_Offset": 0,
        "Prsr_ClntRtnSpr_Factor": 1,
        "Prsr_ClntRtnSpr_Offset": 0,
        "Prsr_FltIn_Factor": 1,
        "Prsr_FltIn_Offset": 0,
        "Prsr_Flt1Out_Factor": 1,
        "Prsr_Flt1Out_Offset": 0,
        "Prsr_Flt2Out_Factor": 1,
        "Prsr_Flt2Out_Offset": 0,
        "Prsr_Flt3Out_Factor": 1,
        "Prsr_Flt3Out_Offset": 0,
        "Prsr_Flt4Out_Factor": 1,
        "Prsr_Flt4Out_Offset": 0,
        "Prsr_Flt5Out_Factor": 1,
        "Prsr_Flt5Out_Offset": 0,
        "Prsr_WtrIn_Factor": 1,
        "Prsr_WtrIn_Offset": 0,
        "Prsr_WtrOut_Factor": 1,
        "Prsr_WtrOut_Offset": 0,
        "WaterPV_Factor": 1,
        "WaterPV_Offset": 0,
        "RltHmd_Factor": 1,
        "RltHmd_Offset": 0,
        "Temp_Ambient_Factor": 1,
        "Temp_Ambient_Offset": 0,
        "DewPt_Factor": 1,
        "DewPt_Offset": 0,
        "Flow_Clnt_Factor": 1,
        "Flow_Clnt_Offset": 0,
        "Flow_Wtr_Factor": 1,
        "Flow_Wtr_Offset": 0,
        "pH_Factor": 1,
        "pH_Offset": 0,
        "Cdct_Factor": 1,
        "Cdct_Offset": 0,
        "Tbd_Factor": 1,
        "Tbd_Offset": 0,
        "Power_Factor": 1,
        "Power_Offset": 0,
        "Heat_Capacity_Factor": 1,
        "Heat_Capacity_Offset": 0,
        "AC_Factor": 1,
        "AC_Offset": 0,
    }
)


valve_factory = {"ambient": 20, "coolant": 20}

auto_factory = {"pv1": 80, "pump": 50, "water_min": 20}

inv_error_code = {
    "code1": 0,
    "code2": 0,
}

ver_switch = {
    "function_switch": False,
    "flow_switch": False,
    "flow2_switch": False,
    "resultEVSW": False,
    "resultFLSW": False,
    "resultFLSW2": False,
    "median_switch": False,
    "mc_switch": False,
}


adjust_factory = {
    "AC_Factor": 1,
    "AC_Offset": 0,
    "Cdct_Factor": 1,
    "Cdct_Offset": 0,
    "DewPt_Factor": 1,
    "DewPt_Offset": 0,
    "Flow_Clnt_Factor": 1,
    "Flow_Clnt_Offset": 0,
    "Flow_Wtr_Factor": 1,
    "Flow_Wtr_Offset": 0,
    "Heat_Capacity_Factor": 1,
    "Heat_Capacity_Offset": 0,
    "Power_Factor": 1,
    "Power_Offset": 0,
    "Prsr_ClntRtnSpr_Factor": 500,
    "Prsr_ClntRtnSpr_Offset": 0,
    "Prsr_ClntRtn_Factor": 500,
    "Prsr_ClntRtn_Offset": 0,
    "Prsr_ClntSplySpr_Factor": 1600,
    "Prsr_ClntSplySpr_Offset": 0,
    "Prsr_ClntSply_Factor": 1600,
    "Prsr_ClntSply_Offset": 0,
    "Prsr_Flt1Out_Factor": 1600,
    "Prsr_Flt1Out_Offset": 0,
    "Prsr_Flt2Out_Factor": 500,
    "Prsr_Flt2Out_Offset": 0,
    "Prsr_Flt3Out_Factor": 500,
    "Prsr_Flt3Out_Offset": 0,
    "Prsr_Flt4Out_Factor": 500,
    "Prsr_Flt4Out_Offset": 0,
    "Prsr_Flt5Out_Factor": 1600,
    "Prsr_Flt5Out_Offset": 0,
    "Prsr_FltIn_Factor": 1600,
    "Prsr_FltIn_Offset": 0,
    "Prsr_WtrIn_Factor": 1600,
    "Prsr_WtrIn_Offset": 0,
    "Prsr_WtrOut_Factor": 1600,
    "Prsr_WtrOut_Offset": 0,
    "RltHmd_Factor": 1,
    "RltHmd_Offset": 0,
    "Tbd_Factor": 1,
    "Tbd_Offset": 0,
    "Temp_Ambient_Factor": 1,
    "Temp_Ambient_Offset": 0,
    "Temp_ClntRtn_Factor": 1,
    "Temp_ClntRtn_Offset": 0,
    "Temp_ClntSplySpr_Factor": 1,
    "Temp_ClntSplySpr_Offset": 0,
    "Temp_ClntSply_Factor": 1,
    "Temp_ClntSply_Offset": 0,
    "Temp_WaterIn_Factor": 1,
    "Temp_WaterIn_Offset": 0,
    "Temp_WaterOut_Factor": 1,
    "Temp_WaterOut_Offset": 0,
    "WaterPV_Factor": 1,
    "WaterPV_Offset": 0,
    "pH_Factor": 1,
    "pH_Offset": 0,
}

thrshd_factory = {
    "Delay_AC": 10,
    "Delay_ATS_Communication": 10,
    "Delay_Ambient_Sensor_Communication": 10,
    "Delay_Cdct": 0,
    "Delay_ClntFlow": 40,
    "Delay_Conductivity_Sensor_Communication": 10,
    "Delay_Coolant_Flow_Meter_Communication": 10,
    "Delay_EV1": 25,
    "Delay_EV2": 25,
    "Delay_EV3": 25,
    "Delay_EV4": 25,
    "Delay_Inv1_Error": 0,
    "Delay_Inv1_OverLoad": 0,
    "Delay_Inv2_Error": 0,
    "Delay_Inv2_OverLoad": 0,
    "Delay_Inverter1_Communication": 10,
    "Delay_Inverter2_Communication": 10,
    "Delay_Power_Meter_Communication": 10,
    "Delay_PrsrClntRtn": 0,
    "Delay_PrsrClntRtnSpr": 0,
    "Delay_PrsrClntSply": 0,
    "Delay_PrsrClntSplySpr": 0,
    "Delay_PrsrFlt1Out": 0,
    "Delay_PrsrFlt2Out": 0,
    "Delay_PrsrFlt3Out": 0,
    "Delay_PrsrFlt4Out": 0,
    "Delay_PrsrFlt5Out": 0,
    "Delay_PrsrFltIn": 0,
    "Delay_PrsrWaterIn": 0,
    "Delay_PrsrWaterOut": 0,
    "Delay_RltvHmd": 0,
    "Delay_Tbt": 0,
    "Delay_TempAmbient": 0,
    "Delay_TempCds": 0,
    "Delay_TempClntRtn": 0,
    "Delay_TempClntSply": 0,
    "Delay_TempClntSplySply": 0,
    "Delay_TempWaterIn": 0,
    "Delay_TempWaterOut": 0,
    "Delay_Turbidity_Sensor_Communication": 10,
    "Delay_WaterFlow": 0,
    "Delay_WaterPV": 0,
    "Delay_Water_Flow_Meter_Communication": 10,
    "Delay_Water_Leak": 0,
    "Delay_Water_Leak_Broken": 0,
    "Delay_ATS": 60,
    "Delay_pH": 0,
    "Delay_pH_Sensor_Communication": 10,
    "Delay_TempClntSply_broken": 15,
    "Delay_TempClntSplySpr_broken": 15,
    "Delay_TempClntRtn_broken": 15,
    "Delay_TempWaterIn_broken": 15,
    "Delay_TempWaterOut_broken": 15,
    "Delay_PrsrClntSply_broken": 15,
    "Delay_PrsrClntSplySpr_broken": 15,
    "Delay_PrsrClntRtn_broken": 15,
    "Delay_PrsrClntRtnSpr_broken": 15,
    "Delay_PrsrFltIn_broken": 15,
    "Delay_PrsrFlt1Out_broken": 15,
    "Delay_PrsrFlt2Out_broken": 15,
    "Delay_PrsrFlt3Out_broken": 15,
    "Delay_PrsrFlt4Out_broken": 15,
    "Delay_PrsrFlt5Out_broken": 15,
    "Delay_PrsrWaterIn_broken": 15,
    "Delay_PrsrWaterOut_broken": 15,
    "Delay_Clnt_Flow_broken": 15,
    "Delay_Wtr_Flow_broken": 15,
    "Delay_level1_error": 0,
    "Delay_level2_error": 0,
    "Delay_level3_error": 0,
    "Delay_power1_error": 0,
    "Delay_power2_error": 0,
    "Thr_A_AC_H": 45,
    "Thr_A_Cdct_H": 4700,
    "Thr_A_Cdct_L": 4000,
    "Thr_A_ClntFlow": 20,
    "Thr_A_PrsrClntRtn": 200,
    "Thr_A_PrsrClntRtnSpr": 200,
    "Thr_A_PrsrClntSply": 400,
    "Thr_A_PrsrClntSplySpr": 400,
    "Thr_A_PrsrFlt1Out_H": 200,
    "Thr_A_PrsrFlt2Out_H": 200,
    "Thr_A_PrsrFlt3Out_H": 200,
    "Thr_A_PrsrFlt4Out_H": 200,
    "Thr_A_PrsrFlt5Out_H": 200,
    "Thr_A_PrsrFltIn_H": 550,
    "Thr_A_PrsrWaterIn": 800,
    "Thr_A_PrsrWaterOut": 800,
    "Thr_A_RltvHmd_H": 80,
    "Thr_A_RltvHmd_L": 8,
    "Thr_A_Rst_AC_H": 40,
    "Thr_A_Rst_Cdct_H": 4650,
    "Thr_A_Rst_Cdct_L": 4100,
    "Thr_A_Rst_ClntFlow": 25,
    "Thr_A_Rst_PrsrClntRtn": 150,
    "Thr_A_Rst_PrsrClntRtnSpr": 150,
    "Thr_A_Rst_PrsrClntSply": 350,
    "Thr_A_Rst_PrsrClntSplySpr": 350,
    "Thr_A_Rst_PrsrFlt1Out_H": 150,
    "Thr_A_Rst_PrsrFlt2Out_H": 150,
    "Thr_A_Rst_PrsrFlt3Out_H": 150,
    "Thr_A_Rst_PrsrFlt4Out_H": 150,
    "Thr_A_Rst_PrsrFlt5Out_H": 150,
    "Thr_A_Rst_PrsrFltIn_H": 500,
    "Thr_A_Rst_PrsrWaterIn": 750,
    "Thr_A_Rst_PrsrWaterOut": 750,
    "Thr_A_Rst_RltvHmd_H": 75,
    "Thr_A_Rst_RltvHmd_L": 8.5,
    "Thr_A_Rst_Tbt_H": 11,
    "Thr_A_Rst_Tbt_L": 2,
    "Thr_A_Rst_TempAmbient_H": 40,
    "Thr_A_Rst_TempAmbient_L": 23,
    "Thr_A_Rst_TempCds": 2.5,
    "Thr_A_Rst_TempClntRtn": 60,
    "Thr_A_Rst_TempClntSply": 60,
    "Thr_A_Rst_TempClntSplySpr": 60,
    "Thr_A_Rst_TempWaterIn_H": 40,
    "Thr_A_Rst_TempWaterIn_L": 10,
    "Thr_A_Rst_TempWaterOut_H": 45,
    "Thr_A_Rst_TempWaterOut_L": 10,
    "Thr_A_Rst_WaterFlow": 25,
    "Thr_A_Rst_pH_H": 7.9,
    "Thr_A_Rst_pH_L": 7.2,
    "Thr_A_Tbt_H": 15,
    "Thr_A_Tbt_L": 1,
    "Thr_A_TempAmbient_H": 45,
    "Thr_A_TempAmbient_L": 18,
    "Thr_A_TempCds": 2,
    "Thr_A_TempClntRtn": 65,
    "Thr_A_TempClntSply": 65,
    "Thr_A_TempClntSplySpr": 65,
    "Thr_A_TempWaterIn_H": 45,
    "Thr_A_TempWaterIn_L": 5,
    "Thr_A_TempWaterOut_H": 50,
    "Thr_A_TempWaterOut_L": 5,
    "Thr_A_WaterFlow": 20,
    "Thr_A_pH_H": 8,
    "Thr_A_pH_L": 7,
    "Thr_W_AC_H": 40,
    "Thr_W_Cdct_H": 4600,
    "Thr_W_Cdct_L": 4200,
    "Thr_W_ClntFlow": 30,
    "Thr_W_PrsrClntRtn": 150,
    "Thr_W_PrsrClntRtnSpr": 150,
    "Thr_W_PrsrClntSply": 350,
    "Thr_W_PrsrClntSplySpr": 350,
    "Thr_W_PrsrFlt1Out_H": 150,
    "Thr_W_PrsrFlt2Out_H": 150,
    "Thr_W_PrsrFlt3Out_H": 150,
    "Thr_W_PrsrFlt4Out_H": 150,
    "Thr_W_PrsrFlt5Out_H": 150,
    "Thr_W_PrsrFltIn_H": 500,
    "Thr_W_PrsrWaterIn": 750,
    "Thr_W_PrsrWaterOut": 750,
    "Thr_W_RltvHmd_H": 75,
    "Thr_W_RltvHmd_L": 8.5,
    "Thr_W_Rst_AC_H": 35,
    "Thr_W_Rst_Cdct_H": 4500,
    "Thr_W_Rst_Cdct_L": 4300,
    "Thr_W_Rst_ClntFlow": 35,
    "Thr_W_Rst_PrsrClntRtn": 100,
    "Thr_W_Rst_PrsrClntRtnSpr": 100,
    "Thr_W_Rst_PrsrClntSply": 300,
    "Thr_W_Rst_PrsrClntSplySpr": 300,
    "Thr_W_Rst_PrsrFlt1Out_H": 100,
    "Thr_W_Rst_PrsrFlt2Out_H": 100,
    "Thr_W_Rst_PrsrFlt3Out_H": 100,
    "Thr_W_Rst_PrsrFlt4Out_H": 100,
    "Thr_W_Rst_PrsrFlt5Out_H": 100,
    "Thr_W_Rst_PrsrFltIn_H": 450,
    "Thr_W_Rst_PrsrWaterIn": 700,
    "Thr_W_Rst_PrsrWaterOut": 700,
    "Thr_W_Rst_RltvHmd_H": 70,
    "Thr_W_Rst_RltvHmd_L": 9,
    "Thr_W_Rst_Tbt_H": 8,
    "Thr_W_Rst_Tbt_L": 3,
    "Thr_W_Rst_TempAmbient_H": 35,
    "Thr_W_Rst_TempAmbient_L": 25,
    "Thr_W_Rst_TempCds": 5.5,
    "Thr_W_Rst_TempClntRtn": 55,
    "Thr_W_Rst_TempClntSply": 55,
    "Thr_W_Rst_TempClntSplySpr": 55,
    "Thr_W_Rst_TempWaterIn_H": 35,
    "Thr_W_Rst_TempWaterIn_L": 15,
    "Thr_W_Rst_TempWaterOut_H": 40,
    "Thr_W_Rst_TempWaterOut_L": 15,
    "Thr_W_Rst_WaterFlow": 35,
    "Thr_W_Rst_pH_H": 7.8,
    "Thr_W_Rst_pH_L": 7.3,
    "Thr_W_Tbt_H": 10,
    "Thr_W_Tbt_L": 2,
    "Thr_W_TempAmbient_H": 40,
    "Thr_W_TempAmbient_L": 23,
    "Thr_W_TempCds": 5,
    "Thr_W_TempClntRtn": 60,
    "Thr_W_TempClntSply": 60,
    "Thr_W_TempClntSplySpr": 60,
    "Thr_W_TempWaterIn_H": 40,
    "Thr_W_TempWaterIn_L": 10,
    "Thr_W_TempWaterOut_H": 45,
    "Thr_W_TempWaterOut_L": 10,
    "Thr_W_WaterFlow": 30,
    "Thr_W_pH_H": 7.9,
    "Thr_W_pH_L": 7.2,
    "W_TempClntSply_trap": False,
    "A_TempClntSply_trap": False,
    "W_TempClntSplySpr_trap": False,
    "A_TempClntSplySpr_trap": False,
    "W_TempClntRtn_trap": False,
    "A_TempClntRtn_trap": False,
    "W_TempWaterIn_trap": False,
    "A_TempWaterIn_trap": False,
    "W_TempWaterOut_trap": False,
    "A_TempWaterOut_trap": False,
    "W_PrsrClntSply_trap": False,
    "A_PrsrClntSply_trap": False,
    "W_PrsrClntSplySpr_trap": False,
    "A_PrsrClntSplySpr_trap": False,
    "W_PrsrClntRtn_trap": False,
    "A_PrsrClntRtn_trap": False,
    "W_PrsrClntRtnSpr_trap": False,
    "A_PrsrClntRtnSpr_trap": False,
    "W_PrsrFltIn_trap": False,
    "A_PrsrFltIn_trap": False,
    "W_PrsrFlt1Out_trap": False,
    "A_PrsrFlt1Out_trap": False,
    "W_PrsrFlt2Out_trap": False,
    "A_PrsrFlt2Out_trap": False,
    "W_PrsrFlt3Out_trap": False,
    "A_PrsrFlt3Out_trap": False,
    "W_PrsrFlt4Out_trap": False,
    "A_PrsrFlt4Out_trap": False,
    "W_PrsrFlt5Out_trap": False,
    "A_PrsrFlt5Out_trap": False,
    "W_PrsrWaterIn_trap": False,
    "A_PrsrWaterIn_trap": False,
    "W_PrsrWaterOut_trap": False,
    "A_PrsrWaterOut_trap": False,
    "W_RltvHmd_trap": False,
    "A_RltvHmd_trap": False,
    "W_TempAmbient_trap": False,
    "A_TempAmbient_trap": False,
    "W_TempCds_trap": False,
    "A_TempCds_trap": False,
    "W_ClntFlow_trap": False,
    "A_ClntFlow_trap": False,
    "W_WaterFlow_trap": False,
    "A_WaterFlow_trap": False,
    "W_pH_trap": False,
    "A_pH_trap": False,
    "W_Cdct_trap": False,
    "A_Cdct_trap": False,
    "W_Tbt_trap": False,
    "A_Tbt_trap": False,
    "W_AC_trap": False,
    "A_AC_trap": False,
    "E_WaterPV_trap": False,
    "E_EV1_trap": False,
    "E_EV2_trap": False,
    "E_EV3_trap": False,
    "E_EV4_trap": False,
    "E_Inv1_OverLoad_trap": False,
    "E_Inv2_OverLoad_trap": False,
    "E_Inv1_Error_trap": False,
    "E_Inv2_Error_trap": False,
    "E_Water_Leak_trap": False,
    "E_Water_Leak_Broken_trap": False,
    "E_ATS_trap": False,
    "E_Inverter1_Communication_trap": False,
    "E_Inverter2_Communication_trap": False,
    "E_Ambient_Sensor_Communication_trap": False,
    "E_Coolant_Flow_Meter_Communication_trap": False,
    "E_Water_Flow_Meter_Communication_trap": False,
    "E_Conductivity_Sensor_Communication_trap": False,
    "E_pH_Sensor_Communication_trap": False,
    "E_Turbidity_Sensor_Communication_trap": False,
    "E_ATS_Communication_trap": False,
    "E_Power_Meter_Communication_trap": False,
    "E_TempClntSply_broken_trap": False,
    "E_TempClntSplySpr_broken_trap": False,
    "E_TempClntRtn_broken_trap": False,
    "E_TempWaterIn_broken_trap": False,
    "E_TempWaterOut_broken_trap": False,
    "E_PrsrClntSply_broken_trap": False,
    "E_PrsrClntSplySpr_broken_trap": False,
    "E_PrsrClntRtn_broken_trap": False,
    "E_PrsrClntRtnSpr_broken_trap": False,
    "E_PrsrFltIn_broken_trap": False,
    "E_PrsrFlt1Out_broken_trap": False,
    "E_PrsrFlt2Out_broken_trap": False,
    "E_PrsrFlt3Out_broken_trap": False,
    "E_PrsrFlt4Out_broken_trap": False,
    "E_PrsrFlt5Out_broken_trap": False,
    "E_PrsrWaterIn_broken_trap": False,
    "E_PrsrWaterOut_broken_trap": False,
    "E_Clnt_Flow_broken_trap": False,
    "E_Wtr_Flow_broken_trap": False,
    "E_Low_Coolant_Level_Warning_trap": False,
    "E_Inv1_error_code_trap": False,
    "E_Inv2_error_code_trap": False,
    "E_pc1_error_trap": False,
    "E_pc2_error_trap": False,
    "E_level1_error_trap": False,
    "E_level2_error_trap": False,
    "E_level3_error_trap": False,
    "E_power1_error_trap": False,
    "E_power2_error_trap": False,
    "E_plc_trap": False,
}


pid_factory = {
    "temperature": {
        "sample_time_temp": 100,
        "kp_temp": 50,
        "ki_time_temp": 10,
        "kd_temp": 0,
        "kd_time_temp": 0,
    },
    "pressure": {
        "sample_time_pressure": 20,
        "kp_pressure": 800,
        "ki_time_pressure": 10,
        "kd_pressure": 0,
        "kd_time_pressure": 0,
    },
}

key_mapping = {
    "Temp_ClntSply_broken": "temp_clntSply",
    "Temp_ClntSplySpr_broken": "temp_clntSplySpr",
    "Temp_ClntRtn_broken": "temp_clntRtn",
    "Temp_WaterIn_broken": "temp_waterIn",
    "Temp_WaterOut_broken": "temp_waterOut",
    "Prsr_ClntSply_broken": "prsr_clntSply",
    "Prsr_ClntSplySpr_broken": "prsr_clntSplySpr",
    "Prsr_ClntRtn_broken": "prsr_clntRtn",
    "Prsr_ClntRtnSpr_broken": "prsr_clntRtnSpr",
    "Prsr_FltIn_broken": "prsr_fltIn",
    "Prsr_Flt1Out_broken": "prsr_flt1Out",
    "Prsr_Flt2Out_broken": "prsr_flt2Out",
    "Prsr_Flt3Out_broken": "prsr_flt3Out",
    "Prsr_Flt4Out_broken": "prsr_flt4Out",
    "Prsr_Flt5Out_broken": "prsr_flt5Out",
    "Prsr_WtrIn_broken": "prsr_wtrIn",
    "Prsr_WtrOut_broken": "prsr_wtrOut",
    "water_pv": "WaterPV",
    "rltHmd": "rltHmd",
    "temp_ambient": "temp_ambient",
    "dewPt": "dewPt",
    "f1": "flow_clnt",
    "f2": "flow_wtr",
    "pH": "pH",
    "cdct": "cdct",
    "tbd": "tbd",
    "power": "power",
    "p1_speed": "inv1_freq",
    "p2_speed": "inv2_freq",
    "AC": "AC",
    "heat_capacity": "heat_capacity",
}

inspection_value = {
    "Temp_ClntSply_broken": 0,
    "Temp_ClntSplySpr_broken": 0,
    "Temp_ClntRtn_broken": 0,
    "Temp_WaterIn_broken": 0,
    "Temp_WaterOut_broken": 0,
    "Prsr_ClntSply_broken": 0,
    "Prsr_ClntSplySpr_broken": 0,
    "Prsr_ClntRtn_broken": 0,
    "Prsr_ClntRtnSpr_broken": 0,
    "Prsr_FltIn_broken": 0,
    "Prsr_Flt1Out_broken": 0,
    "Prsr_Flt2Out_broken": 0,
    "Prsr_Flt3Out_broken": 0,
    "Prsr_Flt4Out_broken": 0,
    "Prsr_Flt5Out_broken": 0,
    "Prsr_WtrIn_broken": 0,
    "Prsr_WtrOut_broken": 0,
    "Clnt_Flow_broken": 0,
    "Wtr_Flow_broken": 0,
    "water_pv": 0,
    "rltHmd": 0,
    "temp_ambient": 0,
    "dewPt": 0,
    "f1": 0,
    "f2": 0,
    "pH": 0,
    "cdct": 0,
    "tbd": 0,
    "power": 0,
    "p1_speed": 0,
    "p2_speed": 0,
    "AC": 0,
    "heat_capacity": 0,
}

measure_data = {
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
}

result_data = {
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
    "f2": [],
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
    "force_change_mode": False,
    "inspect_finish": 3,
    "inspect_time": "",
}

inspection_time_last_check = {"current_time": ""}

light_mark = {
    "warning": False,
    "alert": False,
    "error": False,
}

progress_data = {
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
}


pid_setting = {
    "temperature": {
        "sample_time_temp": 0,
        "kp_temp": 0,
        "ki_time_temp": 0,
        "kd_temp": 0,
        "kd_time_temp": 0,
    },
    "pressure": {
        "sample_time_pressure": 0,
        "kp_pressure": 0,
        "ki_time_pressure": 0,
        "kd_pressure": 0,
        "kd_time_pressure": 0,
    },
}


inspection_time = {
    "ev_open_time": 0,
    "water_open_time": 0,
    "pump_open_time": 0,
    "communication_check_time": 0,
}

pid_order = {
    "pressure": [
        "sample_time_pressure",
        "kp_pressure",
        "ki_time_pressure",
        "kd_pressure",
        "kd_time_pressure",
    ],
    "temperature": [
        "sample_time_temp",
        "kp_temp",
        "ki_time_temp",
        "kd_temp",
        "kd_time_temp",
    ],
}

ctr_alt_mod_set_data = {
    "value": {
        "oil_temp_set": 0,
        "oil_pressure_set": 0,
    },
}

ctr_pump_data = {
    "value": {
        "pump1_speed": 0,
        "pump2_speed": 0,
    },
}

ctr_waterPV_data = {
    "value": {
        "water_PV": 0,
    },
}

auto_setting = {"auto_water": 0, "auto_pump": 0, "auto_dew_point": 0}

valve_setting = {"t1": 0, "ta": 0}

system_data = {
    "value": {
        "unit": "metric",
        "last_unit": "metric",
    }
}

FW_Info = {
    "SN": "ABC-1234",
    "Model": "800KW",
    "Version": "1",
    "UI": "240229-1",
    "PC": "240229-2",
    "PLC": "240229-3",
}

TIMEOUT_Info = {"timeoutLight": 60}
all_network_set = [
    {
        "v4dhcp_en": "",
        "IPv4Address": "",
        "v4Subnet": "",
        "v4DefaultGateway": "",
        "v4AutoDNS": "",
        "v4DNSPrimary": "",
        "v4DNSOther": "",
        "v6dhcp_en": "",
        "IPv6Address": "",
        "v6Subnet": "",
        "v6DefaultGateway": "",
        "v6AutoDNS": "",
        "v6DNSPrimary": "",
        "v6DNSOther": "",
    },
    {
        "v4dhcp_en": "",
        "IPv4Address": "",
        "v4Subnet": "",
        "v4DefaultGateway": "",
        "v4AutoDNS": "",
        "v4DNSPrimary": "",
        "v4DNSOther": "",
        "v6dhcp_en": "",
        "IPv6Address": "",
        "v6Subnet": "",
        "v6DefaultGateway": "",
        "v6AutoDNS": "",
        "v6DNSPrimary": "",
        "v6DNSOther": "",
    },
    {
        "v4dhcp_en": "",
        "IPv4Address": "",
        "v4Subnet": "",
        "v4DefaultGateway": "",
        "v4AutoDNS": "",
        "v4DNSPrimary": "",
        "v4DNSOther": "",
        "v6dhcp_en": "",
        "IPv6Address": "",
        "v6Subnet": "",
        "v6DefaultGateway": "",
        "v6AutoDNS": "",
        "v6DNSPrimary": "",
        "v6DNSOther": "",
    },
    {
        "v4dhcp_en": "",
        "IPv4Address": "",
        "v4Subnet": "",
        "v4DefaultGateway": "",
        "v4AutoDNS": "",
        "v4DNSPrimary": "",
        "v4DNSOther": "",
        "v6dhcp_en": "",
        "IPv6Address": "",
        "v6Subnet": "",
        "v6DefaultGateway": "",
        "v6AutoDNS": "",
        "v6DNSPrimary": "",
        "v6DNSOther": "",
    },
]

read_data = {
    "status": False,
    "systemset": False,
    "control": False,
    "engineerMode": False,
}


sensor_map = {
    "temp_clntSply": "Coolant Supply Temperature (T1)",
    "temp_clntSplySpr": "Coolant Supply Temperature (Spare) (T1 sp)",
    "temp_clntRtn": "Coolant Return Temperature (T2)",
    "prsr_clntSply": "Coolant Supply Pressure (P1)",
    "prsr_clntSplySpr": "Coolant Supply Pressure (Spare) (P1 sp)",
    "prsr_clntRtn": "Coolant Return Pressure (P2)",
    "prsr_clntRtnSpr": "Coolant Return Pressure (Spare) (P2 sp)",
    "prsr_diff": "Differential Pressure (Pd=P1-P2)",
    "flow_clnt": "Coolant Flow Rate (F1)",
    "temp_waterIn": "Facility Water Supply Temperature (T4)",
    "temp_waterOut": "Facility Water Return Temperature (T5)",
    "prsr_wtrIn": "Facility Water Supply Pressure (P10)",
    "prsr_wtrOut": "Facility Water Return Pressure (P11)",
    "flow_wtr": "Facility Water Flow Rate (F2)",
    "temp_ambient": "Ambient Temperature (T a)",
    "rltHmd": "Relative Humidity (RH)",
    "dewPt": "Dew Point Temperature (T Dp)",
    "pH": "pH (PH)",
    "cdct": "Conductivity (CON)",
    "tbd": "Turbidity (Tur)",
    "power": "Instant Power Consumption",
    "heat_capacity": "Heat Capacity",
    "AC": "Average Current",
    "prsr_fltIn": "Filter Inlet Pressure (P3)",
    "prsr_flt1Out": "Filter1 Outlet Pressure (P4)",
    "prsr_flt2Out": "Filter2 Outlet Pressure (P5)",
    "prsr_flt3Out": "Filter3 Outlet Pressure (P6)",
    "prsr_flt4Out": "Filter4 Outlet Pressure (P7)",
    "prsr_flt5Out": "Filter5 Outlet Pressure (P8)",
    "inv1_freq": "Coolant Pump1[%]",
    "inv2_freq": "Coolant Pump2[%]",
    "WaterPV": "Facility Water Proportional Valve 1 (PV1) [%]",
}

ctrl_map = {
    "resultMode": "Mode Selection",
    "resultTemp": "Target Coolant Temperature Setting",
    "resultPressure": "Target Coolant Pressure Setting",
    "resultP1": "Pump1 Speed Setting",
    "resultP2": "Pump2 Speed Setting",
    "resultWater": "Facility Water Proportional Valve 1 Setting (PV1) [%]",
}


logData = {
    "value": {
        "temp_clntSply": 0,
        "temp_clntSplySpr": 0,
        "temp_clntRtn": 0,
        "prsr_clntSply": 0,
        "prsr_clntSplySpr": 0,
        "prsr_clntRtn": 0,
        "prsr_clntRtnSpr": 0,
        "prsr_diff": 0,
        "flow_clnt": 0,
        "temp_waterIn": 0,
        "temp_waterOut": 0,
        "prsr_wtrIn": 0,
        "prsr_wtrOut": 0,
        "flow_wtr": 0,
        "temp_ambient": 0,
        "rltHmd": 0,
        "dewPt": 0,
        "pH": 0,
        "cdct": 0,
        "tbd": 0,
        "power": 0,
        "heat_capacity": 0,
        "AC": 0,
        "prsr_fltIn": 0,
        "prsr_flt1Out": 0,
        "prsr_flt2Out": 0,
        "prsr_flt3Out": 0,
        "prsr_flt4Out": 0,
        "prsr_flt5Out": 0,
        "inv1_freq": 0,
        "inv2_freq": 0,
        "WaterPV": 0,
    },
    "setting": {
        "resultMode": "Manual",
        "resultTemp": 0,
        "resultPressure": 0,
        "resultP1": 0,
        "resultP2": 0,
        "resultWater": 0,
    },
}

setting_limit = {
    "control": {
        "oil_temp_set_up": 0,
        "oil_temp_set_low": 0,
        "oil_pressure_set_up": 0,
        "oil_pressure_set_low": 0,
    }
}

unit_status = {
    "imperial": False,
    "metric": False,
}


sampling_rate = {"number": 15}
user_identity = {"ID": "user"}
collapse_state = {"status": False}

snmp_setting = {
    "trap_ip_address": "",
    "read_community": "",
    "write_community": "",
    "v3_switch": False,
}


def read_net_name():
    net_data = {
        "netname1": "ethernet1",
        "netname2": "ethernet2",
        "netname3": "Wired connection 1",
        "netname4": "Wired connection 2",
    }

    interface_name = [
        value for key, value in net_data.items() if key.startswith("netname")
    ]

    return interface_name


def check_warning_status():
    for base_key in sensorData["warning_notice"].keys():
        high_key = base_key + "_high"
        low_key = base_key + "_low"

        if sensorData["warning"].get(high_key, False) or sensorData["warning"].get(
            low_key, False
        ):
            sensorData["warning_notice"][base_key] = True
        else:
            sensorData["warning_notice"][base_key] = False

    for base_key in sensorData["alert_notice"].keys():
        high_key = base_key + "_high"
        low_key = base_key + "_low"

        if sensorData["alert"].get(high_key, False) or sensorData["alert"].get(
            low_key, False
        ):
            sensorData["alert_notice"][base_key] = True
        else:
            sensorData["alert_notice"][base_key] = False


def parse_nmcli_output(outputs, network_set, is_ipv6=False):
    for output in outputs:
        if output.strip():
            key, value = map(str.strip, output.split(":", 1))

            if is_ipv6:
                if "ipv6.method" in key:
                    network_set["v6dhcp_en"] = value

                elif key.startswith("IP6.ADDRESS"):
                    ip_net = ipaddress.ip_interface(value)
                    network_set["IPv6Address"] = str(ip_net.ip)
                    network_set["v6Subnet"] = str(ip_net.network.prefixlen)

                elif "IP6.GATEWAY" in key:
                    if value == "--":
                        network_set["v6DefaultGateway"] = ""
                    else:
                        network_set["v6DefaultGateway"] = value

                elif "ipv6.ignore-auto-dns" in key:
                    if value == "no":
                        network_set["v6AutoDNS"] = "auto"
                    else:
                        network_set["v6AutoDNS"] = "manual"

                elif "IP6.DNS[1]" in key:
                    network_set["v6DNSPrimary"] = value

                elif "IP6.DNS[2]" in key:
                    network_set["v6DNSOther"] = value

            else:
                if "ipv4.method" in key:
                    network_set["v4dhcp_en"] = value

                elif "IP4.ADDRESS[1]" in key:
                    ip_net = ipaddress.ip_interface(value)
                    network_set["IPv4Address"] = str(ip_net.ip)
                    network_set["v4Subnet"] = str(ip_net.network.netmask)

                elif "IP4.GATEWAY" in key:
                    if value == "--":
                        network_set["v4DefaultGateway"] = ""
                    else:
                        network_set["v4DefaultGateway"] = value

                elif "ipv4.ignore-auto-dns" in key:
                    if value == "no":
                        network_set["v4AutoDNS"] = "auto"
                    else:
                        network_set["v4AutoDNS"] = "manual"

                elif "IP4.DNS[1]" in key:
                    network_set["v4DNSPrimary"] = value

                elif "IP4.DNS[2]" in key:
                    network_set["v4DNSOther"] = value


def get_ethernet_info(interface_name, local_network_set):
    if not onLinux:
        return local_network_set

    command = f'sudo nmcli -f ipv4.method,ip4.ADDRESS,ip4.gateway,ip4.dns,ipv4.ignore-auto-dns con show "{interface_name}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    parse_nmcli_output(result.stdout.splitlines(), local_network_set, is_ipv6=False)

    command = f'sudo nmcli -f ipv6.method,ip6.address,ip6.gateway,ip6.dns,ipv6.ignore-auto-dns con show "{interface_name}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    parse_nmcli_output(result.stdout.splitlines(), local_network_set, is_ipv6=True)

    return local_network_set


def collect_allnetwork_info():
    interface_names = read_net_name()
    network_info_list = []

    for i, interface_name in enumerate(interface_names):
        ethernet_info = get_ethernet_info(interface_name, all_network_set[i])
        network_info_list.append(ethernet_info)

    return network_info_list


def delete_files_in_folder(folder_path):
    if os.path.exists(folder_path):
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    delete_files_in_folder(file_path)
            except (PermissionError, OSError) as e:
                print(f"Error deleting {file_path}: {e}")
                continue
    else:
        print(f"The folder {folder_path} does not exist.")


def delete_old_logs(location, days_to_keep=1100):
    current_time = time.time()

    for subdir in ["error", "operation", "sensor", "journal"]:
        subdir_path = os.path.join(location, subdir)
        if os.path.isdir(subdir_path):
            for root, dirs, files in os.walk(subdir_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > days_to_keep * 86400:
                            os.remove(file_path)
                            print(f"Deleted old log file: {file_path}")


def write_sensor_log():
    try:
        column_names = ["time"] + list(sensor_map.values()) + list(ctrl_map.values())
        log_dir = f"{log_path}/logs/sensor"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = f"{log_dir}/sensor.log.{datetime.now().strftime('%Y-%m-%d')}.csv"
    except Exception as e:
        journal_logger.info(f"create sensor log file error: {e}")

    try:
        if not os.path.exists(log_file):
            os.makedirs(log_dir, exist_ok=True)
        with open(log_file, mode="a", newline="") as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(column_names)
            else:
                with open(log_file, "r") as file:
                    file.seek(0)
                    file.readline()
                    last_log_date = file.readline().split(",")[0]
                    last_log_date = last_log_date.split()[0]

                    current_date = datetime.now().strftime("%Y-%m-%d")

                    if current_date != last_log_date:
                        file.close()

                        log_file = f"{log_dir}/sensor.log.{current_date}.csv"
                        with open(log_file, mode="a", newline="") as new_file:
                            writer = csv.writer(new_file)
                            writer.writerow(column_names)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [timestamp]
                + list(logData["value"].values())
                + list(logData["setting"].values())
            )
    except Exception as e:
        journal_logger.info(f"write sensor log error: {e}")


def load_signal_records():
    try:
        if not os.path.exists(f"{web_path}/json/signal_records.json"):
            with open(f"{web_path}/json/signal_records.json", "w") as file:
                file.write("[]")

        with open(f"{web_path}/json/signal_records.json", "r") as json_file:
            global signal_records
            signal_records = json.load(json_file)
            if len(signal_records) > 500:
                signal_records = signal_records[:500]
                with open(f"{web_path}/json/signal_records.json", "w") as json_file:
                    json.dump(signal_records, json_file, indent=4)
    except FileNotFoundError:
        signal_records = []


def load_downtime_signal_records():
    try:
        if not os.path.exists(f"{web_path}/json/downtime_signal_records.json"):
            with open(f"{web_path}/json/downtime_signal_records.json", "w") as file:
                file.write("[]")

        with open(f"{web_path}/json/downtime_signal_records.json", "r") as json_file:
            global downtime_signal_records
            downtime_signal_records = json.load(json_file)
            if len(downtime_signal_records) > 500:
                downtime_signal_records = downtime_signal_records[:500]
                with open(
                    f"{web_path}/json/downtime_signal_records.json", "w"
                ) as json_file:
                    json.dump(downtime_signal_records, json_file, indent=4)
    except FileNotFoundError:
        downtime_signal_records = []


def save_to_json():
    signal_records.sort(key=lambda x: x["on_time"], reverse=True)
    if not os.path.exists(f"{web_path}/json/signal_records.json"):
        with open(f"{web_path}/json/signal_records.json", "w") as file:
            file.write("[]")

    with open(f"{web_path}/json/signal_records.json", "w") as json_file:
        json.dump(signal_records, json_file, indent=4)


def save_to_downtime_json():
    downtime_signal_records.sort(key=lambda x: x["on_time"], reverse=True)
    if not os.path.exists(f"{web_path}/json/downtime_signal_records.json"):
        with open(f"{web_path}/json/downtime_signal_records.json", "w") as file:
            file.write("[]")

    with open(f"{web_path}/json/downtime_signal_records.json", "w") as json_file:
        json.dump(downtime_signal_records, json_file, indent=4)


def record_signal_on(signal_name, singnal_value):
    load_signal_records()
    max_records_to_check = min(50, len(signal_records))
    for record in signal_records[:max_records_to_check]:
        if (
            record["signal_name"] == signal_name
            and record["on_time"] is not None
            and record["off_time"] is None
        ):
            return

    record = {
        "signal_name": signal_name,
        "on_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "off_time": None,
        "signal_value": singnal_value,
    }
    signal_records.append(record)
    save_to_json()


def record_downtime_signal_on(signal_name, singnal_value):
    load_downtime_signal_records()
    max_records_to_check = min(50, len(downtime_signal_records))
    for record in downtime_signal_records[:max_records_to_check]:
        if (
            record["signal_name"] == signal_name
            and record["on_time"] is not None
            and record["off_time"] is None
        ):
            return

    record = {
        "signal_name": signal_name,
        "on_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "off_time": None,
        "signal_value": singnal_value,
    }
    downtime_signal_records.append(record)
    save_to_downtime_json()


def record_signal_off(signal_name, singnal_value):
    load_signal_records()
    max_records_to_check = min(50, len(signal_records))
    for record in signal_records[:max_records_to_check]:
        if (
            record["signal_name"] == signal_name
            and record["on_time"] is not None
            and record["off_time"] is None
        ):
            record["off_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_to_json()
            break


def record_downtime_signal_off(signal_name, singnal_value):
    load_downtime_signal_records()
    max_records_to_check = min(50, len(downtime_signal_records))
    for record in downtime_signal_records[:max_records_to_check]:
        if (
            record["signal_name"] == signal_name
            and record["on_time"] is not None
            and record["off_time"] is None
        ):
            record["off_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_to_downtime_json()
            break


def delete_old_file():
    log_dir = f"{log_path}/logs"
    current_date = dt.date.today()
    one_year_ago = current_date - dt.timedelta(days=365 * 3)
    for file in glob.glob(os.path.join(log_dir, "*.csv")):
        modified_date = dt.date.fromtimestamp(os.path.getmtime(file))
        if modified_date < one_year_ago:
            os.remove(file)


def change_to_metric():
    key_list = list(thrshd.keys())
    for key in key_list:
        if not key.endswith("_trap") and not key.startswith("Delay_"):
            if "Temp" in key and "TempCds" not in key:
                thrshd[key] = (thrshd[key] - 32) * 5.0 / 9.0

            if "TempCds" in key:
                thrshd[key] = thrshd[key] * 5.0 / 9.0

            if "Prsr" in key:
                thrshd[key] = thrshd[key] * 6.89476

            if "Flow" in key:
                thrshd[key] = thrshd[key] / 0.2642

    registers = []
    index = 0
    thr_reg = (sum(1 for key in thrshd if "Thr_" in key)) * 2

    for key in thrshd.keys():
        value = thrshd[key]
        if index < int(thr_reg / 2):
            word1, word2 = cvt_float_byte(value)
            registers.append(word2)
            registers.append(word1)
        index += 1

    grouped_register = [registers[i : i + 64] for i in range(0, len(registers), 64)]

    i = 0
    for group in grouped_register:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(1000 + i * 64, group)
        except Exception as e:
            print(f"write register thrshd issue:{e}")
            return retry_modbus(1000 + i * 64, group, "register")

        i += 1

    key_list = list(ctr_data["value"].keys())
    for key in key_list:
        if key == "oil_temp_set":
            ctr_data["value"]["oil_temp_set"] = (
                (ctr_data["value"]["oil_temp_set"] - 32) / 9.0 * 5.0
            )

        if key == "oil_pressure_set":
            ctr_data["value"]["oil_pressure_set"] = (
                ctr_data["value"]["oil_pressure_set"] * 6.89476
            )

    temp1, temp2 = cvt_float_byte(ctr_data["value"]["oil_temp_set"])
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(993, [temp2, temp1])
            client.write_registers(226, [temp2, temp1])
    except Exception as e:
        print(f"write oil temp error:{e}")
        return retry_modbus_2reg(993, [temp2, temp1], 226, [temp2, temp1])

    prsr1, prsr2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(991, [prsr2, prsr1])
            client.write_registers(224, [prsr2, prsr1])
    except Exception as e:
        print(f"write oil pressure error:{e}")
        return retry_modbus_2reg(991, [prsr2, prsr1], 224, [prsr2, prsr1])

    key_list = list(measure_data.keys())
    for key in key_list:
        if "Temp" in key:
            measure_data[key] = (measure_data[key] - 32) * 5.0 / 9.0

        if "Prsr" in key:
            measure_data[key] = measure_data[key] * 6.89476

        if "f1" in key or "f2" in key:
            measure_data[key] = measure_data[key] / 0.2642
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            for i, (key, value) in enumerate(measure_data.items()):
                word1, word2 = cvt_float_byte(value)
                registers = [word2, word1]
                client.write_registers(901 + i * 2, registers)
    except Exception as e:
        print(f"measure data input error:{e}")
        return retry_modbus(901 + i * 2, registers, "register")

    t1 = round((float(valve_setting["t1"]) - 32) * 5.0 / 9.0)
    ta = round((float(valve_setting["ta"]) - 32) * 5.0 / 9.0)

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(980, [t1, ta])
    except Exception as e:
        print(f"write t1 and ta:{e}")
        return retry_modbus(980, [t1, ta], "register")


def change_to_imperial():
    key_list = list(thrshd.keys())
    for key in key_list:
        if not key.endswith("_trap") and not key.startswith("Delay_"):
            if "Temp" in key and "TempCds" not in key:
                thrshd[key] = thrshd[key] * 9.0 / 5.0 + 32.0

            if "TempCds" in key:
                thrshd[key] = thrshd[key] * 9.0 / 5.0

            if "Prsr" in key:
                thrshd[key] = thrshd[key] * 0.145038

            if "Flow" in key:
                thrshd[key] = thrshd[key] * 0.2642

    registers = []
    index = 0
    thr_count = sum(1 for key in thrshd if "Thr_" in key)

    for key in thrshd.keys():
        value = thrshd[key]
        if index < thr_count:
            word1, word2 = cvt_float_byte(value)
            registers.append(word2)
            registers.append(word1)
        index += 1

    grouped_register = [registers[i : i + 64] for i in range(0, len(registers), 64)]

    i = 0
    for group in grouped_register:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(1000 + i * 64, group)
        except Exception as e:
            print(f"write register thrshd issue:{e}")
            return retry_modbus(1000 + i * 64, group, "register")
        i += 1

    try:
        word1, word2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(224, [word2, word1])
    except Exception as e:
        print(f"write oil pressure error:{e}")
        return retry_modbus(224, [word2, word1], "register")

    try:
        word1, word2 = cvt_float_byte(ctr_data["value"]["oil_temp_set"])
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(226, [word2, word1])
    except Exception as e:
        print(f"write oil pressure error:{e}")
        return retry_modbus(226, [word2, word1], "register")

    key_list = list(ctr_data["value"].keys())
    for key in key_list:
        if key == "oil_temp_set":
            ctr_data["value"]["oil_temp_set"] = (
                ctr_data["value"]["oil_temp_set"] * 9.0 / 5.0 + 32.0
            )

        if key == "oil_pressure_set":
            ctr_data["value"]["oil_pressure_set"] = (
                ctr_data["value"]["oil_pressure_set"] * 0.145038
            )

    temp1, temp2 = cvt_float_byte(ctr_data["value"]["oil_temp_set"])
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(993, [temp2, temp1])
    except Exception as e:
        print(f"write oil temp error:{e}")
        return retry_modbus(993, [temp2, temp1], "register")

    pressure1, pressure2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(991, [pressure2, pressure1])
    except Exception as e:
        print(f"write oil pressure error:{e}")
        return retry_modbus(991, [pressure2, pressure1], "register")

    key_list = list(measure_data.keys())
    for key in key_list:
        if "Temp" in key:
            measure_data[key] = measure_data[key] * 9.0 / 5.0 + 32.0

        if "Prsr" in key:
            measure_data[key] = measure_data[key] * 0.145038

        if "f1" in key or "f2" in key:
            measure_data[key] = measure_data[key] * 0.2642

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            for i, (key, value) in enumerate(measure_data.items()):
                word1, word2 = cvt_float_byte(value)
                registers = [word2, word1]
                client.write_registers(901 + i * 2, registers)
    except Exception as e:
        print(f"measure data input error:{e}")
        return retry_modbus(901 + i * 2, registers, "register")

    t1 = round((valve_setting["t1"]) * 9.0 / 5.0 + 32.0)
    ta = round((valve_setting["ta"]) * 9.0 / 5.0 + 32.0)

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(980, [t1, ta])
    except Exception as e:
        print(f"write t1 and ta:{e}")
        return retry_modbus(980, [t1, ta], "register")


def threshold_import(input):
    for key, value in input.items():
        if key in thrshd:
            thrshd[key] = value

    registers = []
    grouped_register = []
    coil_registers = []
    index = 0
    thr_reg = (sum(1 for key in thrshd if "Thr_" in key)) * 2

    for key in thrshd.keys():
        value = thrshd[key]
        if key.endswith("_trap"):
            coil_registers.append(value)
        else:
            if index < int(thr_reg / 2):
                word1, word2 = cvt_float_byte(value)
                registers.append(word2)
                registers.append(word1)
            else:
                registers.append(int(value))
            index += 1

    grouped_register = [registers[i : i + 64] for i in range(0, len(registers), 64)]

    i = 0
    for group in grouped_register:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(1000 + i * 64, group)
        except Exception as e:
            print(f"write register thrshd issue:{e}")
            return retry_modbus(1000 + i * 64, group, "register")
        i += 1

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coils((8192 + 2000), coil_registers)
    except Exception as e:
        print(f"write trap error: {e}")
        return retry_modbus((8192 + 2000), coil_registers, "coil")

    for key in thrshd.keys():
        value = thrshd[key]
        op_logger.info("%s: %s", key, value)

    return "Setting Successful"


def adjust_import(input):
    for key, value in input.items():
        if key in sensor_adjust:
            sensor_adjust[key] = value

    registers = []

    for key in sensor_adjust.keys():
        value = sensor_adjust[key]
        word1, word2 = cvt_float_byte(value)
        registers.append(word2)
        registers.append(word1)
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(1400, registers)
    except Exception as e:
        print(f"write sensor adjust error:{e}")
        return retry_modbus(1400, registers, "register")

    op_logger.info("Sensor Adjust Inputs received Successfully")

    return "Inputs received successfully"


def valve_import(data):
    registers = [data["ambient"], data["coolant"]]
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(980, registers)
    except Exception as e:
        print(f"write sensor adjust error:{e}")
        return retry_modbus(980, registers, "register")

    op_logger.info(
        "When Dew Point Error, Not Close Water Proportional Valve Condition Inputs received successfully"
    )
    return "Inputs received successfully"


def auto_import(data):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(960, int(data["pv1"]))
            client.write_register(961, int(data["pump"]))
            client.write_register(974, int(data["water_min"]))

    except Exception as e:
        print(f"auto setting:{e}")
        return retry_modbus_3reg(
            960, int(data["pv1"]), 961, int(data["pump"]), 974, int(data["water_min"])
        )

    op_logger.info(
        "Auto Mode Redundant Sensor Broken Setting Inputs received successfully"
    )
    return "Inputs received successfully"


def pid_import(data):
    for key in data.keys():
        if key in pid_order:
            register = []
            sample_time = (
                data[key]["sample_time_temp"]
                if key == "temperature"
                else data[key]["sample_time_pressure"]
            )
            start_address = 550 if key == "temperature" else 510
            sample_time_address = start_address
            data_start_address = start_address + 3

            for pid_key in pid_order[key]:
                if pid_key in data[key]:
                    if (
                        not pid_key == "sample_time_pressure"
                        and not pid_key == "sample_time_temp"
                    ):
                        register.append(int(data[key][pid_key]))
            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    client.write_register(sample_time_address, sample_time)
                    client.write_registers(data_start_address, register)
            except Exception as e:
                print(f"write pid data error:{e}")
                return retry_modbus(data_start_address, register, "register")


def unit_import(data):
    if data == "metric":
        coil_value = False
    elif data == "imperial":
        coil_value = True

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil(address=(8192 + 500), value=coil_value)
    except Exception as e:
        print(f"write in unit error:{e}")
        return retry_modbus((8192 + 500), coil_value, "coil")

    change_data_by_unit()


def close_valve_import(data):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil(address=(8192 + 515), value=data)
            ctr_data["stop_valve_close"] = data
    except Exception as e:
        print(f"close valve error:{e}")
        return retry_modbus((8192 + 515), data, "coil")


def log_interval_import(data):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(3000, data)

        return "Log Interval Updated Successfully"
    except Exception as e:
        print(f"error:{e}")


def snmp_import(data):
    with open(f"{snmp_path}/snmp/snmp.json", "w") as json_file:
        json.dump(data, json_file)


def network_set_import(interface_name, input):
    try:
        if input["v4dhcp_en"] == "auto":
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv4.method",
                    "auto",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv4.addresses",
                    "",
                    "ipv4.gateway",
                    "",
                ],
                check=True,
            )
        elif input["v4dhcp_en"] == "manual":
            mask = input["v4Subnet"]
            network = ipaddress.IPv4Network("0.0.0.0/" + mask, strict=False)

            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv4.method",
                    "manual",
                    "ipv4.address",
                    f"{input['IPv4Address']}/{network.prefixlen}",
                    "ipv4.gateway",
                    input["v4DefaultGateway"],
                ],
                check=True,
            )

        if input["v4AutoDNS"] == "auto":
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.dns", ""],
                check=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv4.ignore-auto-dns",
                    "no",
                ],
                check=True,
            )
        elif input["v4AutoDNS"] == "manual":
            dns_servers = []
            if input["v4DNSPrimary"]:
                dns_servers.append(input["v4DNSPrimary"])
            if input["v4DNSOther"]:
                dns_servers.append(input["v4DNSOther"])

            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv4.ignore-auto-dns",
                    "yes",
                ],
                check=True,
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.dns", ""],
                check=True,
            )
            if dns_servers:
                dns_servers_str = " ".join(dns_servers)
                print("Setting DNS servers to:", dns_servers_str)
                subprocess.run(
                    [
                        "sudo",
                        "nmcli",
                        "con",
                        "mod",
                        interface_name,
                        "ipv4.dns",
                        dns_servers_str,
                    ],
                    check=True,
                )

        if input["v6dhcp_en"] == "auto":
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv6.method",
                    "auto",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv6.addresses",
                    "",
                    "ipv6.gateway",
                    "",
                ],
                check=True,
            )
        elif input["v6dhcp_en"] == "manual":
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv6.method",
                    "manual",
                    "ipv6.address",
                    f"{input['IPv6Address']}/{input['v6Subnet']}",
                    "ipv6.gateway",
                    input["v6DefaultGateway"],
                ],
                check=True,
            )

        if input["v6AutoDNS"] == "auto":
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv6.dns", ""],
                check=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv6.ignore-auto-dns",
                    "no",
                ],
                check=True,
            )
        elif input["v6AutoDNS"] == "manual":
            dns_servers = []
            if input["v6DNSPrimary"]:
                dns_servers.append(input["v6DNSPrimary"])
            if input["v6DNSOther"]:
                dns_servers.append(input["v6DNSOther"])

            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv6.ignore-auto-dns",
                    "yes",
                ],
                check=True,
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv6.dns", ""],
                check=True,
            )
            if dns_servers:
                dns_servers_str = " ".join(dns_servers)
                print("Setting DNS servers to:", dns_servers_str)
                subprocess.run(
                    [
                        "sudo",
                        "nmcli",
                        "con",
                        "mod",
                        interface_name,
                        "ipv6.dns",
                        dns_servers_str,
                    ],
                    check=True,
                )

        subprocess.run(
            ["sudo", "systemctl", "restart", "NetworkManager"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def read_unit():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            r = client.read_coils(address=(8192 + 500), count=1)

            if r.bits[0]:
                system_data["value"]["unit"] = "imperial"
                ctr_data["unit"]["unit_temp"] = "°F"
                ctr_data["unit"]["unit_prsr"] = "psi"
            else:
                system_data["value"]["unit"] = "metric"
                ctr_data["unit"]["unit_temp"] = "°C"
                ctr_data["unit"]["unit_prsr"] = "kPa"

            if r.bits[0]:
                setting_limit["control"]["oil_temp_set_up"] = 55.0 * 9.0 / 5.0 + 32.0
                setting_limit["control"]["oil_temp_set_low"] = 35.0 * 9.0 / 5.0 + 32.0
                setting_limit["control"]["oil_pressure_set_up"] = 750 * 0.145038
                setting_limit["control"]["oil_pressure_set_low"] = 0
            else:
                setting_limit["control"]["oil_temp_set_up"] = 55.0
                setting_limit["control"]["oil_temp_set_low"] = 35.0
                setting_limit["control"]["oil_pressure_set_up"] = 750
                setting_limit["control"]["oil_pressure_set_low"] = 0
    except Exception as e:
        print(f"unit error:{e}")


def read_rack_status():
    host = {
        "rack1_register": "192.168.3.20",
        "rack2_register": "192.168.3.21",
        "rack3_register": "192.168.3.22",
        "rack4_register": "192.168.3.23",
        "rack5_register": "192.168.3.24",
        "rack6_register": "192.168.3.25",
        "rack7_register": "192.168.3.26",
        "rack8_register": "192.168.3.27",
        "rack9_register": "192.168.3.28",
        "rack10_register": "192.168.3.29",
        "rack1_coil": "192.168.3.10",
        "rack2_coil": "192.168.3.11",
        "rack3_coil": "192.168.3.12",
        "rack4_coil": "192.168.3.13",
        "rack5_coil": "192.168.3.14",
        "rack6_coil": "192.168.3.15",
        "rack7_coil": "192.168.3.16",
        "rack8_coil": "192.168.3.17",
        "rack9_coil": "192.168.3.18",
        "rack10_coil": "192.168.3.19",
    }

    while True:
        if ctr_data["rack_visibility"]["rack1_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack1_register"], port=modbus_port, timeout=0.5
                ) as client_rack1_reg:
                    r = client_rack1_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack1_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack1_status"] < 0:
                        sensorData["rack_status"]["rack1_status"] = 0
                    sensorData["rack_no_connection"]["rack1_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack1_status"] = True
                print(f"rack1 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack1_coil"], port=modbus_port, timeout=0.5
                ) as client_rack1_coil:
                    r = client_rack1_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack1_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack1_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack1_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack1_leak"] = True
                print(f"rack1 reg error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack1_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 720), [False])
            except Exception as e:
                print(f"rack1 set control error: {e}")

        if ctr_data["rack_visibility"]["rack2_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack2_register"], port=modbus_port, timeout=0.5
                ) as client_rack2_reg:
                    r = client_rack2_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack2_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack2_status"] < 0:
                        sensorData["rack_status"]["rack2_status"] = 0
                    sensorData["rack_no_connection"]["rack2_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack2_status"] = True
                print(f"rack2 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack2_coil"], port=modbus_port, timeout=0.5
                ) as client_rack2_coil:
                    r = client_rack2_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack2_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack2_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack2_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack2_leak"] = True
                print(f"rack2 reg error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack2_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 721), [False])
            except Exception as e:
                print(f"rack2 set control error: {e}")

        if ctr_data["rack_visibility"]["rack3_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack3_register"], port=modbus_port, timeout=0.5
                ) as client_rack3_reg:
                    r = client_rack3_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack3_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack3_status"] < 0:
                        sensorData["rack_status"]["rack3_status"] = 0
                    sensorData["rack_no_connection"]["rack3_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack3_status"] = True
                print(f"rack3 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack3_coil"], port=modbus_port, timeout=0.5
                ) as client_rack3_coil:
                    r = client_rack3_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack3_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack3_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack3_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack3_leak"] = True
                print(f"rack3 reg error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack3_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 722), [False])
            except Exception as e:
                print(f"rack3 set control error: {e}")

        if ctr_data["rack_visibility"]["rack4_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack4_register"], port=modbus_port, timeout=0.5
                ) as client_rack4_reg:
                    r = client_rack4_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack4_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack4_status"] < 0:
                        sensorData["rack_status"]["rack4_status"] = 0
                    sensorData["rack_no_connection"]["rack4_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack4_status"] = True
                print(f"rack4 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack4_coil"], port=modbus_port, timeout=0.5
                ) as client_rack4_coil:
                    r = client_rack4_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack4_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack4_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack4_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack4_leak"] = True
                print(f"rack4 coil error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack4_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 723), [False])
            except Exception as e:
                print(f"rack4 set control error: {e}")

        if ctr_data["rack_visibility"]["rack5_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack5_register"], port=modbus_port, timeout=0.5
                ) as client_rack5_reg:
                    r = client_rack5_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack5_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack5_status"] < 0:
                        sensorData["rack_status"]["rack5_status"] = 0
                    sensorData["rack_no_connection"]["rack5_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack5_status"] = True
                print(f"rack5 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack5_coil"], port=modbus_port, timeout=0.5
                ) as client_rack5_coil:
                    r = client_rack5_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack5_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack5_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack5_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack5_leak"] = True
                print(f"rack5 coil error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack5_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 724), [False])
            except Exception as e:
                print(f"rack5 set control error: {e}")

        if ctr_data["rack_visibility"]["rack6_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack6_register"], port=modbus_port, timeout=0.5
                ) as client_rack6_reg:
                    r = client_rack6_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack6_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack6_status"] < 0:
                        sensorData["rack_status"]["rack6_status"] = 0
                    sensorData["rack_no_connection"]["rack6_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack6_status"] = True
                print(f"rack6 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack6_coil"], port=modbus_port, timeout=0.5
                ) as client_rack6_coil:
                    r = client_rack6_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack6_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack6_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack6_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack6_leak"] = True
                print(f"rack6 coil error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack5_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 725), [False])
            except Exception as e:
                print(f"rack5 set control error: {e}")

        if ctr_data["rack_visibility"]["rack7_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack7_register"], port=modbus_port, timeout=0.5
                ) as client_rack7_reg:
                    r = client_rack7_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack7_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack7_status"] < 0:
                        sensorData["rack_status"]["rack7_status"] = 0
                    sensorData["rack_no_connection"]["rack7_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack7_status"] = True
                print(f"rack7 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack7_coil"], port=modbus_port, timeout=0.5
                ) as client_rack7_coil:
                    r = client_rack7_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack7_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack7_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack7_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack7_leak"] = True
                print(f"rack7 coil error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack7_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 726), [False])
            except Exception as e:
                print(f"rack7 set control error: {e}")

        if ctr_data["rack_visibility"]["rack8_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack8_register"], port=modbus_port, timeout=0.5
                ) as client_rack8_reg:
                    r = client_rack8_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack8_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack8_status"] < 0:
                        sensorData["rack_status"]["rack8_status"] = 0
                    sensorData["rack_no_connection"]["rack8_status"] = False

            except Exception as e:
                sensorData["rack_no_connection"]["rack8_status"] = True
                print(f"rack8 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack8_coil"], port=modbus_port, timeout=0.5
                ) as client_rack8_coil:
                    r = client_rack8_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack8_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack8_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack8_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack8_leak"] = True
                print(f"rack8 coil error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack8_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 727), [False])
            except Exception as e:
                print(f"rack8 set control error: {e}")

        if ctr_data["rack_visibility"]["rack9_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack9_register"], port=modbus_port, timeout=0.5
                ) as client_rack9_reg:
                    r = client_rack9_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack9_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack9_status"] < 0:
                        sensorData["rack_status"]["rack9_status"] = 0
                    sensorData["rack_no_connection"]["rack9_status"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack9_status"] = True
                print(f"rack9 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack9_coil"], port=modbus_port, timeout=0.5
                ) as client_rack9_coil:
                    r = client_rack9_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack9_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack9_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack9_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack9_leak"] = True
                print(f"rack9 coil error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack9_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 728), [False])
            except Exception as e:
                print(f"rack9 set control error: {e}")

        if ctr_data["rack_visibility"]["rack10_enable"]:
            try:
                with ModbusTcpClient(
                    host=host["rack10_register"], port=modbus_port, timeout=0.5
                ) as client_rack10_reg:
                    r = client_rack10_reg.read_holding_registers(0, 1)
                    result = r.registers[0]
                    sensorData["rack_status"]["rack10_status"] = (
                        (result - 39321) / 26214 * 100
                    )
                    if sensorData["rack_status"]["rack10_status"] < 0:
                        sensorData["rack_status"]["rack10_status"] = 0
                    sensorData["rack_no_connection"]["rack10_status"] = False

            except Exception as e:
                sensorData["rack_no_connection"]["rack10_status"] = True
                print(f"rack10 reg error: {e}")
                pass

            try:
                with ModbusTcpClient(
                    host=host["rack10_coil"], port=modbus_port, timeout=0.5
                ) as client_rack10_coil:
                    r = client_rack10_coil.read_coils(0, 2)
                    sensorData["rack_leak"]["rack10_leak"] = r.bits[0]
                    sensorData["rack_broken"]["rack10_broken"] = r.bits[1]
                    sensorData["rack_no_connection"]["rack10_leak"] = False
            except Exception as e:
                sensorData["rack_no_connection"]["rack10_leak"] = True
                print(f"rack10 coil error: {e}")
                pass

            try:
                if sensorData["rack_leak"]["rack10_leak"]:
                    with ModbusTcpClient(host="192.168.3.250", port=502) as client:
                        client.write_coils((8192 + 729), [False])
            except Exception as e:
                print(f"rack10 set control error: {e}")

        time.sleep(1)


def many_client(host):
    try:
        client = ModbusTcpClient(host=host, port=modbus_port)
        return client
    except Exception as e:
        print(f"rack setting error: {e}")
        return None


def change_to_adjust(key):
    except_key = [
        "relative_humid_low",
        "relative_humid_high",
        "dew_point_temp_low",
        "clnt_flow_low",
        "wtr_flow_low",
        "ph_low",
        "ph_high",
        "cndct_low",
        "cndct_high",
    ]

    if key in except_key:
        if "ph" in key:
            return "pH_Factor"
        elif "clnt_flow_low" in key:
            return "Flow_Clnt_Factor"
        elif "wtr_flow_low" in key:
            return "Flow_Wtr_Factor"
        elif "dew_point_temp_low" in key:
            return "DewPt_Factor"
        elif "relative_humid" in key:
            return "RltHmd_Factor"
        elif "cndct" in key:
            return "Cdct_Factor"

    if key.endswith("_high"):
        new_key = key.replace("_high", "_Factor")
    elif key.endswith("_low"):
        new_key = key.replace("_low", "_Factor")

    parts = new_key.split("_")
    new_key = "_".join(part[0].upper() + part[1:] for part in parts)

    return new_key


def retry_modbus(address, value, method, max_retries=3):
    attempt = 0

    while attempt < max_retries:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                if method == "register":
                    client.write_registers(address, value)
                elif method == "coil":
                    client.write_coils(address, value)
                return True
        except Exception as e:
            attempt += 1
            print(f"Write attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Write failed.")
                return jsonify(
                    {
                        "status": "error",
                        "title": "Error",
                        "message": "Writing failed",
                    }
                )


def retry_modbus_both(address_reg, value_reg, address_coil, value_coil, max_retries=3):
    attempt = 0

    while attempt < max_retries:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(address_reg, value_reg)
                client.write_coils(address_coil, value_coil)
                return True
        except Exception as e:
            attempt += 1
            print(f"Write attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Write failed.")
                return jsonify(
                    {
                        "status": "error",
                        "title": "Error",
                        "message": "Writing failed",
                    }
                )


def retry_modbus_2reg(
    address_reg1, value_reg1, address_reg2, value_reg2, max_retries=3
):
    attempt = 0

    while attempt < max_retries:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(address_reg1, value_reg1)
                client.write_registers(address_reg2, value_reg2)
                return True
        except Exception as e:
            attempt += 1
            print(f"Write attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Write failed.")
                return jsonify(
                    {
                        "status": "error",
                        "title": "Error",
                        "message": "Writing failed",
                    }
                )


def retry_modbus_3reg(
    address_reg1,
    value_reg1,
    address_reg2,
    value_reg2,
    address_reg3,
    value_reg3,
    max_retries=3,
):
    attempt = 0

    while attempt < max_retries:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(address_reg1, value_reg1)
                client.write_registers(address_reg2, value_reg2)
                client.write_registers(address_reg3, value_reg3)
                return True
        except Exception as e:
            attempt += 1
            print(f"Write attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Write failed.")
                return jsonify(
                    {
                        "status": "error",
                        "title": "Error",
                        "message": "Writing failed",
                    }
                )


def retry_modbus_2coil(
    address_coil1, value_coil1, address_coil2, value_coil2, max_retries=3
):
    attempt = 0

    while attempt < max_retries:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils(address_coil1, value_coil1)
                client.write_coils(address_coil2, value_coil2)
                return True
        except Exception as e:
            attempt += 1
            print(f"Write attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Write failed.")
                return jsonify(
                    {
                        "status": "error",
                        "title": "Error",
                        "message": "Writing failed",
                    }
                )


def retry_modbus_setmode_singlecoil(address_coil, value_coil, max_retries=3):
    attempt = 0

    while attempt < max_retries:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils(address_coil, value_coil)
                return True
        except Exception as e:
            attempt += 1
            print(f"Write attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Write failed.")
                return False


def retry_modbus_setmode(
    address_coil1, value_coil1, address_coil2, value_coil2, max_retries=3
):
    attempt = 0

    while attempt < max_retries:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils(address_coil1, value_coil1)
                client.write_coils(address_coil2, value_coil2)
                return True
        except Exception as e:
            attempt += 1
            print(f"Write attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print("Max retries reached. Write failed.")
                return False


def update_json_restore_times():
    try:
        if not os.path.exists(f"{web_path}/json/signal_records.json"):
            with open(f"{web_path}/json/signal_records.json", "w") as file:
                file.write("[]")
        with open(f"{web_path}/json/signal_records.json", "r") as file:
            data = json.load(file)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for entry in data:
            if entry["off_time"] is None:
                entry["off_time"] = current_time

        with open(f"{web_path}/json/signal_records.json", "w") as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        print(f"更新 JSON 文件時發生錯誤: {e}")
    try:
        if not os.path.exists(f"{web_path}/json/downtime_signal_records.json"):
            with open(f"{web_path}/json/downtime_signal_records.json", "w") as file:
                file.write("[]")
        with open(f"{web_path}/json/downtime_signal_records.json", "r") as file:
            data = json.load(file)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for entry in data:
            if entry["off_time"] is None:
                entry["off_time"] = current_time

        with open(f"{web_path}/json/downtime_signal_records.json", "w") as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        print(f"更新 JSON 文件時發生錯誤: {e}")


def change_data_by_unit():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            last_unit = client.read_coils((8192 + 501), 1, unit=modbus_slave_id)
            current_unit = client.read_coils((8192 + 500), 1, unit=modbus_slave_id)

            last_unit = last_unit.bits[0]
            current_unit = current_unit.bits[0]

            if current_unit:
                system_data["value"]["unit"] = "imperial"
            else:
                system_data["value"]["unit"] = "metric"

            if last_unit:
                system_data["value"]["last_unit"] = "imperial"
            else:
                system_data["value"]["last_unit"] = "metric"

            print(f"{last_unit} -> {current_unit}")

            if current_unit and current_unit != last_unit:
                change_to_imperial()
            elif not current_unit and current_unit != last_unit:
                change_to_metric()

            client.write_coils((8192 + 501), [current_unit])

    except Exception as e:
        print(f"unit set error:{e}")
        return retry_modbus((8192 + 501), [current_unit], "coil")


def return_to_manual_when_logout():
    try:
        with ModbusTcpClient(port=modbus_port, host=modbus_host) as client:
            r = client.read_coils((8192 + 516), 1)
            if r.bits[0]:
                client.write_coils((8192 + 516), [False])
                client.write_coils((8192 + 505), [True])
    except Exception as e:
        print(f"return to manual error:{e}")
        retry_modbus_2coil((8192 + 516), [False], (8192 + 505), [True])


def cvt_registers_to_float(reg1, reg2):
    temp1 = [reg1, reg2]
    decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
        temp1, byteorder=Endian.Big, wordorder=Endian.Little
    )
    decoded_value_big_endian = decoder_big_endian.decode_32bit_float()
    return decoded_value_big_endian


def combine_bits(lower, upper):
    value = (upper << 16) | lower
    return value


def read_split_register(r, i):
    lower_16 = r[i]
    upper_16 = r[i + 1]
    value = combine_bits(lower_16, upper_16)
    return value


def cvt_float_byte(value):
    float_as_bytes = struct.pack(">f", float(value))
    word1, word2 = struct.unpack(">HH", float_as_bytes)
    return word1, word2


def set_mode(value_to_write):
    coil_value = False

    if value_to_write == "auto":
        coil_value = False
    elif value_to_write == "manual":
        coil_value = True
    else:
        coil_value = True
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil((8192 + 505), coil_value)
    except Exception as e:
        print(f"set op mode:{e}")
        return retry_modbus_setmode_singlecoil((8192 + 505), coil_value)

    if value_to_write == "engineer":
        coil_value = True
    else:
        coil_value = False
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil((8192 + 516), coil_value)
    except Exception as e:
        print(f"set engineer mode:{e}")
        return retry_modbus_setmode_singlecoil((8192 + 516), coil_value)

    if value_to_write == "inspection":
        coil_value = True
    else:
        coil_value = False
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil((8192 + 517), coil_value)
    except Exception as e:
        print(f"set inspection mode:{e}")
        return retry_modbus_setmode_singlecoil((8192 + 517), coil_value)

    if value_to_write == "auto":
        coil_value = True
    elif value_to_write == "manual":
        coil_value = True
    elif value_to_write == "stop":
        coil_value = False
    elif value_to_write == "engineer":
        coil_value = True
    elif value_to_write == "inspection":
        coil_value = True
    else:
        coil_value = False

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil(address=(8192 + 514), value=coil_value)
            client.write_coil((8192 + 600), result_data["force_change_mode"])
    except Exception as e:
        print(f"setting force change mode and set mode error:{e}")
        return retry_modbus_setmode(
            (8192 + 514), coil_value, (8192 + 600), result_data["force_change_mode"]
        )

    op_logger.info("Mode Updated Successfully. Mode: %s", value_to_write)
    return True


def set_p1(word1, word2):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(246, [word2, word1])
            p1 = cvt_registers_to_float(word2, word1)
        op_logger.info("Pump Speed 1 Updated Successfully. Pump1 Speed: %s", p1)
    except Exception as e:
        print(f"pump speed setting error:{e}")
        return retry_modbus(246, [word2, word1], "register")


def set_p2(word1, word2):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(222, [word2, word1])
            p2 = cvt_registers_to_float(word2, word1)
        op_logger.info("Pump Speed 2 Updated Successfully. Pump2 Speed: %s", p2)
    except Exception as e:
        print(f"pump speed setting error:{e}")
        return retry_modbus(222, [word2, word1], "register")


def set_water(water):
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            word1, word2 = cvt_float_byte(float(water))
            client.write_registers(352, [word2, word1])
        op_logger.info(
            "Facility Water Proportional Valve 1 (PV1) Updated Successfully. Facility Water Proportional Valve 1 (PV1): %s",
            water,
        )
    except Exception as e:
        print(f"pump speed setting error:{e}")
        return retry_modbus(352, [word2, word1], "register")


def read_modbus_data():
    global \
        prev_plc_error, \
        light_mark, \
        tcount_log, \
        error_data, \
        pc2_active, \
        previous_alert_states, \
        previous_error_states, \
        previous_warning_states
    current_date = datetime.now().strftime("%Y-%m-%d")
    last_date = datetime.now().strftime("%Y-%m-%d")
    flag = False
    sensorData["error"]["PLC"] = False
    start_time = time.time()
    check_file_age = 0
    plc_status_cnt = 0
    plc_status_cnt = 0
    error_count = 0
    warning_count = 0
    alert_count = 0

    while True:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_holding_registers(0, 10)
                if r.isError():
                    journal_logger.info(f"connect error: {r}")
                    raise Exception("error occured")
                sensorData["error"]["PLC"] = False
                record_signal_off(
                    sensorData["err_log"]["error"]["PLC"].split()[0],
                    sensorData["err_log"]["error"]["PLC"],
                )
                plc_status_cnt = 0

        except Exception as e:
            if plc_status_cnt < 3:
                plc_status_cnt += 1
            else:
                sensorData["error"]["PLC"] = True
                if sensorData["err_log"]["error"]["PLC"] not in error_data:
                    error_data.append(sensorData["err_log"]["error"]["PLC"])
                app.logger.warning(sensorData["err_log"]["error"]["PLC"])
                record_signal_on(
                    sensorData["err_log"]["error"]["PLC"].split()[0],
                    sensorData["err_log"]["error"]["PLC"],
                )
                print(f"plc connection error: {e}")

            time.sleep(1)
            continue

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_holding_registers(1750, 2)
                inv_error_code["code1"] = r.registers[0]
                inv_error_code["code2"] = r.registers[1]
        except Exception as e:
            print(f"inv error code: {e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_coils((8192 + 700), 2)
                ctr_data["downtime_error"]["oc_issue"] = r.bits[0]
                ctr_data["downtime_error"]["f1_issue"] = r.bits[1]
        except Exception as e:
            print(f"read f1/oc issue error: {e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                value_reg = len(sensorData["value"].keys()) * 2
                result = client.read_holding_registers(
                    5000, value_reg, unit=modbus_slave_id
                )

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    keys_list = list(sensorData["value"].keys())
                    j = 0

                    for i in range(0, value_reg, 2):
                        temp1 = [result.registers[i], result.registers[i + 1]]
                        decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                            temp1, byteorder=Endian.Big, wordorder=Endian.Little
                        )
                        decoded_value_big_endian = (
                            decoder_big_endian.decode_32bit_float()
                        )
                        format_value = decoded_value_big_endian
                        sensorData["value"][keys_list[j]] = format_value
                        j += 1
        except Exception as e:
            print(f"read status data error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_coils((8192 + 10), 2, unit=modbus_slave_id)
                sensorData["ats_status"]["ATS1"] = r.bits[0]
                sensorData["ats_status"]["ATS2"] = r.bits[1]
        except Exception as e:
            print(f"ATS issue:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_discrete_inputs(12, 4, unit=modbus_slave_id)
                sensorData["level_sw"]["level1"] = r.bits[0]
                sensorData["level_sw"]["level2"] = r.bits[1]
                sensorData["level_sw"]["power1"] = r.bits[2]
                sensorData["level_sw"]["power2"] = r.bits[3]

                r2 = client.read_discrete_inputs(18, 1, unit=modbus_slave_id)
                sensorData["level_sw"]["level3"] = r2.bits[0]
        except Exception as e:
            print(f"read level issue:{e}")

        try:
            with open(f"{snmp_path}/PLC/json/pc_status.json", "r") as file:
                pc2_active = json.load(file)
                if pc2_active is None:
                    pc2_active = False
        except Exception as e:
            print(f"read pc1 status error: {e}")
            pc2_active = False

        try:
            with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                r = client.read_coils((8192 + 730), 10, unit=modbus_slave_id)
                for x, key in enumerate(ctr_data["rack_pass"].keys()):
                    ctr_data["rack_pass"][key] = r.bits[x]
        except Exception as e:
            print(f"rack read issue:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_discrete_inputs(4, 12, unit=modbus_slave_id)

                keys = list(sensorData["ev"].keys())
                for i in range(0, 8):
                    sensorData["ev"][keys[i]] = r.bits[i]

                for i in range(1, 5):
                    open_key = f"EV{i}_Open"
                    close_key = f"EV{i}_Close"
                    ev_key = f"EV{i}"
                    if sensorData["ev"][open_key] and not sensorData["ev"][close_key]:
                        sensorData["valve"][ev_key] = "True"
                    elif (
                        not sensorData["ev"][open_key]
                        and not sensorData["ev"][close_key]
                    ):
                        sensorData["valve"][ev_key] = "-"
                    else:
                        sensorData["valve"][ev_key] = "False"
        except Exception as e:
            print(f"read input error {e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_holding_registers(1404, 2, unit=modbus_slave_id)
                r2 = client.read_holding_registers(1424, 2, unit=modbus_slave_id)
                r3 = client.read_holding_registers(1432, 2, unit=modbus_slave_id)

                temp1 = [r.registers[0], r.registers[1]]
                prsr1 = [r2.registers[0], r2.registers[1]]
                p2 = [r3.registers[0], r3.registers[1]]
                decoder_big_endian1 = BinaryPayloadDecoder.fromRegisters(
                    temp1, byteorder=Endian.Big, wordorder=Endian.Little
                )
                decoder_big_endian2 = BinaryPayloadDecoder.fromRegisters(
                    prsr1, byteorder=Endian.Big, wordorder=Endian.Little
                )
                decoder_big_endian3 = BinaryPayloadDecoder.fromRegisters(
                    p2, byteorder=Endian.Big, wordorder=Endian.Little
                )
                temp_spare = decoder_big_endian1.decode_32bit_float()
                prsr_spare = decoder_big_endian2.decode_32bit_float()
                p2_spare = decoder_big_endian3.decode_32bit_float()

                if temp_spare == 0:
                    sensorData["collapse"]["temp_spare"] = False
                else:
                    sensorData["collapse"]["temp_spare"] = True

                if not sensorData["error"]["TempClntSply_broken"]:
                    sensorData["collapse"]["t1_no_error"] = False
                else:
                    sensorData["collapse"]["t1_no_error"] = True

                if prsr_spare == 0:
                    sensorData["collapse"]["prsr_spare"] = False
                else:
                    sensorData["collapse"]["prsr_spare"] = True

                if not sensorData["error"]["PrsrClntSply_broken"]:
                    sensorData["collapse"]["p1_no_error"] = False
                else:
                    sensorData["collapse"]["p1_no_error"] = True

                if p2_spare == 0:
                    sensorData["collapse"]["p2_spare"] = False
                else:
                    sensorData["collapse"]["p2_spare"] = True

                if not sensorData["error"]["PrsrClntRtn_broken"]:
                    sensorData["collapse"]["p2_no_error"] = False
                else:
                    sensorData["collapse"]["p2_no_error"] = True

        except Exception as e:
            print(f"read temp spare adjust error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_coils(address=(8192 + 500), count=1)

                if not result.isError():
                    if result.bits[0]:
                        sensorData["unit"]["unit_temp"] = "°F"
                    else:
                        sensorData["unit"]["unit_temp"] = "°C"

                    if result.bits[0]:
                        sensorData["unit"]["unit_pressure"] = "psi"
                    else:
                        sensorData["unit"]["unit_pressure"] = "kPa"

                    if result.bits[0]:
                        sensorData["unit"]["unit_flow"] = "GPM"
                    else:
                        sensorData["unit"]["unit_flow"] = "LPM"

                    if result.bits[0]:
                        setting_limit["control"]["oil_temp_set_up"] = (
                            55.0 * 9.0 / 5.0 + 32.0
                        )
                        setting_limit["control"]["oil_temp_set_low"] = (
                            35.0 * 9.0 / 5.0 + 32.0
                        )
                        setting_limit["control"]["oil_pressure_set_up"] = 750 * 0.145038
                        setting_limit["control"]["oil_pressure_set_low"] = 0
                    else:
                        setting_limit["control"]["oil_temp_set_up"] = 55.0
                        setting_limit["control"]["oil_temp_set_low"] = 35.0
                        setting_limit["control"]["oil_pressure_set_up"] = 750.0
                        setting_limit["control"]["oil_pressure_set_low"] = 0

        except Exception as e:
            print(f"read unit/oil temp/oil pressure error:{e}")

        tcount_log = time.time() - start_time

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_holding_registers(3000, 1, unit=modbus_slave_id)
        except Exception as e:
            print(f"read sampling rate error:{e}")

        if tcount_log >= sampling_rate["number"]:
            try:
                for key in sensorData["value"]:
                    if key in logData["value"]:
                        new_data_value = round(sensorData["value"][key], 1)
                        logData["value"][key] = new_data_value

                if (
                    sensorData["error"]["PrsrClntSply_broken"]
                    and sensorData["error"]["PrsrClntSplySpr_broken"]
                ):
                    prsr_diff = "-"
                elif sensorData["error"]["PrsrClntSply_broken"]:
                    prsr_diff = (
                        sensorData["value"]["prsr_clntSplySpr"]
                        - sensorData["value"]["prsr_clntRtn"]
                    )
                else:
                    prsr_diff = (
                        sensorData["value"]["prsr_clntSply"]
                        - sensorData["value"]["prsr_clntRtn"]
                    )

                if isinstance(prsr_diff, str):
                    logData["value"]["prsr_diff"] = prsr_diff
                else:
                    logData["value"]["prsr_diff"] = round(prsr_diff, 1)

                for key in ctr_data["value"]:
                    if key in logData["setting"]:
                        if key == "resultMode":
                            logData["setting"][key] = ctr_data["value"][key]
                        else:
                            new_data_setting = round(ctr_data["value"][key], 1)
                            logData["setting"][key] = new_data_setting

                if ver_switch["function_switch"]:
                    logData["value"]["prsr_clntRtnSpr"] = "N/A"

            except Exception as e:
                journal_logger.info(f"write log error: {e}")

            write_sensor_log()
            tcount_log = 0
            start_time = time.time()

        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != last_date:
            delete_old_file()
        last_date = datetime.now().strftime("%Y-%m-%d")

        if check_file_age > 60:
            delete_old_logs(f"{log_path}/logs")
            check_file_age = 0
        check_file_age += 1

        read_unit()
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_coils(address=(8192 + 514), count=1)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    if not result.bits[0]:
                        ctr_data["value"]["resultMode"] = "Stop"
                        ctr_data["value"]["opMod"] = "stop"
                    else:
                        result = client.read_coils(address=(8192 + 516), count=1)

                        if result.bits[0]:
                            ctr_data["value"]["resultMode"] = "Engineer"
                            ctr_data["value"]["opMod"] = "engineer"
                        else:
                            r = client.read_coils(address=(8192 + 517), count=1)

                            if r.bits[0]:
                                ctr_data["value"]["resultMode"] = "Inspection"
                                ctr_data["value"]["opMod"] = "inspection"
                            else:
                                result = client.read_coils(
                                    address=(8192 + 505), count=1
                                )

                                if result.isError():
                                    print(f"Modbus Error: {result}")
                                else:
                                    if not result.bits[0]:
                                        ctr_data["value"]["resultMode"] = "Auto"
                                        ctr_data["value"]["opMod"] = "auto"

                                    else:
                                        ctr_data["value"]["resultMode"] = "Manual"
                                        ctr_data["value"]["opMod"] = "manual"
        except Exception as e:
            print(f"set mode error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_holding_registers(address=993, count=2)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    oil_temp_set = cvt_registers_to_float(
                        result.registers[0], result.registers[1]
                    )
                    ctr_data["value"]["resultTemp"] = oil_temp_set
                    ctr_data["value"]["oil_temp_set"] = oil_temp_set
        except Exception as e:
            print(f"read oil temp error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_holding_registers(address=991, count=2)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    oil_pressure_set = cvt_registers_to_float(
                        result.registers[0], result.registers[1]
                    )
                    ctr_data["value"]["resultPressure"] = oil_pressure_set
                    ctr_data["value"]["oil_pressure_set"] = oil_pressure_set
        except Exception as e:
            print(f"read oil pressure error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_coils(0, 2, unit=modbus_slave_id)
                if not r.isError():
                    ctr_data["inv"]["inv1"] = r.bits[0]
                    ctr_data["inv"]["inv2"] = r.bits[1]
        except Exception as e:
            print(f"read mc error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_holding_registers(address=246, count=2)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    pump1_speed = cvt_registers_to_float(
                        result.registers[0], result.registers[1]
                    )
                    ctr_data["value"]["pump1_speed"] = pump1_speed
        except Exception as e:
            print(f"pump speed1 error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_holding_registers(address=222, count=2)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    pump2_speed = cvt_registers_to_float(
                        result.registers[0], result.registers[1]
                    )

                    if pump1_speed == pump2_speed:
                        pump2_speed = cvt_registers_to_float(
                            result.registers[0], result.registers[1]
                        )
                        ctr_data["value"]["pump2_speed"] = pump2_speed
                    else:
                        if (
                            pump1_speed > 0
                            and ctr_data["value"]["resultMode"] == "Manual"
                            or pump1_speed > 0
                            and ctr_data["value"]["resultMode"] == "Engineer"
                        ):
                            if sensorData["error"]["Inv1_OverLoad"]:
                                ctr_data["value"]["pump2_speed"] = pump2_speed
                            if sensorData["error"]["Inv2_OverLoad"]:
                                try:
                                    client.write_registers(222, [0, 0])
                                    ctr_data["value"]["pump2_speed"] = 0

                                except Exception as e:
                                    print(f"read pump2 speed error:{e}")

                            if (
                                not sensorData["error"]["Inv1_OverLoad"]
                                and not sensorData["error"]["Inv1_OverLoad"]
                            ):
                                try:
                                    client.write_registers(222, [0, 0])
                                    ctr_data["value"]["pump2_speed"] = 0

                                except Exception as e:
                                    print(f"read pump2 speed error:{e}")

                        else:
                            ctr_data["value"]["pump2_speed"] = pump2_speed
        except Exception as e:
            print(f"pump speed2 error:{e}")

        if ctr_data["inv"]["inv1"]:
            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    result = client.read_holding_registers(
                        address=(20480 + 6300), count=1
                    )
                    if result.isError():
                        print(f"Modbus Error: {result}")
                    else:
                        pump1_speed = result.registers[0]
                        pump1_speed = pump1_speed / 16000 * 75 + 25
                        ctr_data["value"]["resultP1"] = round(pump1_speed)
            except Exception as e:
                print(f"pump speed1 error:{e}")
        else:
            ctr_data["value"]["resultP1"] = 0

        if ctr_data["inv"]["inv2"]:
            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    result = client.read_holding_registers(
                        address=(20480 + 6340), count=1
                    )
                    if result.isError():
                        print(f"Modbus Error: {result}")
                    else:
                        pump2_speed = result.registers[0]
                        pump2_speed = pump2_speed / 16000 * 75 + 25
                        ctr_data["value"]["resultP2"] = round(pump2_speed)
            except Exception as e:
                print(f"pump speed2 error:{e}")
        else:
            ctr_data["value"]["resultP2"] = 0

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_holding_registers(address=352, count=2)
                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    water_PV = cvt_registers_to_float(
                        result.registers[0], result.registers[1]
                    )
                    ctr_data["value"]["water_PV"] = water_PV

                r = client.read_holding_registers((20480 + 6380), 1)
                if r.isError():
                    print(f"Modbus Error: {r}")
                else:
                    water = r.registers[0] * 100 / 16000
                    ctr_data["value"]["resultWater"] = round(water)
        except Exception as e:
            print(f"read waterPV error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_holding_registers(address=200, count=2)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    Pump1_run_time = read_split_register(result.registers, 0)
                    ctr_data["text"]["Pump1_run_time"] = Pump1_run_time
        except Exception as e:
            print(f"read pump1 runtime error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_holding_registers(address=202, count=2)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    Pump2_run_time = read_split_register(result.registers, 0)
                    ctr_data["text"]["Pump2_run_time"] = Pump2_run_time
        except Exception as e:
            print(f"read pump2 runtime error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                result = client.read_coils(address=6, count=4, unit=modbus_slave_id)

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    ctr_data["valve"]["resultEV1"] = result.bits[0]
                    ctr_data["valve"]["resultEV2"] = result.bits[1]
                    ctr_data["valve"]["resultEV3"] = result.bits[2]
                    ctr_data["valve"]["resultEV4"] = result.bits[3]
                    ctr_data["valve"]["ev1_sw"] = result.bits[0]
                    ctr_data["valve"]["ev2_sw"] = result.bits[1]
                    ctr_data["valve"]["ev3_sw"] = result.bits[2]
                    ctr_data["valve"]["ev4_sw"] = result.bits[3]
        except Exception as e:
            print(f"read ev error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_coils((8192 + 720), 10)

                for i, (k, v) in enumerate(ctr_data["rack_set"].items()):
                    result_key = k.replace("_sw", "_sw_result")
                    if k.endswith("_sw"):
                        ctr_data["rack_set"][k] = r.bits[i]
                        ctr_data["rack_set"][result_key] = r.bits[i]

        except Exception as e:
            print(f"read rack control: {e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_coils(2, 2, unit=modbus_slave_id)

                if not r.isError():
                    ctr_data["mc"]["mc1_sw"] = r.bits[0]
                    ctr_data["mc"]["mc2_sw"] = r.bits[1]
                    ctr_data["mc"]["resultMC1"] = r.bits[0]
                    ctr_data["mc"]["resultMC2"] = r.bits[1]
        except Exception as e:
            print(f"read mc error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_holding_registers(973, 1)
                ctr_data["inspect_action"] = r.registers[0]

        except Exception as e:
            print(f"read inspect action error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_holding_registers(702, 18, unit=modbus_slave_id)

                j = 0
                for i in range(0, 18, 4):
                    key = f"f{j + 1}"
                    ctr_data["filter"][key] = read_split_register(r.registers, i)
                    j += 1
        except Exception as e:
            print(f"read filter runtime error:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_coils((8192 + 801), 6)
                ver_switch["function_switch"] = r.bits[0]
                ver_switch["resultEVSW"] = r.bits[0]
                ver_switch["flow_switch"] = r.bits[1]
                ver_switch["resultFLSW"] = r.bits[1]
                ver_switch["flow2_switch"] = r.bits[2]
                ver_switch["resultFLSW2"] = r.bits[2]
                ver_switch["median_switch"] = r.bits[3]
                ver_switch["mc_switch"] = r.bits[4]

            if not os.path.exists(f"{web_path}/json/version.json"):
                with open(f"{web_path}/json/version.json", "w") as file:
                    file.write("")
            with open(f"{web_path}/json/version.json", "w") as json_file:
                json.dump(ver_switch, json_file, indent=4)

        except Exception as e:
            print(f"version check error: {e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                adjust_len = len(sensor_adjust.keys()) * 2
                result = client.read_holding_registers(
                    1400, adjust_len, unit=modbus_slave_id
                )

                if result.isError():
                    print(f"Modbus Error: {result}")
                else:
                    keys_list = list(sensor_adjust.keys())
                    j = 0
                    for i in range(0, adjust_len, 2):
                        temp1 = [result.registers[i], result.registers[i + 1]]
                        decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                            temp1, byteorder=Endian.Big, wordorder=Endian.Little
                        )
                        decoded_value_big_endian = (
                            decoder_big_endian.decode_32bit_float()
                        )
                        sensor_adjust[keys_list[j]] = decoded_value_big_endian
                        j += 1
        except Exception as e:
            print(f"read adjust error:{e}")
        error_data.clear()
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                warning_key_len = len(sensorData["warning"].keys())
                warning_reg = (warning_key_len // 16) + (
                    1 if warning_key_len % 16 != 0 else 0
                )
                result = client.read_holding_registers(
                    1700, warning_reg, unit=modbus_slave_id
                )

                if not result.isError():
                    value = (
                        result.registers[0]
                        | result.registers[1] << 16
                        | result.registers[2] << 32
                    )

                    binary_string = bin(value)[2:].zfill(warning_key_len)
                    keys_list = list(sensorData["warning"].keys())
                    index = -1

                    for key in keys_list:
                        sensorData["warning"][key] = bool(int(binary_string[index]))
                        index -= 1

                    if sensor_adjust["Temp_ClntSplySpr_Factor"] == 0:
                        sensorData["warning"]["temp_clntSplySpr_high"] = False

                    if sensor_adjust["Prsr_ClntSplySpr_Factor"] == 0:
                        sensorData["warning"]["prsr_clntSplySpr_high"] = False

                    if sensor_adjust["Prsr_ClntRtnSpr_Factor"] == 0:
                        sensorData["warning"]["prsr_clntRtnSpr_high"] = False

                    if ver_switch["function_switch"]:
                        sensorData["warning"]["prsr_clntRtnSpr_high"] = False

                    adjust_key = change_to_adjust(key)

                    for key in keys_list:
                        if (
                            sensorData["warning"][key]
                            and sensor_adjust[adjust_key] != 0
                        ):
                            if sensorData["err_log"]["warning"][key] not in error_data:
                                error_data.append(sensorData["err_log"]["warning"][key])
                    warning_count += 1

                    if warning_toggle:
                        if warning_count > 10:
                            for key in keys_list:
                                current_state = sensorData["warning"][key]

                                if sensor_adjust[adjust_key] != 0:
                                    if key not in previous_warning_states:
                                        previous_warning_states[key] = False
                                    if (
                                        current_state
                                        and not previous_warning_states[key]
                                    ):
                                        app.logger.warning(
                                            sensorData["err_log"]["warning"][key]
                                        )

                                    elif (
                                        not current_state
                                        and previous_warning_states[key]
                                    ):
                                        app.logger.info(
                                            f"{sensorData['err_log']['warning'][key]} Restore"
                                        )

                                    previous_warning_states[key] = current_state
                            warning_count = 0

                    check_warning_status()

        except Exception as e:
            print(f"read warning error issue:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                alert_key_len = len(sensorData["alert"].keys())
                alert_reg = (alert_key_len // 16) + (
                    1 if alert_key_len % 16 != 0 else 0
                )
                result = client.read_holding_registers(
                    1705, alert_reg, unit=modbus_slave_id
                )

                if not result.isError():
                    value = (
                        result.registers[0]
                        | result.registers[1] << 16
                        | result.registers[2] << 32
                    )
                    binary_string = bin(value)[2:].zfill(alert_key_len)
                    keys_list = list(sensorData["alert"].keys())
                    index = -1

                    for key in keys_list:
                        sensorData["alert"][key] = bool(int(binary_string[index]))
                        index -= 1

                    if sensor_adjust["Temp_ClntSplySpr_Factor"] == 0:
                        sensorData["alert"]["temp_clntSplySpr_high"] = False

                    if sensor_adjust["Prsr_ClntSplySpr_Factor"] == 0:
                        sensorData["alert"]["prsr_clntSplySpr_high"] = False

                    if sensor_adjust["Prsr_ClntRtnSpr_Factor"] == 0:
                        sensorData["alert"]["prsr_clntRtnSpr_high"] = False

                    if ver_switch["function_switch"]:
                        sensorData["alert"]["prsr_clntRtnSpr_high"] = False

                    adjust_key = change_to_adjust(key)

                    for key in keys_list:
                        if sensorData["alert"][key] and sensor_adjust[adjust_key] != 0:
                            if sensorData["err_log"]["alert"][key] not in error_data:
                                error_data.append(sensorData["err_log"]["alert"][key])

                    alert_count += 1

                    if alert_toggle:
                        if alert_count > 10:
                            for key in keys_list:
                                current_state = sensorData["alert"][key]
                                adjust_key = change_to_adjust(key)
                                if sensor_adjust[adjust_key] != 0:
                                    if key not in previous_alert_states:
                                        previous_alert_states[key] = False
                                    if current_state and not previous_alert_states[key]:
                                        app.logger.warning(
                                            sensorData["err_log"]["alert"][key]
                                        )

                                        record_signal_on(
                                            sensorData["err_log"]["alert"][key].split()[
                                                0
                                            ],
                                            sensorData["err_log"]["alert"][key],
                                        )
                                    elif (
                                        not current_state and previous_alert_states[key]
                                    ):
                                        app.logger.info(
                                            f"{sensorData['err_log']['alert'][key]} Restore"
                                        )

                                        record_signal_off(
                                            sensorData["err_log"]["alert"][key].split()[
                                                0
                                            ],
                                            sensorData["err_log"]["alert"][key],
                                        )
                                    previous_alert_states[key] = current_state
                            alert_count = 0

        except Exception as e:
            print(f"read alert error issue:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                err_key_len = len(sensorData["error"].keys()) - 1
                err_reg = (err_key_len // 16) + (1 if err_key_len % 16 != 0 else 0)
                result = client.read_holding_registers(
                    1708, err_reg, unit=modbus_slave_id
                )
                if not result.isError():
                    value = (
                        result.registers[0]
                        | result.registers[1] << 16
                        | result.registers[2] << 32
                        | result.registers[3] << 48
                    )
                    binary_string = bin(value)[2:].zfill(err_key_len)
                    keys_list = list(sensorData["error"].keys())

                    index = -1
                    for key in keys_list:
                        if key != "PLC":
                            sensorData["error"][key] = bool(int(binary_string[index]))
                            index -= 1

                    if inv_error_code["code1"] > 0:
                        sensorData["err_log"]["error"]["Inv1_error_code"] = (
                            f"M341 Inverter1 Error. Error Code: {inv_error_code['code1']}"
                        )

                    if inv_error_code["code2"] > 0:
                        sensorData["err_log"]["error"]["Inv2_error_code"] = (
                            f"M342 Inverter1 Error. Error Code: {inv_error_code['code2']}"
                        )

                    if sensor_adjust["Temp_ClntSplySpr_Factor"] == 0:
                        sensorData["error"]["TempClntSplySpr_broken"] = False

                    if sensor_adjust["Prsr_ClntSplySpr_Factor"] == 0:
                        sensorData["error"]["PrsrClntSplySpr_broken"] = False

                    if sensor_adjust["Prsr_ClntRtnSpr_Factor"] == 0:
                        sensorData["error"]["PrsrClntRtnSpr_broken"] = False

                    if ver_switch["function_switch"]:
                        sensorData["error"]["PrsrClntRtnSpr_broken"] = False
                        sensorData["error"]["level1_error"] = False
                        sensorData["error"]["level2_error"] = False
                        sensorData["error"]["power1_error"] = False
                        sensorData["error"]["power2_error"] = False
                        sensorData["error"]["level3_error"] = False

                    for key in keys_list:
                        if sensorData["error"][key]:
                            if sensorData["err_log"]["error"][key] not in error_data:
                                error_data.append(sensorData["err_log"]["error"][key])
                    error_count += 1

                    if error_toggle:
                        if error_count > 10:
                            for key in keys_list:
                                current_state = sensorData["error"][key]

                                if key not in previous_error_states:
                                    previous_error_states[key] = False

                                if current_state and not previous_error_states[key]:
                                    app.logger.warning(
                                        sensorData["err_log"]["error"][key]
                                    )

                                    record_signal_on(
                                        sensorData["err_log"]["error"][key].split()[0],
                                        sensorData["err_log"]["error"][key],
                                    )
                                    if (
                                        sensorData["err_log"]["error"][key].split()[0]
                                        == "M301"
                                        or sensorData["err_log"]["error"][key].split()[
                                            0
                                        ]
                                        == "M302"
                                        or sensorData["err_log"]["error"][key].split()[
                                            0
                                        ]
                                        == "M338"
                                    ):
                                        record_downtime_signal_on(
                                            sensorData["err_log"]["error"][key].split()[
                                                0
                                            ],
                                            sensorData["err_log"]["error"][key],
                                        )

                                elif not current_state and previous_error_states[key]:
                                    app.logger.info(
                                        f"{sensorData['err_log']['error'][key]} Restore"
                                    )

                                    record_signal_off(
                                        sensorData["err_log"]["error"][key].split()[0],
                                        sensorData["err_log"]["error"][key],
                                    )
                                    if (
                                        sensorData["err_log"]["error"][key].split()[0]
                                        == "M301"
                                        or sensorData["err_log"]["error"][key].split()[
                                            0
                                        ]
                                        == "M302"
                                        or sensorData["err_log"]["error"][key].split()[
                                            0
                                        ]
                                        == "M338"
                                    ):
                                        record_downtime_signal_off(
                                            sensorData["err_log"]["error"][key].split()[
                                                0
                                            ],
                                            sensorData["err_log"]["error"][key],
                                        )
                                previous_error_states[key] = current_state
                            error_count = 0

        except Exception as e:
            print(f"read error issue:{e}")

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_coils((8192 + 710), 10, unit=modbus_slave_id)
                for i, (k, v) in enumerate(ctr_data["rack_visibility"].items()):
                    ctr_data["rack_visibility"][k] = r.bits[i]

        except Exception as e:
            print(f"read rack enable error:{e}")

        read_data["control"] = False

        if read_data["engineerMode"]:
            read_unit()
            try:
                thr_reg = (sum(1 for key in thrshd if "Thr_" in key)) * 2
                delay_reg = sum(1 for key in thrshd if "Delay_" in key)
                trap_reg = sum(1 for key in thrshd if "_trap" in key)
                start_address = 1000
                total_registers = thr_reg
                read_num = 120

                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    for counted_num in range(0, total_registers, read_num):
                        count = min(read_num, total_registers - counted_num)
                        result = client.read_holding_registers(
                            start_address + counted_num, count, unit=modbus_slave_id
                        )

                        if result.isError():
                            print(f"Modbus Errorxxx: {result}")
                            continue
                        else:
                            keys_list = list(thrshd.keys())
                            j = counted_num // 2
                            for i in range(0, count, 2):
                                if i + 1 < len(result.registers) and j < len(keys_list):
                                    temp1 = [
                                        result.registers[i],
                                        result.registers[i + 1],
                                    ]
                                    decoder_big_endian = (
                                        BinaryPayloadDecoder.fromRegisters(
                                            temp1,
                                            byteorder=Endian.Big,
                                            wordorder=Endian.Little,
                                        )
                                    )
                                    decoded_value_big_endian = (
                                        decoder_big_endian.decode_32bit_float()
                                    )
                                    thrshd[keys_list[j]] = decoded_value_big_endian
                                    j += 1

                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    result = client.read_holding_registers(
                        1000 + thr_reg, delay_reg, unit=modbus_slave_id
                    )

                    if result.isError():
                        print(f"Modbus Error: {result}")
                    else:
                        keys_list = list(thrshd.keys())
                        j = int(thr_reg / 2)
                        for i in range(0, delay_reg):
                            thrshd[keys_list[j]] = result.registers[i]
                            j += 1

                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_coils((8192 + 2000), trap_reg)

                    if r.isError():
                        print(f"Modbus Error: {r}")
                    else:
                        keys_list = list(thrshd.keys())
                        j = int(thr_reg / 2 + delay_reg)
                        for i in range(0, trap_reg):
                            thrshd[keys_list[j]] = r.bits[i]
                            j += 1

                    with open(f"{web_path}/json/thrshd.json", "w") as json_file:
                        json.dump(thrshd, json_file)
            except Exception as e:
                print(f"read thrshd error:{e}")
                flag = True

            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_holding_registers(510, 1, unit=modbus_slave_id)

                    pid_setting["pressure"]["sample_time_pressure"] = r.registers[0]
                    result = client.read_holding_registers(513, 4, unit=modbus_slave_id)

                    key_list = list(pid_setting["pressure"].keys())
                    y = 0
                    for i in range(1, 5):
                        pid_setting["pressure"][key_list[i]] = result.registers[y]
                        y += 1
            except Exception as e:
                print(f"read pid pressure error:{e}")
                flag = True

            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_holding_registers(550, 1, unit=modbus_slave_id)

                    pid_setting["temperature"]["sample_time_temp"] = r.registers[0]
                    result = client.read_holding_registers(553, 4, unit=modbus_slave_id)

                    key_list = list(pid_setting["temperature"].keys())
                    y = 0
                    for i in range(1, 5):
                        pid_setting["temperature"][key_list[i]] = result.registers[y]
                        y += 1
            except Exception as e:
                print(f"read pid temp error:{e}")
                flag = True

            with open(f"{web_path}/json/pid_setting.json", "w") as json_file:
                json.dump(pid_setting, json_file)

            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_holding_registers(740, 4, unit=modbus_slave_id)

                    keys = list(inspection_time.keys())
                    for i in range(4):
                        inspection_time[keys[i]] = r.registers[i]

            except Exception as e:
                print(f"read inspection time error:{e}")
                flag = True

            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_holding_registers(960, 2, unit=modbus_slave_id)

                    auto_setting["auto_water"] = r.registers[0]
                    auto_setting["auto_pump"] = r.registers[1]
            except Exception as e:
                print(f"read auto setting error:{e}")
                flag = True
            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_holding_registers(974, 1, unit=modbus_slave_id)

                    auto_setting["auto_dew_point"] = r.registers[0]
            except Exception as e:
                print(f"read auto setting error:{e}")
                flag = True

            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_holding_registers(980, 2, unit=modbus_slave_id)

                    valve_setting["t1"] = r.registers[0]
                    valve_setting["ta"] = r.registers[1]

                    with open(f"{web_path}/json/valve_setting.json", "w") as json_file:
                        json.dump(valve_setting, json_file, indent=4)

            except Exception as e:
                print(f"read valve setting error:{e}")
                flag = True

        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                r = client.read_holding_registers(3000, 1, unit=modbus_slave_id)

                sampling_rate["number"] = r.registers[0]
        except Exception as e:
            print(f"read sample time error:{e}")

        if read_data["systemset"]:
            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    result = client.read_coils(address=(8192 + 500), count=1)

                    if result.bits[0]:
                        system_data["value"]["unit"] = "imperial"
                    else:
                        system_data["value"]["unit"] = "metric"

            except Exception as e:
                print(f"unit error:{e}")

            read_data["systemset"] = False

        read_data["engineerMode"] = flag

        flag = False

        try:
            if not os.path.exists(f"{web_path}/json/sensor_data.json"):
                with open(f"{web_path}/json/sensor_data.json", "w") as file:
                    file.write("")
            with open(f"{web_path}/json/sensor_data.json", "w") as json_file:
                json.dump(sensorData, json_file, indent=4)
        except Exception as e:
            print(f"sensor_data.json:{e}")

        try:
            if not os.path.exists(f"{web_path}/json/ctr_data.json"):
                with open(f"{web_path}/json/ctr_data.json", "w") as file:
                    file.write("")
            with open(f"{web_path}/json/ctr_data.json", "w") as json_file2:
                json.dump(ctr_data, json_file2, indent=4)
        except Exception as e:
            print(f"ctr_data.json:{e}")

        try:
            if not os.path.exists(f"{web_path}/json/system_data.json"):
                with open(f"{web_path}/json/system_data.json", "w") as file:
                    file.write("")

            with open(f"{web_path}/json/system_data.json", "w") as json_file3:
                json.dump(system_data, json_file3, indent=4)
        except Exception as e:
            print(f"system_data.json:{e}")

        try:
            if not os.path.exists(f"{web_path}/json/measure_data.json"):
                with open(f"{web_path}/json/measure_data.json", "w") as file:
                    file.write("")
            with open(f"{web_path}/json/measure_data.json", "w") as json_file3:
                json.dump(measure_data, json_file3, indent=4)
        except Exception as e:
            print(f"measure_data.json:{e}")

        time.sleep(0.9)


@app.route("/")
def login_page():
    return render_template("login.html")


@app.route("/status")
@login_required
def statusEngineer():
    return render_template(
        "status_Engineer.html",
        user=current_user.id,
    )


@app.route("/api/status")
def api_status():
    try:
        # Note: In production, add @login_required. For dev/demo, allowing loose access to facilitate Vue dev server.
        # But if we use session auth, we need credentials passed.
        with open(f"{web_path}/json/measure_data.json", "r") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download_logs")
@login_required
def download_logs():
    files = os.listdir(f"{log_path}/logs")
    print(files)
    return render_template("download.html", files=files, user=current_user.id)


@app.route("/download_logs/<path:filename>")
@login_required
def download(filename):
    return send_from_directory(f"{log_path}/logs", filename, as_attachment=True)


@app.route("/sensor_logs")
@login_required
def sensor_logs():
    directory = f"{log_path}/logs/sensor"
    if not os.path.exists(directory):
        os.makedirs(directory)
    files = os.listdir(f"{log_path}/logs/sensor")

    files = [f for f in files if not (f.startswith(".__") or f == ".DS_Store")]

    sorted_files = sorted(
        files, key=lambda x: x.split(".")[-2].split(".")[0], reverse=True
    )

    return render_template("sensorLog.html", files=sorted_files, user=current_user.id)


@app.route("/sensor_logs/<path:filename>")
@login_required
def download_sensor_logs(filename):
    return send_from_directory(f"{log_path}/logs/sensor", filename, as_attachment=True)


@app.route("/operation_logs")
@login_required
def operation_logs():
    directory = f"{log_path}/logs/operation"
    if not os.path.exists(directory):
        os.makedirs(directory)
    files = os.listdir(f"{log_path}/logs/operation")

    files = [f for f in files if not (f.startswith(".__") or f == ".DS_Store")]
    sorted_files = sorted(
        files,
        key=lambda x: (x != "oplog.log", x.split(".")[-1] if x != "oplog.log" else ""),
        reverse=True,
    )
    if "oplog.log" in sorted_files:
        sorted_files.insert(0, sorted_files.pop(sorted_files.index("oplog.log")))

    return render_template(
        "operationLog.html", files=sorted_files, user=current_user.id
    )


@app.route("/operation_logs/<path:filename>")
@login_required
def download_operation_logs(filename):
    return send_from_directory(
        f"{log_path}/logs/operation", filename, as_attachment=True
    )


@app.route("/operation_logs_restapi")
@login_required
def operation_logs_restapi():
    directory = f"{snmp_path}/RestAPI/logs/operation"
    if not os.path.exists(directory):
        os.makedirs(directory)
    files = os.listdir(f"{snmp_path}/RestAPI/logs/operation")

    files = [f for f in files if not (f.startswith(".__") or f == ".DS_Store")]
    sorted_files = sorted(
        files,
        key=lambda x: (
            x != "oplog_api.log",
            x.split(".")[-1] if x != "oplog_api.log" else "",
        ),
        reverse=True,
    )
    if "oplog_api.log" in sorted_files:
        sorted_files.insert(0, sorted_files.pop(sorted_files.index("oplog_api.log")))

    return render_template(
        "operationLogRestAPI.html", files=sorted_files, user=current_user.id
    )


@app.route("/operation_logs_restapi/<path:filename>")
@login_required
def download_operation_logs_restapi(filename):
    return send_from_directory(
        f"{snmp_path}/RestAPI/logs/operation", filename, as_attachment=True
    )


@app.route("/error_logs")
@login_required
def error_logs():
    directory = f"{log_path}/logs/error"
    if not os.path.exists(directory):
        os.makedirs(directory)
    files = os.listdir(f"{log_path}/logs/error")

    files = [f for f in files if not (f.startswith(".__") or f == ".DS_Store")]

    sorted_files = sorted(
        files,
        key=lambda x: (
            x != "errorlog.log",
            x.split(".")[-1] if x != "errorlog.log" else "",
        ),
        reverse=True,
    )

    if "errorlog.log" in sorted_files:
        sorted_files.insert(0, sorted_files.pop(sorted_files.index("errorlog.log")))

    return render_template("errorLog.html", files=sorted_files, user=current_user.id)


@app.route("/error_logs/<path:filename>")
@login_required
def download_error_logs(filename):
    return send_from_directory(f"{log_path}/logs/error", filename, as_attachment=True)


@app.route("/logout")
@login_required
def logout():
    return_to_manual_when_logout()

    logout_user()
    session.pop("username", None)
    return redirect("/")


@app.route("/network")
@login_required
def network():
    return render_template("network.html", user=current_user.id)


@app.route("/error_logs_table")
@login_required
def error_logs_table():
    return render_template("errorLogTable.html", user=current_user.id)


@app.route("/systemset")
@login_required
def systemset():
    return render_template("systemSetting.html", user=current_user.id)


@app.route("/fwStatus")
@login_required
def fwStatus():
    return render_template("fwStatus.html", user=current_user.id)


@app.route("/inspection")
@login_required
def inspection():
    return render_template("inspection.html", user=current_user.id)


@app.route("/modbus")
@login_required
def Page():
    return render_template("modbus.html")


@app.route("/engineerMode")
@login_required
def engineerMode():
    return render_template("engineerMode.html", user=current_user.id)


@app.route("/get_data")
@login_required
def get_data():
    keys_list = list(sensorData["value"].keys())

    for key in keys_list:
        if isinstance(sensorData["value"][key], float) and math.isnan(
            sensorData["value"][key]
        ):
            sensorData["value"][key] = 0

    return jsonify(sensorData)


@app.route("/get_data_engineerMode")
@login_required
def get_data_engineerMode():
    read_data["engineerMode"] = True
    timeout = get_data_timeout
    start_time = time.time()
    while read_data["engineerMode"]:
        if time.time() - start_time > timeout:
            read_data["engineerMode"] = False
            return jsonify({"error": "Request timeout"}), 504
        time.sleep(0.5)

    return jsonify(
        {
            "sensor_adjust": sensor_adjust,
            "thrshd": thrshd,
            "pid_pressure": pid_setting["pressure"],
            "pid_temp": pid_setting["temperature"],
            "inspection_time": inspection_time,
            "auto_setting": auto_setting,
            "visibility": ctr_data["rack_visibility"],
            "valve": valve_setting,
            "ver_switch": ver_switch,
        }
    )


@app.route("/get_data_control")
@login_required
def get_data_control():
    read_data["control"] = True
    timeout = get_data_timeout
    start_time = time.time()
    while read_data["control"]:
        if time.time() - start_time > timeout:
            read_data["control"] = False
            return jsonify({"error": "Request timeout"}), 504
        time.sleep(0.5)

    return jsonify(ctr_data)


@app.route("/get_data_systemset")
@login_required
def get_data_systemset():
    read_data["systemset"] = True
    timeout = get_data_timeout
    start_time = time.time()
    while read_data["systemset"]:
        if time.time() - start_time > timeout:
            read_data["systemset"] = False
            return jsonify({"error": "Request timeout"}), 504
        time.sleep(0.5)

    return jsonify(
        {
            "system_data": system_data,
            "sampling_rate": sampling_rate,
        }
    )


@app.route("/get_data_version")
@login_required
def get_data_version():
    return jsonify(ver_switch)


@app.route("/control")
@login_required
def controlPage():
    return render_template("control.html", user=current_user.id)


@app.route("/set_operation_mode", methods=["POST"])
@login_required
def set_operation_mode():
    data = request.json
    value_to_write = data.get("value")
    result_data["force_change_mode"] = data.get("force_change_mode")
    mode_input = data.get("input")
    message = ""
    p1_flag = False
    p2_flag = False

    water_pv = mode_input["water_pv"]

    if mode_input["selectMode"] == "auto":
        temp = mode_input["temp"]
        prsr = mode_input["prsr"]

        try:
            if system_data["value"]["unit"] == "imperial":
                temp_change = (float(temp) - 32) * 5.0 / 9.0
                prsr_change = float(prsr) * 6.89476

                temp1, temp2 = cvt_float_byte(temp_change)
                prsr1, prsr2 = cvt_float_byte(prsr_change)

                try:
                    with ModbusTcpClient(
                        host=modbus_host, port=modbus_port, unit=modbus_slave_id
                    ) as client:
                        client.write_registers(226, [temp2, temp1])
                        client.write_registers(224, [prsr2, prsr1])
                except Exception as e:
                    print(f"set temp error:{e}")
                    return retry_modbus_2reg(226, [temp2, temp1], 224, [prsr2, prsr1])
            else:
                temp1, temp2 = cvt_float_byte(temp)
                prsr1, prsr2 = cvt_float_byte(prsr)

                try:
                    with ModbusTcpClient(
                        host=modbus_host, port=modbus_port, unit=modbus_slave_id
                    ) as client:
                        client.write_registers(226, [temp2, temp1])
                        client.write_registers(224, [prsr2, prsr1])
                except Exception as e:
                    print(f"set temp error:{e}")
                    return retry_modbus_2reg(226, [temp2, temp1], 224, [prsr2, prsr1])

        except Exception as e:
            print(f"change temp pressure error: {e}")

        if (temp > setting_limit["control"]["oil_temp_set_up"]) or (
            temp < setting_limit["control"]["oil_temp_set_low"]
        ):
            return jsonify(
                {
                    "status": "warning",
                    "title": "Out of Range",
                    "message": "Temperature setting must be between\n35°C and 55°C (95°F to 131°F).",
                }
            )
        word1, word2 = cvt_float_byte(temp)
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(993, [word2, word1])
        except Exception as e:
            print(f"set temp error:{e}")
            return retry_modbus(993, [word2, word1], "register")

        if (
            prsr > setting_limit["control"]["oil_pressure_set_up"]
            or prsr < setting_limit["control"]["oil_pressure_set_low"]
        ):
            return jsonify(
                {
                    "status": "warning",
                    "title": "Out of Range",
                    "message": "Pressure setting must be between\n0 kPa and 750 kPa (0 Psi to 108.75 Psi).",
                }
            )
        word1, word2 = cvt_float_byte(prsr)
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(991, [word2, word1])

        except Exception as e:
            print(f"set pressure error:{e}")
            return retry_modbus(991, [word2, word1], "register")

        if not ctr_data["mc"]["resultMC1"] or not ctr_data["mc"]["resultMC2"]:
            if set_mode(value_to_write):
                return jsonify(
                    {
                        "status": "info",
                        "title": "MC Off Notice",
                        "message": "Please check inverter power",
                    }
                )

        if sensorData["error"]["Inv1_Error"] or sensorData["error"]["Inv2_Error"]:
            if set_mode(value_to_write):
                return jsonify(
                    {
                        "status": "info",
                        "title": "Inverter Notice",
                        "message": "Error inverter unable to power on",
                    }
                )

        op_logger.info("Temperature: %s, Pressure: %s", temp, prsr)

        if set_mode(value_to_write):
            return jsonify(
                {
                    "status": "success",
                    "title": "Success",
                    "message": "Auto mode is activated successfully",
                }
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "title": "Error",
                    "message": "Failed to set mode",
                }
            )

    try:
        if (
            mode_input["selectMode"] == "engineer"
            or mode_input["selectMode"] == "manual"
        ):
            ev1_sw = mode_input.get("ev1")
            ev2_sw = mode_input.get("ev2")
            ev3_sw = mode_input.get("ev3")
            ev4_sw = mode_input.get("ev4")
            pump1_speed = mode_input["p1"]
            pump2_speed = mode_input["p2"]
            inv1_error = sensorData["error"]["Inv1_Error"]
            inv2_error = sensorData["error"]["Inv2_Error"]
            inv1_overload = sensorData["error"]["Inv1_OverLoad"]
            inv2_overload = sensorData["error"]["Inv2_OverLoad"]

            regs = [ev1_sw, ev2_sw, ev3_sw, ev4_sw]

            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    client.write_coils((8192 + 520), regs)
                    op_logger.info(
                        "EV1: %s, EV2: %s, EV3: %s, EV4: %s",
                        regs[0],
                        regs[1],
                        regs[2],
                        regs[3],
                    )
            except Exception as e:
                print(f"ev set error:{e}")
                return retry_modbus((8192 + 520), regs, "coil")

            set_water(water_pv)

            word1, word2 = cvt_float_byte(float(pump1_speed))
            if inv1_overload or inv1_error:
                word2 = 0
                word1 = 0

            word3, word4 = cvt_float_byte(float(pump2_speed))
            if inv2_overload or inv2_error:
                word3 = 0
                word4 = 0

            if pump1_speed > 0 and pump2_speed > 0 and pump1_speed != pump2_speed:
                return jsonify(
                    {
                        "status": "warning",
                        "title": "Warning",
                        "message": "To modify the settings, please set both pump to the same speed.",
                    }
                )

            if (
                inv1_overload
                and inv2_overload
                and not (pump1_speed == 0 and pump2_speed == 0)
            ):
                return jsonify(
                    {
                        "status": "error",
                        "title": "Overcurrent Error",
                        "message": "Both pump can't start due to both inverter overlaod",
                    }
                )

            if (
                inv1_error
                and inv2_error
                and not (pump1_speed == 0 and pump2_speed == 0)
            ):
                return jsonify(
                    {
                        "status": "error",
                        "title": "Inverter Error",
                        "message": "Unable to start pump due to both inverter error",
                    }
                )

            if pump1_speed == 0 and pump2_speed == 0:
                set_p1(0, 0)
                set_p2(0, 0)

            if pump1_speed > 0 and pump2_speed > 0 and pump1_speed == pump2_speed:
                if inv1_overload or inv1_error:
                    set_p2(word3, word4)
                    p1_flag = True
                    message = "Pump Speed 2 Updated Successfully. \nPump 1 failed to start due to inverter error or overload."

                if inv2_overload or inv2_error:
                    set_p1(word1, word2)
                    p2_flag = True
                    message = "Pump Speed 1 Updated Successfully. \nPump 2 failed to start due to inverter error or overload."

                if p1_flag and p2_flag:
                    message = "Unable to start pump due to inverter error or overload"

                if p1_flag or p2_flag:
                    return jsonify(
                        {
                            "status": "error",
                            "title": "Inverter Warning",
                            "message": message,
                        }
                    )
                else:
                    set_p1(word1, word2)
                    set_p2(word3, word4)

            elif pump1_speed > 0 and pump2_speed == 0:
                set_p2(0, 0)
                if inv1_overload or inv1_error:
                    return jsonify(
                        {
                            "status": "error",
                            "title": "Inverter Warning",
                            "message": "Failed to activate pump1 due to inverter1 error or overload",
                        }
                    )
                else:
                    set_p1(word1, word2)

            elif pump1_speed == 0 and pump2_speed > 0:
                set_p1(0, 0)
                if inv2_overload or inv2_error:
                    return jsonify(
                        {
                            "status": "error",
                            "title": "Inverter Warning",
                            "message": "Failed to activate pump2 due to inverter2 error or overload",
                        }
                    )
                else:
                    set_p2(word3, word4)

            if (not ctr_data["mc"]["resultMC1"] and pump1_speed > 0) or (
                not ctr_data["mc"]["resultMC2"] and pump2_speed > 0
            ):
                if set_mode(value_to_write):
                    return jsonify(
                        {
                            "status": "info",
                            "title": "Check MC",
                            "message": "Please check inverter power",
                        }
                    )

            if set_mode(value_to_write):
                if mode_input["selectMode"] == "engineer":
                    return jsonify(
                        {
                            "status": "success",
                            "title": "Success",
                            "message": "Engineer mode is activated successfully",
                        }
                    )
                elif mode_input["selectMode"] == "manual":
                    return jsonify(
                        {
                            "status": "success",
                            "title": "Success",
                            "message": "Manual mode is activated successfully",
                        }
                    )
            else:
                return jsonify(
                    {
                        "status": "error",
                        "title": "Error",
                        "message": "Failed to set mode",
                    }
                )

    except Exception as e:
        print(f"mode setting error：{e}")

    if mode_input["selectMode"] == "stop":
        if set_mode(value_to_write):
            return jsonify(
                {
                    "status": "success",
                    "title": "Success",
                    "message": "Stop mode is activated successfully",
                }
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "title": "Error",
                    "message": "Failed to set mode",
                }
            )

    if mode_input["selectMode"] == "inspection":
        if set_mode(value_to_write):
            return jsonify(
                {
                    "status": "success",
                    "title": "Success",
                    "message": "Inspection mode is activated successfully",
                }
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "title": "Error",
                    "message": "Failed to set mode",
                }
            )


@app.route("/control/auto_mode_set_aply", methods=["POST"])
@login_required
def auto_mode_setting():
    data = request.json
    temperature = data.get("temperature")
    temp = float(temperature)

    if (temp > setting_limit["control"]["oil_temp_set_up"]) or (
        temp < setting_limit["control"]["oil_temp_set_low"]
    ):
        return "Temperature Setting out of range(35~55°C 95~131℉)"
    word1, word2 = cvt_float_byte(temperature)
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(993, [word2, word1])

    except Exception as e:
        print(f"set temp error:{e}")
        return retry_modbus(993, [word2, word1], "register")

    pressure = data.get("pressure")
    prsr = float(pressure)
    if (
        prsr > setting_limit["control"]["oil_pressure_set_up"]
        or prsr < setting_limit["control"]["oil_pressure_set_low"]
    ):
        return "Pressure Setting out of range(0~750 kPa 0~108.75 Psi)"
    word1, word2 = cvt_float_byte(pressure)
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(991, [word2, word1])

    except Exception as e:
        print(f"set pressure error:{e}")
        return retry_modbus(991, [word2, word1], "register")

    op_logger.info("Temperature: %s, Pressure: %s", temperature, pressure)

    return "Temperature and Pressure Setting Successful"


@app.route("/control/auto_mode_set_cnsl")
@login_required
def ctr_alt_mod_cnsl():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            result = client.read_holding_registers(address=993, count=2)

        if result.isError():
            print(f"Modbus Error: {result}")
        else:
            oil_temp_set = cvt_registers_to_float(
                result.registers[0], result.registers[1]
            )
            ctr_alt_mod_set_data["value"]["oil_temp_set"] = oil_temp_set
    except Exception as e:
        print(f"read oil temp error:{e}")

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            result = client.read_holding_registers(address=991, count=2)

        if result.isError():
            print(f"Modbus Error: {result}")
        else:
            oil_pressure_set = cvt_registers_to_float(
                result.registers[0], result.registers[1]
            )
            ctr_alt_mod_set_data["value"]["oil_pressure_set"] = oil_pressure_set
    except Exception as e:
        print(f"pressure error:{e}")

    return jsonify(ctr_alt_mod_set_data)


@app.route("/pump_speed_setting", methods=["POST"])
@login_required
def pump_speed_setting():
    data = request.json

    pump1_speed = data.get("pump1_speed")
    word1, word2 = cvt_float_byte(pump1_speed)
    if sensorData["error"]["Inv1_OverLoad"]:
        word1 = 0
        word2 = 0

    pump2_speed = data.get("pump2_speed")
    word3, word4 = cvt_float_byte(pump2_speed)
    if sensorData["error"]["Inv2_OverLoad"]:
        word1 = 0
        word2 = 0

    if pump1_speed > 0 and pump2_speed > 0 and pump1_speed != pump2_speed:
        return "Please synchronize speeds to run both pumps or change speed."
    else:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(246, [word2, word1])
                client.write_registers(222, [word4, word3])
        except Exception as e:
            print(f"pump speed setting error:{e}")
            return retry_modbus_2reg(246, [word2, word1], 222, [word4, word3])

        if (pump1_speed == 0 and pump2_speed == 0) or (
            ctr_data["value"]["resultP1"] == 0 and ctr_data["value"]["resultP2"] == 0
        ):
            try:
                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    client.write_coils((8192 + 520), [False] * 4)
            except Exception as e:
                print(f"setting ev error:{e}")
                return retry_modbus((8192 + 520), [False] * 4, "coil")

        if ctr_data["value"]["resultMode"] in ["Engineer", "Manual"]:
            if pump1_speed == pump2_speed:
                if sensorData["error"]["Inv1_OverLoad"]:
                    op_logger.info(
                        "Pump1 Speed: %s, Pump2 Speed: %s", pump1_speed, pump2_speed
                    )
                    return "Pump Speed 2 Updated Successfully"
                if sensorData["error"]["Inv2_OverLoad"]:
                    op_logger.info(
                        "Pump1 Speed: %s, Pump2 Speed: %s", pump1_speed, pump2_speed
                    )
                    return "Pump Speed 1 Updated Successfully"
                if (
                    not sensorData["error"]["Inv1_OverLoad"]
                    and not sensorData["error"]["Inv2_OverLoad"]
                ):
                    op_logger.info(
                        "Pump1 Speed: %s, Pump2 Speed: %s", pump1_speed, pump2_speed
                    )
                    return "Pump Speed Updated Successfully"
            elif pump1_speed > 0 and pump2_speed > 0 and pump1_speed != pump2_speed:
                if sensorData["error"]["Inv1_OverLoad"]:
                    op_logger.info(
                        "Pump1 Speed: %s, Pump2 Speed: %s", pump1_speed, pump2_speed
                    )
                    return "Pump Speed 2 Updated Successfully. \nPump1 can't start due to inverter1 overlaod"
                if sensorData["error"]["Inv2_OverLoad"]:
                    op_logger.info(
                        "Pump1 Speed: %s, Pump2 Speed: %s", pump1_speed, pump2_speed
                    )
                    return "Pump Speed 1 Updated Successfully. \nPump2 can't start due to inverter2 overlaod"
                if (
                    not sensorData["error"]["Inv1_OverLoad"]
                    and not sensorData["error"]["Inv2_OverLoad"]
                ):
                    op_logger.info("Pump1 Speed: %s, Pump2 Speed: 0", pump1_speed)
                    return "Please synchronize speeds to run both pumps. \nPump2 is switched off."
            elif (
                sensorData["error"]["Inv1_OverLoad"]
                and pump1_speed > 0
                and pump2_speed == 0
                and pump1_speed != pump2_speed
            ):
                op_logger.info("Pump1 Speed: 0, Pump2 Speed: %s", pump2_speed)
                return "Inverter1 Overload: Unable to update pump1 speed"
            elif (
                sensorData["error"]["Inv2_OverLoad"]
                and pump1_speed == 0
                and pump2_speed > 0
                and pump1_speed != pump2_speed
            ):
                op_logger.info("Pump1 Speed: %s, Pump2 Speed: 0", pump1_speed)
                return "Inverter2 Overload: Unable to update pump2 speed"

        op_logger.info("Pump1 Speed: %s, Pump2 Speed: %s", pump1_speed, pump2_speed)
        return "Pump Speed Updated Successfully"


@app.route("/control/ctr_pump_cnsl")
@login_required
def ctr_pump_cnsl():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            result = client.read_holding_registers(address=246, count=2)

        if result.isError():
            print(f"Modbus Error: {result}")
        else:
            oil_temp_set = cvt_registers_to_float(
                result.registers[0], result.registers[1]
            )
            ctr_pump_data["value"]["pump1_speed"] = oil_temp_set

    except Exception as e:
        print(f"ctr_pump_cnsl error:{e}")

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            result = client.read_holding_registers(address=222, count=2)

        if result.isError():
            print(f"Modbus Error: {result}")
        else:
            oil_pressure_set = cvt_registers_to_float(
                result.registers[0], result.registers[1]
            )
            ctr_pump_data["value"]["pump2_speed"] = oil_pressure_set

    except Exception as e:
        print(f"water pump error:{e}")

    return jsonify(ctr_pump_data)


@app.route("/waterPV_setting", methods=["POST"])
@login_required
def waterPV_setting():
    data = request.json
    water_PV = data.get("water_PV")
    word1, word2 = cvt_float_byte(water_PV)
    if (
        sensorData["alert_notice"]["dew_point_temp"]
        and sensorData["value"]["temp_clntSply"] < 20
    ):
        return "Unable to update: Dew Point is at alert level"
    else:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(352, [word2, word1])

        except Exception as e:
            print(f"set water pv error:{e}")
            return retry_modbus(352, [word2, word1], "register")

    op_logger.info("Water PV: %s", water_PV)
    return "Water PV Updated Successfully"


@app.route("/control/ctr_waterPV_cnsl")
@login_required
def ctr_waterPV_cnsl():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            result = client.read_holding_registers(address=352, count=2)

        if result.isError():
            print(f"Modbus Error: {result}")
        else:
            waterPV = cvt_registers_to_float(result.registers[0], result.registers[1])
            ctr_waterPV_data["value"]["water_PV"] = waterPV
    except Exception as e:
        print(f"control issue:{e}")

    return jsonify(ctr_waterPV_data)


@app.route("/filter_time_setting", methods=["POST"])
@login_required
def filter_time_setting():
    data = request.json
    filter_interval = data.get("filter_interval")
    filter_time = data.get("filter_time")
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(238, int(filter_time))
    except Exception as e:
        print(f"set filter time error:{e}")
        return retry_modbus(238, int(filter_time), "register")

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(240, int(filter_interval))
    except Exception as e:
        print(f"set filter time error:{e}")
        return retry_modbus(240, int(filter_interval), "register")

    filter_time = data.get("filter_interval")
    op_logger.info(
        "Open Filter Time Interval: %s, Filter Time: %s", filter_interval, filter_time
    )
    return "Filter Time Updated Successfully"


@app.route("/mc_setting", methods=["POST"])
@login_required
def mc_setting():
    data = request.get_json()

    mc1_sw = data.get("mc1_sw")
    mc2_sw = data.get("mc2_sw")

    regs = [mc1_sw, mc2_sw]
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coils((8192 + 617), regs)
    except Exception as e:
        print(f"mc setting error:{e}")
        return retry_modbus((8192 + 617), regs, "coil")

    if not mc1_sw:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils(0, [False])
                client.write_registers(246, [0, 0])

        except Exception as e:
            print(f"setting error:{e}")
            return retry_modbus_both(246, [0, 0], 0, [False])

    elif not mc2_sw:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils(1, [False])
                client.write_registers(222, [0, 0])

        except Exception as e:
            print(f"mc setting error:{e}")
            return retry_modbus_both(222, [0, 0], 1, [False])

    if ctr_data["downtime_error"]["oc_issue"]:
        return {
            "status": "OC",
            "message": "Overcurrent issue detected\nThe malfunctioning MC cannot be switched on",
        }
    op_logger.info("MC Set Updated Successfully. MC1: %s, MC2: %s", regs[0], regs[1])
    return {
        "status": "success",
        "message": "MC Set Updated Successfully",
    }


@app.route("/close_valve_stop", methods=["POST"])
@login_required
def close_valve_stop():
    data = request.json
    value_to_write = data.get("close_valve")

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil(address=(8192 + 515), value=value_to_write)
            ctr_data["stop_valve_close"] = value_to_write
    except Exception as e:
        print(f"close valve error:{e}")
        return retry_modbus((8192 + 515), value_to_write, "coil")

    op_logger.info("Close Valve When Stop: %s", value_to_write)
    return "Updated setting successfully"


@app.route("/read_close_valve_stop", methods=["GET"])
@login_required
def read_close_valve_stop():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            result = client.read_coils((8192 + 515), 1)
    except Exception as e:
        print(f"read close valve stop error:{e}")
        return jsonify({"error": "Request timeout"}), 504

    return jsonify({"success": True}) if result.bits[0] else jsonify({"success": False})


@app.route("/thrshd_set", methods=["POST"])
@login_required
def thrshd_set():
    data = request.get_json()

    with open(f"{web_path}/json/thrshd.json", "w") as json_file:
        json.dump(data, json_file)

    registers = []
    grouped_register = []
    coil_registers = []
    index = 0
    thr_count = sum(1 for key in thrshd if "Thr_" in key)

    for key in thrshd.keys():
        value = data[key]
        if key.endswith("_trap"):
            coil_registers.append(value)
        else:
            if index < thr_count:
                word1, word2 = cvt_float_byte(value)
                registers.append(word2)
                registers.append(word1)
            else:
                registers.append(int(value))
            index += 1

    grouped_register = [registers[i : i + 64] for i in range(0, len(registers), 64)]

    i = 0
    for group in grouped_register:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_registers(1000 + i * 64, group)
        except Exception as e:
            print(f"set thrshd error:{e}")
            return retry_modbus(1000 + i * 64, group, "register")
        i += 1

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coils((8192 + 2000), coil_registers)
    except Exception as e:
        print(f"write trap error: {e}")
        return retry_modbus((8192 + 2000), coil_registers, "coil")

    for key in thrshd.keys():
        value = data[key]
        op_logger.info("%s: %s", key, value)

    return "Threshold Setting Updated Successfully"


@app.route("/writeSensorAdjust", methods=["POST"])
@login_required
def writeSensorAdjust():
    data = request.get_json()

    registers = []

    for key in sensor_adjust.keys():
        value = data[key]
        word1, word2 = cvt_float_byte(value)
        registers.append(word2)
        registers.append(word1)
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(1400, registers)

    except Exception as e:
        print(f"write sensor adjust error:{e}")
        return retry_modbus(1400, registers, "register")

    op_logger.info("Sensor Adjust Inputs received Successfully")

    return "Sensor Adjust Setting Updated Successfully"


@app.route("/systemSetting/unit_set", methods=["POST"])
@login_required
def unit_set():
    data = request.json
    value_to_write = data.get("value")

    if value_to_write == "metric":
        coil_value = False
    elif value_to_write == "imperial":
        coil_value = True

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coil(address=(8192 + 500), value=coil_value)
    except Exception as e:
        print(f"write in unit error:{e}")
        return retry_modbus((8192 + 500), coil_value, "coil")

    change_data_by_unit()
    op_logger.info("setting unit_set successfully")
    return f"Unit set to '{value_to_write}' successfully"


@app.route("/systemSetting/unit_cancel", methods=["GET"])
@login_required
def unit_cancel():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            result = client.read_coils(address=(8192 + 500), count=1)

            if result.isError():
                print(f"Modbus Error: {result}")
            else:
                if not result.bits[0]:
                    system_data["value"]["unit"] = "metric"
                else:
                    system_data["value"]["unit"] = "imperial"
    except Exception as e:
        print(f"read unit error:{e}")

    op_logger.info("Unit: %s", system_data["value"]["unit"])
    return jsonify(system_data)


@app.route("/update_password", methods=["POST"])
@login_required
def update_password():
    pwd_package = request.get_json().get("pwd_package")

    password = pwd_package["password"]
    last_pwd = pwd_package["last_pwd"]
    passwordcfm = pwd_package["passwordcfm"]

    if passwordcfm != password:
        return jsonify(
            {"status": "error", "message": "Passwords do not match. Please re-enter."}
        )

    if not all([password, last_pwd, passwordcfm]):
        return jsonify(
            {
                "status": "error",
                "message": "Please fill out all password fields",
            }
        )

    if last_pwd != USER_DATA["user"]:
        return jsonify(
            {
                "status": "error",
                "message": "Last password is incorrect",
            }
        )

    USER_DATA["user"] = password

    set_key(f"{web_path}/.env", "USER", USER_DATA["user"])
    os.chmod(f"{web_path}/.env", 0o666)
    op_logger.info("User password updated successfully")
    return jsonify({"status": "success", "message": "Password Updated Successfully"})


@app.route("/reset_password", methods=["POST"])
@login_required
def reset_password():
    USER_DATA["user"] = "0000"

    set_key(f"{web_path}/.env", "USER", USER_DATA["user"])
    os.chmod(f"{web_path}/.env", 0o666)
    op_logger.info("User password updated successfully")
    return jsonify({"status": "success", "message": "Password Updated Successfully"})


@app.route("/get_modbus_ip", methods=["GET"])
def get_modbus_ip():
    modbus_host = os.environ.get("MODBUS_IP")
    return jsonify({"modbus_ip": modbus_host})


@app.route("/update_modbus_ip", methods=["POST"])
@login_required
def update_modbus_ip():
    new_ip = request.json.get("modbus_ip")
    if not new_ip:
        return jsonify({"error": "No IP address provided"}), 400

    set_key(f"{web_path}/.env", "MODBUS_IP", new_ip)

    global modbus_host
    modbus_host = new_ip
    os.environ["MODBUS_IP"] = new_ip

    op_logger.info(f"MODBUS_IP updated successfully, new_modbus_ip: {modbus_host}")
    return jsonify(
        {"message": "MODBUS_IP updated successfully", "new_modbus_ip": modbus_host}
    )


@app.route("/write_version", methods=["POST"])
@login_required
def write_version():
    data = request.json

    if os.path.exists(f"{web_path}/fw_info.json"):
        with open(f"{web_path}/fw_info.json", "r") as file:
            FW_Info = json.load(file)

    FW_Info["SN"] = data["SN"]
    FW_Info["Model"] = data["Model"]
    FW_Info["Version"] = data["Version"]

    with open(f"{web_path}/fw_info.json", "w") as file:
        json.dump(FW_Info, file)

    op_logger.info(f"FW Setting Updated Successfully. {data}")
    return "FW Setting Updated Successfully"


@app.route("/read_version", methods=["GET"])
@login_required
def read_version():
    if not os.path.exists(f"{web_path}/fw_info.json"):
        with open(f"{web_path}/fw_info.json", "w") as file:
            file.write("")
    with open(f"{web_path}/fw_info.json", "r") as file:
        FW_Info = json.load(file)

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            r = client.read_holding_registers(990, 1)
            plc_version = r.registers[0]
    except Exception as e:
        print(f"fwInfo error: {e}")
        return jsonify({"error": "Request timeout"}), 504

    return jsonify({"FW_Info": FW_Info, "plc_version": plc_version})


@app.route("/set_time", methods=["POST"])
def set_time():
    if not onLinux:
        return jsonify({"status": "error", "message": "Not supported on Windows"}), 501
    try:
        data = request.json
        datetime_str = data["value"]
        # 檢查輸入的格式，若缺少秒數則補上 ":00"
        if len(datetime_str) == 16:  # "YYYY-MM-DDTHH:MM"
            datetime_str += ":00"  # 變成 "YYYY-MM-DDTHH:MM:00"
        json_datetime = dt.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        formatted_date_time = json_datetime.strftime("%Y-%m-%d %H:%M:%S")

        subprocess.run(["sudo", "timedatectl", "set-ntp", "false"], check=True)

        result = subprocess.run(
            ["sudo", "timedatectl", "set-time", formatted_date_time],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stderr:
            op_logger.info(f"Failed to set time: {result.stderr}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to set time: {result.stderr}",
                    }
                ),
                500,
            )

        # 確保 RTC 時鐘也更新
        subprocess.run(["sudo", "hwclock", "--systohc"], check=True)

        op_logger.info("Date and time set successfully.")
        return jsonify(
            {
                "status": "success",
                "message": "Date and time set successfully. Please log in again.",
            }
        )

    except subprocess.CalledProcessError as e:
        op_logger.info(f"Time Set Unsuccessful. {e}")
        return (
            jsonify({"status": "error", "message": f"Time Set Unsuccessful: {e}"}),
            500,
        )

    except Exception as e:
        op_logger.info(f"General error: {e}")
        return jsonify({"status": "error", "message": f"Unexpected error: {e}"}), 500


@app.route("/sync_time", methods=["POST"])
def sync_time():
    if not onLinux:
        return jsonify({"status": "error", "message": "Not supported on Windows"}), 501
    data = request.json
    ntp_server = data.get("ntp_server")
    timezone = data.get("timezone")

    if not ntp_server or not timezone:
        return (
            jsonify(
                {"status": "error", "message": "NTP server and timezone are required."}
            ),
            400,
        )

    try:
        # 設定時區
        subprocess.run(["sudo", "timedatectl", "set-timezone", timezone], check=True)
        op_logger.info(f"Timezone set to {timezone}.")

        # 執行 NTP 同步
        result = subprocess.run(
            ["sudo", "ntpdate", ntp_server], capture_output=True, text=True
        )

        if result.returncode != 0:
            op_logger.info(f"NTP sync failed: {result.stderr}")
            return (
                jsonify(
                    {"status": "error", "message": f"NTP sync failed: {result.stderr}"}
                ),
                500,
            )

        op_logger.info(f"Sync result: {result.stdout}")

        # 同步 RTC 硬體時鐘
        subprocess.run(["sudo", "hwclock", "--systohc"], check=True)
        op_logger.info("RTC clock updated with system time.")

        # 重新載入 systemd（非必要，但可避免 service 問題）
        subprocess.run(
            ["sudo", "systemctl", "daemon-reload"], capture_output=True, text=True
        )

        # 重新啟動 webui.service，確保應用程式正確運行
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "webui.service"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to restart webui service: {result.stderr}",
                    }
                ),
                500,
            )

        op_logger.info(
            f"Time synchronized with {ntp_server} and timezone set to {timezone}."
        )
        return jsonify(
            {
                "status": "success",
                "message": f"Time synchronized with {ntp_server} and timezone set to {timezone}.",
            }
        )

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Sync process failed: {e}"}), 500


@app.route("/get_system_time", methods=["GET"])
def get_system_time():
    current_time = dt.datetime.now()

    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({"system_time": current_time_str})


@app.route("/get_timeout", methods=["GET"])
def get_timeout():
    if not os.path.exists(f"{web_path}/json/timeout_light.json"):
        with open(f"{web_path}/json/timeout_light.json", "w") as file:
            file.write('{"timeoutLight": "30011"}')

    with open(f"{web_path}/json/timeout_light.json", "r") as file:
        TIMEOUT_Info = json.load(file)

    return jsonify(TIMEOUT_Info)


@app.route("/set_timeout", methods=["POST"])
def set_timeout():
    data = request.json
    TIMEOUT_Info = data

    with open(f"{web_path}/json/timeout_light.json", "w") as file:
        json.dump(TIMEOUT_Info, file)
    op_logger.info(
        f"Update indicator delay successfully. Indicator delay:{TIMEOUT_Info}"
    )
    return jsonify({"status": "success"})


@app.route("/get_network_info", methods=["GET"])
@login_required
def get_network_info():
    json_formatted_string = []

    network_info_list = collect_allnetwork_info()

    web_formatted_string = [
        json.dumps(info, indent=4, separators=(",", ": ")) for info in network_info_list
    ]

    with open(f"{web_path}/json/network.json", "w") as jsonFile:
        json.dump(json_formatted_string, jsonFile, indent=4)

    return jsonify(
        {
            "ethernet_info1": web_formatted_string[0],
            "ethernet_info2": web_formatted_string[1],
            "ethernet_info3": web_formatted_string[2],
            "ethernet_info4": web_formatted_string[3],
        }
    )


@app.route("/set_network", methods=["POST"])
@login_required
def set_network():
    if not onLinux:
        return jsonify({"status": "error", "message": "Not supported on Windows"}), 501
    data = request.json
    network_set = all_network_set[int(data["networkId"]) - 1]

    response = {
        "status": "success",
        "message": "Network Setting Updated Successfully",
    }

    for key in data.keys():
        if key != "networkId":
            network_set[key] = data[key]

    interface_names = read_net_name()
    networkId = int(data["networkId"])
    interface_name = interface_names[networkId - 1]

    try:
        if network_set["v4dhcp_en"]:
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv4.method",
                    "auto",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv4.addresses",
                    "",
                    "ipv4.gateway",
                    "",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        else:
            mask = network_set["v4Subnet"]
            network = ipaddress.IPv4Network("0.0.0.0/" + mask, strict=False)

            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv4.gateway",
                    "",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv4.method",
                    "manual",
                    "ipv4.address",
                    f"{network_set['IPv4Address']}/{network.prefixlen}",
                    "ipv4.gateway",
                    network_set["v4DefaultGateway"],
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            op_logger.info(
                f"interface name:{interface_name},ipv4 address:{network_set['IPv4Address']}/{network.prefixlen},netmask:{mask},gateway:{network_set['v4DefaultGateway']}"
            )
    except subprocess.CalledProcessError as e:
        response["status"] = "error"
        response["message"] = f"DHCP v4 setting failed: {e.stderr.strip()}"
        op_logger.info(response)

        return jsonify(response), 400
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Unexpected error in DHCP v4 setting: {e.stderr.strip()}"
        op_logger.info(response)
        return jsonify(response), 400

    try:
        if network_set["v4AutoDNS"]:
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.dns", ""],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv4.ignore-auto-dns",
                    "no",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        else:
            dns_servers = []
            if network_set["v4DNSPrimary"]:
                dns_servers.append(network_set["v4DNSPrimary"])
            if network_set["v4DNSOther"]:
                dns_servers.append(network_set["v4DNSOther"])

            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv4.ignore-auto-dns",
                    "yes",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.dns", ""],
                check=True,
                capture_output=True,
                text=True,
            )

            if dns_servers:
                dns_servers_str = " ".join(dns_servers)
                print("Setting DNS servers to:", dns_servers_str)
                subprocess.run(
                    [
                        "sudo",
                        "nmcli",
                        "con",
                        "mod",
                        interface_name,
                        "ipv4.dns",
                        dns_servers_str,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
    except subprocess.CalledProcessError as e:
        response["status"] = "error"
        response["message"] = f"DNS v4 setting failed: {e.stderr.strip()}"
        op_logger.info(response)

        return jsonify(response), 400
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Unexpected error in DNS v4 setting: {e.stderr.strip()}"
        op_logger.info(response)

        return jsonify(response), 400

    try:
        subprocess.run(
            ["sudo", "systemctl", "restart", "NetworkManager"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        response["status"] = "error"
        response["message"] = f"Error restarting NetworkManager: {e.stderr.strip()}"
        return jsonify(response), 500
    except Exception as e:
        response["status"] = "error"
        response["message"] = (
            f"Unexpected error restarting NetworkManager: {e.stderr.strip()}"
        )
        return jsonify(response), 500

    try:
        subprocess.run(
            ["sudo", "nmcli", "con", "down", interface_name],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["sudo", "nmcli", "con", "up", interface_name],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        response["status"] = "error"
        response["message"] = f"Error restarting network connection: {e.stderr.strip()}"
        return jsonify(response), 500
    op_logger.info(response)
    return jsonify(response)


@app.route("/v6set_network", methods=["POST"])
@login_required
def v6set_network():
    if not onLinux:
        return jsonify({"status": "error", "message": "Not supported on Windows"}), 501
    data = request.json

    network_set = all_network_set[int(data["networkId"]) - 1]
    response = {
        "status": "success",
        "message": "Network Setting Updated Successfully",
    }
    for key in data.keys():
        if key != "networkId":
            network_set[key] = data[key]

    interface_names = read_net_name()
    networkId = int(data["networkId"])
    interface_name = interface_names[networkId - 1]

    try:
        if network_set["v6dhcp_en"]:
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv6.method",
                    "auto",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv6.addresses",
                    "",
                    "ipv6.gateway",
                    "",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "modify",
                    interface_name,
                    "ipv6.method",
                    "manual",
                    "ipv6.address",
                    f"{network_set['IPv6Address']}/{network_set['v6Subnet']}",
                    "ipv6.gateway",
                    network_set["v6DefaultGateway"],
                ],
                check=True,
                capture_output=True,
                text=True,
            )

    except subprocess.CalledProcessError as e:
        print(f"Error executing DHCP v6 command: {e.stderr.strip()}")
    except Exception as e:
        print(f"Unexpected error in DHCP v6 setting: {e.stderr.strip()}")

    try:
        if network_set["v6AutoDNS"]:
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv6.dns", ""],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv6.ignore-auto-dns",
                    "no",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            dns_servers = []
            if network_set["v6DNSPrimary"]:
                dns_servers.append(network_set["v6DNSPrimary"])
            if network_set["v6DNSOther"]:
                dns_servers.append(network_set["v6DNSOther"])

            subprocess.run(
                [
                    "sudo",
                    "nmcli",
                    "con",
                    "mod",
                    interface_name,
                    "ipv6.ignore-auto-dns",
                    "yes",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv6.dns", ""],
                check=True,
                capture_output=True,
                text=True,
            )

            if dns_servers:
                dns_servers_str = " ".join(dns_servers)
                print("Setting DNS servers to:", dns_servers_str)
                subprocess.run(
                    [
                        "sudo",
                        "nmcli",
                        "con",
                        "mod",
                        interface_name,
                        "ipv6.dns",
                        dns_servers_str,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

    except subprocess.CalledProcessError as e:
        print(f"Error executing DNS v6 command: {e.stderr.strip()}")
    except Exception as e:
        print(f"Unexpected error in DNS v6 setting: {e.stderr.strip()}")

    try:
        subprocess.run(
            ["sudo", "systemctl", "restart", "NetworkManager"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        response["status"] = "error"
        response["message"] = f"Error restarting NetworkManager: {e.stderr.strip()}"
        return jsonify(response), 500
    except Exception as e:
        response["status"] = "error"
        response["message"] = (
            f"Unexpected error restarting NetworkManager: {e.stderr.strip()}"
        )
        return jsonify(response), 500

    try:
        subprocess.run(
            ["sudo", "nmcli", "con", "down", interface_name],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["sudo", "nmcli", "con", "up", interface_name],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        response["status"] = "error"
        response["message"] = f"Error restarting network connection: {e.stderr.strip()}"
        return jsonify(response), 500
    op_logger.info(response)
    return jsonify(response)


@app.route("/export_settings", methods=["POST"])
@login_required
def export_settings():
    data = request.json

    export_data.clear()

    try:
        if data["exp_system_chk"]:
            export_data["unit"] = system_data["value"]["unit"]

            export_data["valve_setting"] = ctr_data["stop_valve_close"]

            export_data["log_interval"] = sampling_rate["number"]

            with open(f"{snmp_path}/snmp/snmp.json", "r") as file:
                snmp = json.load(file)
            export_data["snmp"] = snmp

            if "users" not in export_data:
                export_data["users"] = {}

                encrypted_password_user = cipher_suite.encrypt(
                    USER_DATA["user"].encode()
                ).decode()
                export_data["users"]["user"] = encrypted_password_user

                encrypted_password_kiosk = cipher_suite.encrypt(
                    USER_DATA["user"].encode()
                ).decode()
                export_data["users"]["kiosk"] = encrypted_password_kiosk

        if data["exp_alt_chk"]:
            read_unit()

            try:
                thr_reg = (sum(1 for key in thrshd if "Thr_" in key)) * 2
                delay_reg = sum(1 for key in thrshd if "Delay_" in key)
                trap_reg = sum(1 for key in thrshd if "_trap" in key)
                start_address = 1000
                total_registers = thr_reg
                read_num = 120

                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    for counted_num in range(0, total_registers, read_num):
                        count = min(read_num, total_registers - counted_num)
                        result = client.read_holding_registers(
                            start_address + counted_num, count, unit=modbus_slave_id
                        )

                        if result.isError():
                            print(f"Modbus Errorxxx: {result}")
                            continue
                        else:
                            keys_list = list(thrshd.keys())
                            j = counted_num // 2
                            for i in range(0, count, 2):
                                if i + 1 < len(result.registers) and j < len(keys_list):
                                    temp1 = [
                                        result.registers[i],
                                        result.registers[i + 1],
                                    ]
                                    decoder_big_endian = (
                                        BinaryPayloadDecoder.fromRegisters(
                                            temp1,
                                            byteorder=Endian.Big,
                                            wordorder=Endian.Little,
                                        )
                                    )
                                    decoded_value_big_endian = (
                                        decoder_big_endian.decode_32bit_float()
                                    )
                                    thrshd[keys_list[j]] = decoded_value_big_endian
                                    j += 1

                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    result = client.read_holding_registers(
                        1000 + thr_reg, delay_reg, unit=modbus_slave_id
                    )

                    if result.isError():
                        print(f"Modbus Error: {result}")
                    else:
                        keys_list = list(thrshd.keys())
                        j = int(thr_reg / 2)
                        for i in range(0, delay_reg):
                            thrshd[keys_list[j]] = result.registers[i]
                            j += 1

                with ModbusTcpClient(
                    host=modbus_host, port=modbus_port, unit=modbus_slave_id
                ) as client:
                    r = client.read_coils((8192 + 2000), trap_reg)

                    if r.isError():
                        print(f"Modbus Error: {r}")
                    else:
                        keys_list = list(thrshd.keys())
                        j = int(thr_reg / 2 + delay_reg)
                        for i in range(0, trap_reg):
                            thrshd[keys_list[j]] = r.bits[i]
                            j += 1

                    with open(f"{web_path}/json/thrshd.json", "w") as json_file:
                        json.dump(thrshd, json_file)
            except Exception as e:
                print(f"read thrshd error:{e}")

            if system_data["value"]["unit"] == "metric":
                export_data["thrshd"] = thrshd
            else:
                key_list = list(thrshd.keys())
                for key in key_list:
                    if not key.endswith("_trap") and not key.startswith("Delay_"):
                        if "Temp" in key and "TempCds" not in key:
                            thrshd[key] = (thrshd[key] - 32.0) * 5.0 / 9.0

                        if "TempCds" in key:
                            thrshd[key] = thrshd[key] / 9.0 * 5.0

                        if "Prsr" in key:
                            thrshd[key] = thrshd[key] / 0.145038

                        if "Flow" in key:
                            thrshd[key] = thrshd[key] / 0.2642
                export_data["thrshd"] = thrshd

        if data["exp_ntw_chk"]:
            network_info_list = collect_allnetwork_info()
            export_data["network_set"] = network_info_list

        if data["exp_psw_adj"]:
            if data.get("exp_psw_adj", False):
                export_data["sensor_adjust"] = sensor_adjust
            else:
                export_data["sensor_adjust"] = False

        if data["exp_pid_set"]:
            with open(f"{web_path}/json/pid_setting.json", "r") as file:
                pid = json.load(file)

            if data.get("exp_pid_set", False):
                export_data["pid_setting"] = pid
            else:
                export_data["pid_setting"] = False

    except Exception as e:
        print(f"export: {e}")

    return jsonify(export_data)


@app.route("/import_settings", methods=["POST"])
@login_required
def import_settings():
    uploaded_file = request.files["file"]

    if uploaded_file.filename != "":
        if not os.path.exists(f"{web_path}/json/upload_file.json"):
            with open(f"{web_path}/json/upload_file.json", "w") as file:
                file.write("")

        uploaded_file.save(f"{web_path}/json/upload_file.json")
        with open(f"{web_path}/json/upload_file.json", "r") as file:
            data = json.load(file)
            if "network_set" in data:
                if len(data["network_set"]) != 4:
                    return jsonify(
                        {
                            "status": "error",
                            "message": "Please Provide Exactly Four Network Configurations",
                        }
                    )

                for i, network in enumerate(data["network_set"]):
                    interface_name = read_net_name()
                    print(interface_name[i], network)

                    network_set_import(interface_name[i], network)

            if "users" in data:
                try:
                    decrypted_password_user = cipher_suite.decrypt(
                        data["users"]["user"].encode()
                    ).decode()
                    USER_DATA["user"] = decrypted_password_user

                    decrypted_password_kiosk = cipher_suite.decrypt(
                        data["users"]["kiosk"].encode()
                    ).decode()
                    USER_DATA["kiosk"] = decrypted_password_kiosk

                    set_key(f"{web_path}/.env", "USER", USER_DATA["user"])
                    set_key(f"{web_path}/.env", "USER", USER_DATA["kiosk"])

                except InvalidToken:
                    return jsonify(
                        {"status": "error", "message": "Invalid Encrypted Password"}
                    )

            if "sensor_adjust" in data:
                if user_identity["ID"] == "superuser":
                    sensor_adjust = data["sensor_adjust"]
                    adjust_import(sensor_adjust)
                else:
                    return jsonify(
                        {
                            "status": "error",
                            "message": "No Access to Modify Sensor Adjustment Data",
                        }
                    )

            if "pid_setting" in data:
                pid_setting = data["pid_setting"]
                pid_import(pid_setting)

            if "unit" in data:
                unit_value = data.get("unit")
                unit_import(unit_value)

            if "valve_setting" in data:
                valve_value = data.get("valve_setting")
                close_valve_import(valve_value)

            if "log_interval" in data:
                log_interval_value = data.get("log_interval")
                log_interval_import(log_interval_value)

            if "snmp" in data:
                snmp_value = data.get("snmp")
                snmp_import(snmp_value)

            if "thrshd" in data:
                read_unit()
                if system_data["value"]["unit"] == "metric":
                    thrshd = data["thrshd"]
                    threshold_import(thrshd)
                else:
                    thrshd = data["thrshd"]
                    key_list = list(thrshd.keys())
                    for key in key_list:
                        if not key.endswith("_trap") and not key.startswith("Delay_"):
                            thrshd[key] = thrshd[key]
                            if "Temp" in key and "TempCds" not in key:
                                thrshd[key] = thrshd[key] * 9.0 / 5.0 + 32.0

                            if "TempCds" in key:
                                thrshd[key] = thrshd[key] * 9.0 / 5.0

                            if "Prsr" in key:
                                thrshd[key] = thrshd[key] * 0.145038

                            if "Flow" in key:
                                thrshd[key] = thrshd[key] * 0.2642

                    threshold_import(thrshd)

        return jsonify({"status": "success", "message": "Data Imported Successfully"})
    else:
        return jsonify({"status": "error", "message": "Invalid File"})


@app.route("/reboot", methods=["GET"])
@login_required
def restart():
    subprocess.run(
        ["sudo", "reboot"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return "Restarting System"


@app.route("/shutdown", methods=["GET"])
@login_required
def shutdown():
    subprocess.run(
        ["sudo", "shutdown", "now"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return "Shutting Down System"


@app.route("/upload_zip", methods=["GET", "POST"])
@login_required
def upload_zip():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"}), 400

        if file.filename != "service.zip":
            return (
                jsonify(
                    {"status": "error", "message": "Please upload correct file name"}
                ),
                400,
            )

        if file and file.filename.endswith(".zip"):
            zip_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(zip_path)

            preset_password = "Itgs50848614"

            try:
                with pyzipper.AESZipFile(
                    zip_path, "r", encryption=pyzipper.WZ_AES
                ) as zip_ref:
                    if not any([info.flag_bits & 0x1 for info in zip_ref.infolist()]):
                        zip_ref.close()
                        os.remove(zip_path)
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": "A password-protected ZIP file is required",
                                }
                            ),
                            400,
                        )

                    zip_ref.setpassword(preset_password.encode("utf-8"))

                    try:
                        first_file_name = zip_ref.namelist()[0]
                        zip_ref.read(first_file_name)
                        print("ZIP file is password protected and password is correct.")
                    except RuntimeError:
                        zip_ref.close()
                        os.remove(zip_path)
                        return (
                            jsonify({"status": "error", "message": "Invalid password"}),
                            400,
                        )

                    zip_info = zip_ref.infolist()
                    if len(zip_info) > 0:
                        folder_name = os.path.splitext(zip_info[0].filename)[0]
                    else:
                        zip_ref.close()
                        os.remove(zip_path)
                        return (
                            jsonify(
                                {"status": "error", "message": "ZIP file is empty"}
                            ),
                            400,
                        )

                    os.makedirs(upload_path, exist_ok=True)
                    zip_ref.extractall(upload_path)

            except RuntimeError as e:
                journal_logger.info(f"runtime error: {e}")
                os.remove(zip_path)
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Invalid password or invalid ZIP file",
                        }
                    ),
                    400,
                )
            except Exception as e:
                journal_logger.info(f"Error extracting ZIP: {e}")
                os.remove(zip_path)
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "An error occurred while processing the ZIP file",
                        }
                    ),
                    500,
                )
            finally:
                if "zip_ref" in locals():
                    zip_ref.close()

            os.remove(zip_path)

            try:
                script_path = os.path.join(snmp_path, "restart.sh")
                result = subprocess.run(
                    ["sudo", "bash", script_path],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                journal_logger.info(f"Script output:{result.stdout}")
            except subprocess.CalledProcessError as e:
                journal_logger.info(f"Error executing script: {e}")
                journal_logger.info(f"Script error output:{e.stderr}")

            return (
                jsonify(
                    {"status": "success", "message": "ZIP file uploaded successfully."}
                ),
                200,
            )

        return (
            jsonify(
                {"status": "error", "message": "Wrong file type or missing password"}
            ),
            400,
        )


@app.route("/store_sampling_rate", methods=["POST"])
@login_required
def store_sampling_rate():
    try:
        data = request.json
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(3000, data["sampleRate"])

        op_logger.info("Sampling Rate: %s", data["sampleRate"])
        return "Log Interval Updated Successfully"
    except Exception as e:
        print(f"error:{e}")
        return retry_modbus(3000, data["sampleRate"], "register")


@app.route("/Pump1reset", methods=["POST"])
@login_required
def Pump1reset():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(200, [0, 0])
            client.write_registers(270, [0] * 4)

        op_logger.info("reset Pump1 Running Time successfully!")
        return "Reset Pump1 Running Time Successfully"
    except Exception as e:
        op_logger.info("reset Pump1 Running Time failed!")
        print(f"pump1 reset error:{e}")
        return retry_modbus_2reg(200, [0] * 2, 270, [0] * 4)


@app.route("/Pump2reset", methods=["POST"])
@login_required
def Pump2reset():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(202, [0, 0])
            client.write_registers(274, [0] * 4)
        op_logger.info("reset Pump2 Running Time successfully!")
        return "Reset Pump2 Running Time Successfully"
    except Exception as e:
        op_logger.info("reset Pump2 Running Time failed!")
        print(f"pump2 reset error:{e}")
        return retry_modbus_2reg(202, [0] * 2, 274, [0] * 4)


@app.route("/filter_reset", methods=["POST"])
@login_required
def filter_reset():
    data = request.json
    index = data.get("index")

    start_register = 700 + (index - 1) * 4

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(start_register, [0, 0, 0, 0])
        op_logger.info("reset Filter Running Time successfully!")
        return "Reset Filter Running Time Successfully"
    except Exception as e:
        print(f"filter reset error:{e}")
        op_logger.info("reset Filter Running Time failed!")
        return retry_modbus(start_register, [0] * 4, "register")


@app.route("/store_pid", methods=["POST"])
@login_required
def store_pid_temp():
    data = request.json
    registers = []

    for key in data["temp"].keys():
        if key in pid_setting["temperature"]:
            pid_setting["temperature"][key] = int(data["temp"][key])
            if not key == "sample_time_temp":
                registers.append(pid_setting["temperature"][key])

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(550, pid_setting["temperature"]["sample_time_temp"])
            client.write_registers(553, registers)

    except Exception as e:
        print(f"error:{e}")
        return retry_modbus_2reg(
            550, pid_setting["temperature"]["sample_time_temp"], 553, registers
        )

    registers = []
    for key in data["pressure"].keys():
        if key in pid_setting["pressure"]:
            pid_setting["pressure"][key] = int(data["pressure"][key])
            if not key == "sample_time_pressure":
                registers.append(pid_setting["pressure"][key])

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(510, pid_setting["pressure"]["sample_time_pressure"])
            client.write_registers(513, registers)

    except Exception as e:
        print(f"error:{e}")
        return retry_modbus_2reg(
            510, pid_setting["pressure"]["sample_time_pressure"], 513, registers
        )

    with open(f"{web_path}/json/pid_setting.json", "w") as json_file:
        json.dump(pid_setting, json_file)

    return "Update PID setting successfully"


@app.route("/collapse_network", methods=["POST"])
@login_required
def collapse_network():
    data = request.get_json()

    if data["collapse"]:
        collapse_state["status"] = True
        return "Collapsed Successfully"
    else:
        collapse_state["status"] = False
        return "Uncollapsed Successfully"


@app.route("/check_network", methods=["GET"])
@login_required
def check_network():
    global collapse_state

    return jsonify({"collapse_state": collapse_state})


@app.route("/store_snmp_setting", methods=["POST"])
@login_required
def store_snmp_setting():
    data = request.get_json()

    with open(f"{snmp_path}/snmp/snmp.json", "w") as json_file:
        json.dump(data, json_file)

    try:
        script_path = f"{snmp_path}/snmp/restart.sh"
        subprocess.run(["/bin/bash", script_path], check=True)
    except subprocess.CalledProcessError as e:
        return f"Error running script: {e}", 500
    op_logger.info(f"SNMP Setting Updated Successfully. {data}")
    return "SNMP Setting Updated Successfully"


@app.route("/get_snmp_setting", methods=["GET"])
@login_required
def get_snmp_setting():
    with open(f"{snmp_path}/snmp/snmp.json", "r") as json_file:
        data = json.load(json_file)
        trap_ip = data.get("trap_ip_address")
        read_community = data.get("read_community")

    snmp_setting["trap_ip_address"] = trap_ip
    snmp_setting["read_community"] = read_community

    return jsonify(snmp_setting)


@app.route("/get_error_data", methods=["GET"])
@login_required
def get_error_data():
    global error_data

    data = list(error_data)

    return jsonify(data)


@app.route("/get_inspection_result")
@login_required
def get_inspection_result():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            key_list = list(result_data.keys())
            result_len = len(result_data.keys()) - 3
            r = client.read_holding_registers(750, result_len, unit=modbus_slave_id)

            for i in range(result_len):
                key = key_list[i]
                if r.registers[i] == 1:
                    result_data[key] = True
                elif r.registers[i] == 0:
                    result_data[key] = False

            r2 = client.read_holding_registers(800, result_len, unit=modbus_slave_id)

            key_list = list(progress_data.keys())
            for i in range(result_len):
                key = key_list[i]
                progress_data[key] = r2.registers[i]
    except Exception as e:
        print(f"get inspection result error:{e}")

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            r = client.read_holding_registers(950, 1)
            result_data["inspect_finish"] = r.registers[0]
    except Exception as e:
        print(f"get inspection finish signal error:{e}")

    if result_data["inspect_finish"] == 1:
        current_time = time.time()
        formatted_time = datetime.fromtimestamp(current_time).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        result_data["inspect_time"] = formatted_time

        with open(f"{web_path}/json/inspect_time.json", "w") as json_file:
            json.dump({"inspect_time": result_data["inspect_time"]}, json_file)

    with open(f"{web_path}/json/inspect_time.json", "r") as file:
        data = json.load(file)
        inspection_time_last_check["current_time"] = data.get("inspect_time")

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            r = client.read_holding_registers(901, 48)
            key_list = list(measure_data.keys())

            j = 0
            for i in range(0, 48, 2):
                temp1 = [r.registers[i], r.registers[i + 1]]
                decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
                    temp1, byteorder=Endian.Big, wordorder=Endian.Little
                )
                decoded_value_big_endian = decoder_big_endian.decode_32bit_float()
                format_value = decoded_value_big_endian
                measure_data[key_list[j]] = format_value
                j += 1
    except Exception as e:
        print(f"get measured result error:{e}")

    for inspection_key, sensor_key in key_mapping.items():
        if sensor_key in sensorData["value"]:
            inspection_value[inspection_key] = sensorData["value"][sensor_key]

    with open(f"{web_path}/fw_info.json", "r") as file:
        fw_info_data = json.load(file)

    whole_data = {
        "result_data": result_data,
        "inspection_value": inspection_value,
        "progress_data": progress_data,
        "sensor_data": sensorData,
        "measure_data": measure_data,
        "inspection_time_last_check": inspection_time_last_check,
        "fw_info_data": fw_info_data,
        "ver_switch": ver_switch,
    }
    return jsonify(whole_data)


@app.route("/inspection_time_apply", methods=["POST"])
def inspection_time_apply():
    data = request.get_json("data")

    ev_open_time = int(data.get("ev_open_time"))
    water_open_time = int(data.get("water_open_time"))
    pump_open_time = int(data.get("pump_open_time"))

    inspect_data = [
        ev_open_time,
        water_open_time,
        pump_open_time,
    ]

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(740, inspect_data)

    except Exception as e:
        print(f"inspection time error:{e}")
        return retry_modbus(740, inspect_data, "register")
    op_logger.info("Inspection Time Updated Successfully")
    return "Inspection Time Updated Successfully"


@app.route("/reset_current", methods=["POST"])
def reset_current():
    button_pressed = True

    if sensorData["error"]["Inv1_OverLoad"] or sensorData["error"]["Inv2_OverLoad"]:
        try:
            with ModbusTcpClient(
                host=modbus_host, port=modbus_port, unit=modbus_slave_id
            ) as client:
                client.write_coils((8192 + 800), button_pressed)

        except Exception as e:
            print(f"reset_current:{e}")
            return retry_modbus((8192 + 800), [True], "coil")
    else:
        return jsonify(status="error", message="Currently not overload")

    return jsonify(status="success", message="Reset System Failure Successfully")


@app.route("/start_inspect", methods=["POST"])
def start_inspect():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(900, 1)
            client.write_register(973, 1)
    except Exception as e:
        print(f"start inspect:{e}")
        return retry_modbus_2reg(900, 1, 973, 1)
    op_logger.info("Begin Inspection")
    return jsonify(message="Begin Inspection")


@app.route("/cancel_inspect", methods=["POST"])
def cancel_inspect():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(900, 2)
            client.write_register(973, 2)
    except Exception as e:
        print(f"cancel inspect:{e}")
        return retry_modbus_2reg(900, 2, 973, 2)
    op_logger.info("Cancel Inspection")
    return jsonify(message="Cancel Inspection")


@app.route("/auto_setting_apply", methods=["POST"])
def auto_setting_apply():
    data = request.get_json("data")
    auto_water = data["auto_water"]
    auto_pump = data["auto_pump"]
    auto_dew_point = data["auto_dew_point"]

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_register(960, int(auto_water))
            client.write_register(961, int(auto_pump))
            client.write_register(974, int(auto_dew_point))

    except Exception as e:
        print(f"auto setting:{e}")
        return retry_modbus_3reg(
            960, int(auto_water), 961, int(auto_pump), 974, int(auto_dew_point)
        )
    op_logger.info(f"Update Auto Setting Successfully. {data}")
    return jsonify(message="Update Auto Setting Successfully")


@app.route("/resetAdjust", methods=["POST"])
def resetAdjust():
    adjust_import(adjust_factory)
    op_logger.info("Reset Adjust to Factory Setting Successfully")
    return jsonify(message="Reset Adjust to Factory Setting Successfully")


@app.route("/resetThrshd", methods=["POST"])
def resetThrshd():
    if system_data["value"]["unit"] == "metric":
        threshold_import(thrshd_factory)
    else:
        key_list = list(thrshd_factory.keys())
        for key in key_list:
            if not key.endswith("_trap") and not key.startswith("Delay_"):
                imperial_thrshd_factory[key] = thrshd_factory[key]
                if "Temp" in key and "TempCds" not in key:
                    imperial_thrshd_factory[key] = (
                        thrshd_factory[key] * 9.0 / 5.0 + 32.0
                    )

                if "TempCds" in key:
                    imperial_thrshd_factory[key] = thrshd_factory[key] * 9.0 / 5.0

                if "Prsr" in key:
                    imperial_thrshd_factory[key] = thrshd_factory[key] * 0.145038

                if "Flow" in key:
                    imperial_thrshd_factory[key] = thrshd_factory[key] * 0.2642
        threshold_import(imperial_thrshd_factory)
    op_logger.info("Reset Threshold to Factory Setting Successfully")
    return jsonify(message="Reset Threshold to Factory Setting Successfully")


@app.route("/resetPID", methods=["POST"])
def resetPID():
    pid_import(pid_factory)
    op_logger.info("Reset PID to Factory Setting Successfully")
    return jsonify(message="Reset PID to Factory Setting Successfully")


@app.route("/resetValve", methods=["POST"])
def resetValve():
    if system_data["value"]["unit"] == "metric":
        valve_import(valve_factory)
    else:
        imperial_valve_factory["coolant"] = round(
            (valve_factory["coolant"]) * 9.0 / 5.0 + 32.0
        )
        imperial_valve_factory["ambient"] = round(
            (valve_factory["ambient"]) * 9.0 / 5.0 + 32.0
        )
        valve_import(imperial_valve_factory)
    op_logger.info("Reset Valve to Factory Setting Successfully")
    return jsonify(message="Reset Valve to Factory Setting Successfully")


@app.route("/resetAuto", methods=["POST"])
def resetAuto():
    auto_import(auto_factory)
    op_logger.info("Reset Auto to Factory Setting Successfully")
    return jsonify(message="Reset Auto to Factory Setting Successfully")


@app.route("/set_rack_control", methods=["POST"])
def set_rack_control():
    data = request.get_json()

    failed_racks = []

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

    try:
        for i, coil_val in enumerate(data):
            key = f"rack{i + 1}_sw"
            result_key = f"rack{i + 1}_sw_result"
            rack_key = f"rack{i + 1}"
            rack_ip = host.get(rack_key)
            enable_key = f"rack{i + 1}_enable"
            coil_addr = 8192 + 720 + i
            pass_key = f"rack{i + 1}_pass"

            if not (rack_ip and ctr_data["rack_visibility"].get(enable_key, False)):
                continue

            if not ctr_data["rack_pass"].get(pass_key, False):
                print(f"{pass_key} did not pass")
                failed_racks.append(rack_key)
                continue

            try:
                with ModbusTcpClient(
                    host=modbus_host,
                    port=modbus_port,
                    unit=modbus_slave_id,
                    timeout=0.5,
                ) as client:
                    client.write_coils(coil_addr, [coil_val])
                    ctr_data["rack_set"][key] = bool(coil_val)
                    ctr_data["rack_set"][result_key] = True
            except Exception as e:
                print(f"failed to update rack control: {e}")
                success = retry_modbus_setmode_singlecoil(
                    coil_addr, coil_val if ctr_data["rack_pass"][pass_key] else 0
                )
                if not success:
                    failed_racks.append(rack_key)
                    continue

        if failed_racks:
            failed_racks_list = "".join([f"<li>{rack}</li>" for rack in failed_racks])
            failed_message = f"Failed to update the following racks due to comm error:<br><ul style='margin-left: 67px;margin-top: 10px; text-align: left;'>{failed_racks_list}</ul>"
            return jsonify(status="error", message=failed_message)

        return jsonify(status="success", message="Update rack setting successfully")

    except Exception as e:
        print(f"Error: {e}")

        return jsonify(
            status="error", message="Error occurred while updating rack settings"
        )


@app.route("/set_rack_engineer", methods=["POST"])
def set_rack_engineer():
    data = request.get_json()

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coils((8192 + 710), data)
    except Exception as e:
        print(f"rack engineer error: {e}")
        return retry_modbus((8192 + 710), data, "coil")

    try:
        for i, v in enumerate(data):
            key = f"rack{i + 1}_enable"
            ctr_data["rack_visibility"][key] = v

        return jsonify(
            status="success", message="Rack visibility settings updated successfully"
        )
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(
            status="error", message="Error occurred while updating rack settings"
        )


@app.route("/set_valve_condition", methods=["POST"])
def set_valve_condition():
    data = request.get_json()
    ta = int(data["ta"])
    t1 = int(data["t1"])

    if system_data["value"]["unit"] == "metric":
        if ta > 100 or ta < 0 or t1 > 100 or t1 < 0:
            return jsonify(
                status="over_range",
                message="Valid Input Range is between 0°C to 100°C",
            )
    else:
        if ta > 212 or ta < 32 or t1 > 212 or t1 < 32:
            return jsonify(
                status="over_range",
                message="Valid Input Range is between 32°F to 212°F",
            )

    with open(f"{web_path}/json/valve_setting.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_registers(980, [t1, ta])
        op_logger.info(f"Valve condition updated successfully. {data}")
        return jsonify(status="success", message="Valve condition updated successfully")
    except Exception as e:
        print(f"Error: {e}")
        return retry_modbus(980, [t1, ta], "register")


@app.route("/version_switch", methods=["POST"])
def version_switch():
    data = request.get_json()

    function_switch = data["function_switch"]
    flow_switch = data["flow_switch"]
    flow2_switch = data["flow2_switch"]
    median_switch = data["median_switch"]
    mc_switch = data["mc_switch"]

    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            client.write_coils(
                (8192 + 801),
                [
                    function_switch,
                    flow_switch,
                    flow2_switch,
                    median_switch,
                    mc_switch,
                ],
            )
        op_logger.info(f"Version setting updated successfully. {data}")
        return jsonify(status="success", message="Version setting updated successfully")
    except Exception as e:
        print(f"Error: {e}")
        return retry_modbus(
            (8192 + 801),
            [
                function_switch,
                flow_switch,
                flow2_switch,
                median_switch,
                mc_switch,
            ],
            "coil",
        )


@app.route("/reset_water", methods=["POST"])
def reset_water():
    try:
        with ModbusTcpClient(
            host=modbus_host, port=modbus_port, unit=modbus_slave_id
        ) as client:
            word1, word2 = cvt_float_byte(30)
            client.write_registers(352, [word2, word1])

    except Exception as e:
        print(f"set water pv error:{e}")

        return retry_modbus(352, [word2, word1], "register")

    op_logger.info("Water PV: %s", 30)
    return jsonify(status="success", message="Proportional valve successfully reset")


@app.route("/download_logs/error/<date_range>")
def download_errorlogs_by_range(date_range):
    """Get Error Logs"""

    start_date_str, end_date_str = date_range.split("~")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    today = datetime.now().date()

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        files = os.listdir(f"{log_path}/logs/error")

        for file in files:
            try:
                if file == "errorlog.log":
                    file_date = today
                else:
                    file_date_str = file.rsplit(".", 1)[-1]
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()

                if start_date <= file_date <= end_date:
                    zip_file.write(f"{log_path}/logs/error/{file}", arcname=file)
            except (IndexError, ValueError):
                continue

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"errorlogs_{start_date_str}_to_{end_date_str}.zip",
    )


@app.route("/download_logs/operation/<date_range>")
def download_oplogs_by_range(date_range):
    """Get Operation Logs"""

    start_date_str, end_date_str = date_range.split("~")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    today = datetime.now().date()

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        files = os.listdir(f"{log_path}/logs/operation")

        for file in files:
            try:
                if file == "oplog.log":
                    file_date = today
                    print(f"filedate{file_date}")
                else:
                    file_date_str = file.rsplit(".", 1)[-1]
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                    print(f"filedate{file_date}")

                if start_date <= file_date <= end_date:
                    zip_file.write(f"{log_path}/logs/operation/{file}", arcname=file)
            except (IndexError, ValueError):
                continue

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"oplogs_{start_date_str}_to_{end_date_str}.zip",
    )


@app.route("/download_logs/sensor/<date_range>")
def download_sensorlogs_by_range(date_range):
    """Get Sensor Logs"""

    start_date_str, end_date_str = date_range.split("~")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        files = os.listdir(f"{log_path}/logs/sensor")

        for file in files:
            try:
                file_date_str = file.rsplit(".")[-2]
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                if start_date <= file_date <= end_date:
                    zip_file.write(f"{log_path}/logs/sensor/{file}", arcname=file)
            except (IndexError, ValueError):
                continue

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"sensorlogs_{start_date_str}_to_{end_date_str}.zip",
    )


@app.before_request
def before_request():
    g.sensorData = sensorData
    g.ctr_data = ctr_data
    g.system_data = system_data
    g.result_data = result_data
    g.user_role = USER_DATA
    g.adjust = sensor_adjust
    g.user_login_info = user_login_info


@app.route("/get_signal_records", methods=["GET"])
def get_signal_records():
    try:
        load_signal_records()

        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=20, type=int)

        filter_signal_names = request.args.getlist("signal_name")
        search_keyword = request.args.get("search", default="", type=str).lower()

        filtered_records = signal_records
        if filter_signal_names:
            filtered_records = [
                record
                for record in filtered_records
                if record["signal_name"] in filter_signal_names
            ]

        if search_keyword:
            filtered_records = [
                record
                for record in filtered_records
                if search_keyword in record.get("signal_name", "").lower()
                or search_keyword in record.get("signal_value", "").lower()
            ]

        total_records = len(filtered_records)
        total_pages = (total_records + limit - 1) // limit

        start = (page - 1) * limit
        end = start + limit
        paginated_records = filtered_records[start:end]

        return jsonify(
            {
                "total_records": total_records,
                "total_pages": total_pages,
                "records": paginated_records,
            }
        )
    except FileNotFoundError:
        return jsonify([])


@app.route("/get_downtime_signal_records", methods=["GET"])
def get_downtime_signal_records():
    try:
        load_downtime_signal_records()

        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=20, type=int)

        filter_signal_names = request.args.getlist("signal_name")
        search_keyword = request.args.get("search", default="", type=str).lower()

        filtered_records = downtime_signal_records
        if filter_signal_names:
            filtered_records = [
                record
                for record in filtered_records
                if record["signal_name"] in filter_signal_names
            ]

        if search_keyword:
            filtered_records = [
                record
                for record in filtered_records
                if search_keyword in record.get("signal_name", "").lower()
                or search_keyword in record.get("signal_value", "").lower()
            ]

        total_records = len(filtered_records)
        total_pages = (total_records + limit - 1) // limit

        start = (page - 1) * limit
        end = start + limit
        paginated_records = filtered_records[start:end]

        return jsonify(
            {
                "total_records": total_records,
                "total_pages": total_pages,
                "records": paginated_records,
            }
        )
    except FileNotFoundError:
        return jsonify([])


@app.route("/delete_signal_records", methods=["POST"])
def delete_signal_records():
    data = request.get_json()
    signals_to_delete = data.get("signals", [])

    global signal_records
    initial_count = len(signal_records)

    for signal in signals_to_delete:
        signal_name = signal.get("signal_name")
        on_time = signal.get("on_time")

        signal_records = [
            record
            for record in signal_records
            if not (
                record["signal_name"] == signal_name and record["on_time"] == on_time
            )
        ]

    if len(signal_records) < initial_count:
        save_to_json()
        return jsonify(
            {"status": "success", "message": "Records deleted successfully."}
        )
    else:
        return jsonify({"status": "fail", "message": "No records found to delete."})


@app.route("/delete_downtime_signal_records", methods=["POST"])
def delete_downtime_signal_records():
    data = request.get_json()
    signals_to_delete = data.get("signals", [])

    global downtime_signal_records
    initial_count = len(downtime_signal_records)

    for signal in signals_to_delete:
        signal_name = signal.get("signal_name")
        on_time = signal.get("on_time")

        downtime_signal_records = [
            record
            for record in downtime_signal_records
            if not (
                record["signal_name"] == signal_name and record["on_time"] == on_time
            )
        ]

    if len(downtime_signal_records) < initial_count:
        save_to_downtime_json()
        return jsonify(
            {"status": "success", "message": "Records deleted successfully."}
        )
    else:
        return jsonify({"status": "fail", "message": "No records found to delete."})


update_json_restore_times()

read_rack_status = threading.Thread(target=read_rack_status)
read_rack_status.daemon = True
read_rack_status.start()


modbus_thread = threading.Thread(target=read_modbus_data)
modbus_thread.daemon = True
modbus_thread.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5501, debug=True, use_reloader=repeat)

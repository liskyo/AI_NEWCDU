from flask import (
    request,
    Blueprint,
    jsonify,
    g,
    send_file,
    Flask,
    Response,
)
from flask_login import LoginManager
from flask_login import UserMixin
from dotenv import load_dotenv
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
import logging
import struct
import os
import zipfile
from io import BytesIO
from datetime import datetime
import json
import re
import subprocess
from functools import wraps
import pyzipper
import platform
import threading
import time
import copy


USERNAME = "admin"

PASSWORD = os.getenv("ADMIN")
load_dotenv()

if platform.system() == "Linux":
    onLinux = True
else:
    onLinux = False


app = Flask(__name__)
log_path = os.getcwd()
web_path = f"{log_path}/web"
snmp_path = os.path.dirname(log_path)

upload_path = "/home/user/"
app.config["UPLOAD_FOLDER"] = upload_path

scc_bp = Blueprint("scc", __name__)


login_manager = LoginManager()
login_manager.init_app(scc_bp)


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


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    if user_id in g.user_role:
        return User(user_id)
    return None


thrshd = {}
ctr_data = {}
measure_data = {}
thrshd_factory = {}
valve_setting = {}
system_data = {}
valve_factory = {}
v2 = False

sensor_trap = {
    "CoolantSupplyTemperature": {"Warning": False, "Alert": False},
    "CoolantSupplyTemperatureSpare": {"Warning": False, "Alert": False},
    "CoolantReturnTemperature": {"Warning": False, "Alert": False},
    "WaterSupplyTemperature": {"Warning": False, "Alert": False},
    "WaterReturnTemperature": {"Warning": False, "Alert": False},
    "CoolantSupplyPressure": {"Warning": False, "Alert": False},
    "CoolantSupplyPressureSpare": {"Warning": False, "Alert": False},
    "CoolantReturnPressure": {"Warning": False, "Alert": False},
    "CoolantReturnPressureSpare": {"Warning": False, "Alert": False},
    "FilterInletPressure": {"Warning": False, "Alert": False},
    "Filter1OutletPressure": {"Warning": False, "Alert": False},
    "Filter2OutletPressure": {"Warning": False, "Alert": False},
    "Filter3OutletPressure": {"Warning": False, "Alert": False},
    "Filter4OutletPressure": {"Warning": False, "Alert": False},
    "Filter5OutletPressure": {"Warning": False, "Alert": False},
    "WaterInletPressure": {"Warning": False, "Alert": False},
    "WaterOutletPressure": {"Warning": False, "Alert": False},
    "RelativeHumidity": {"Warning": False, "Alert": False},
    "AmbientTemperature": {"Warning": False, "Alert": False},
    "DewPoint": {"Warning": False, "Alert": False},
    "CoolantFlowRate": {"Warning": False, "Alert": False},
    "WaterFlowRate": {"Warning": False, "Alert": False},
    "pH": {"Warning": False, "Alert": False},
    "Conductivity": {"Warning": False, "Alert": False},
    "Turbidity": {"Warning": False, "Alert": False},
    "InstantPowerConsumption": {"Warning": False, "Alert": False},
    "HeatCapAverageCurrentity": {"Warning": False, "Alert": False},
    "AverageCurrent": {"Warning": False, "Alert": False},
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
    "Delay_ATS": 0,
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

valve_factory = {"ambient": 20, "coolant": 20}

imperial_thrshd_factory = {}
imperial_valve_factory = {}

device_trap = {
    "PV1Status": False,
    "EV1Status": False,
    "EV2Status": False,
    "EV3Status": False,
    "EV4Status": False,
    "VFD1Overload": False,
    "VFD2Overload": False,
    "VFD1Status": False,
    "VFD2Status": False,
    "LeakDetectionLeak": False,
    "LeakDetectionBroken": False,
    "PowerSource": False,
    "Inv1SpeedComm": False,
    "Inv2SpeedComm": False,
    "AmbientTemperatureComm": False,
    "CoolantFlowRateComm": False,
    "FacilityWaterFlowRateComm": False,
    "ConductivityComm": False,
    "pHComm": False,
    "TurbidityComm": False,
    "ATS1Comm": False,
    "InstantPowerConsumptionComm": False,
    "CoolantSupplyTemperatureBroken": False,
    "CoolantSupplyTemperatureSpareBroken": False,
    "CoolantReturnTemperatureBroken": False,
    "WaterSupplyTemperatureBroken": False,
    "WaterReturnTemperatureBroken": False,
    "CoolantSupplyPressureBroken": False,
    "CoolantSupplyPressureSpareBroken": False,
    "CoolantReturnPressureBroken": False,
    "CoolantReturnPressureSpareBroken": False,
    "FilterInletPressureBroken": False,
    "Filter1Status": False,
    "Filter2Status": False,
    "Filter3Status": False,
    "Filter4Status": False,
    "Filter5Status": False,
    "WaterInletPressureBroken": False,
    "WaterOutletPressureBroken": False,
    "CoolantFlowRateBroken": False,
    "WaterFlowRateBroken": False,
    "LowCoolantLevelWarning": False,
    "Inv1ErrorCode": False,
    "Inv2ErrorCode": False,
    "PC1Error": False,
    "PC2Error": False,
    "Level1Error": False,
    "Level2Error": False,
    "Level3Error": False,
    "Power1Error": False,
    "Power2Error": False,
    "ControlUnit": False,
}


ev_status = {
    "EV1": "",
    "EV2": "",
    "EV3": "",
    "EV4": "",
}

ev_on_off = {
    "ev1_open": False,
    "ev1_close": False,
    "ev2_open": False,
    "ev2_close": False,
    "ev3_open": False,
    "ev3_close": False,
    "ev4_open": False,
    "ev4_close": False,
}

inverter_status = {
    "Inverter1": "",
    "Inverter2": "",
}

inv_error_code = {
    "code1": 0,
    "code2": 0,
}

data = {
    "sensor_value": {
        "CoolantSupplyTemperature": 0,
        "CoolantSupplyTemperatureSpare": 0,
        "CoolantReturnTemperature": 0,
        "WaterSupplyTemperature": 0,
        "WaterReturnTemperature": 0,
        "CoolantSupplyPressure": 1.23,
        "CoolantSupplyPressureSpare": 1.23,
        "CoolantReturnPressure": 1.23,
        "FilterInletPressure": 1.23,
        "Filter1OutletPressure": 1.23,
        "Filter2OutletPressure": 1.23,
        "Filter3OutletPressure": 1.23,
        "Filter4OutletPressure": 1.23,
        "Filter5OutletPressure": 1.23,
        "CoolantReturnPressureSpare": 1.23,
        "WaterInletPressure": 1.23,
        "WaterOutletPressure": 1.23,
        "ProportionalValve": 50,
        "RelativeHumidity": 0,
        "AmbientTemperature": 0,
        "DewPoint": 0,
        "CoolantFlowRate": 0,
        "WaterFlowRate": 0,
        "pH": 0,
        "Conductivity": 0,
        "Turbidity": 0,
        "InstantPowerConsumption": 0,
        "Pump1Speed": 0,
        "Pump2Speed": 0,
        "AverageCurrent": 0,
        "HeatCapacity": 0,
    },
    "unit": {
        "Temperature": "Celcius",
        "Pressure": "KPA",
        "FlowRate": "LPM",
        "PowerConsumption": "kW",
        "HeatCapacity": "kW",
    },
    "pump_speed": {"Pump1Speed": 0, "Pump2Speed": 0},
    "pump_service_hours": {"Pump1ServiceHour": 172, "Pump2ServiceHour": 169},
    "filter_service_hours": {
        "Filter1ServiceHour": 172,
        "Filter2ServiceHour": 169,
        "Filter3ServiceHour": 169,
        "Filter4ServiceHour": 169,
        "Filter5ServiceHour": 169,
    },
    "pump_state": {"Pump1State": "Enable", "Pump2State": "Disable"},
    "vfd_health": {"Pump1Health": "Good", "Pump2Health": "Error"},
    "water_pv": {"WaterProportionalValve": 0},
    "valve": {"EV1": "open", "EV2": "open", "EV3": "close", "EV4": "close"},
}

sensor_value_data = {
    "CoolantSupplyTemperature": {
        "Name": "CoolantSupplyTemperature",
        "DisplayName": "Coolant Supply Temperature (T1)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "60"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "65"},
        "DelayTime": 0,
    },
    "CoolantSupplyTemperatureSpare": {
        "Name": "CoolantSupplyTemperatureSpare",
        "DisplayName": "Coolant Supply Temperature (Spare) (T1 sp)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "60"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "65"},
        "DelayTime": 0,
    },
    "CoolantReturnTemperature": {
        "Name": "CoolantReturnTemperature",
        "DisplayName": "Coolant Return Temperature (T2)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "60"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "65"},
        "DelayTime": 0,
    },
    "WaterSupplyTemperature": {
        "Name": "WaterSupplyTemperature",
        "DisplayName": "Facility Water Supply Temperature (T4)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "10", "MaxValue": "40"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "5", "MaxValue": "45"},
        "DelayTime": 0,
    },
    "WaterReturnTemperature": {
        "Name": "WaterReturnTemperature",
        "DisplayName": "Facility Water Return Temperature (T5)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "10", "MaxValue": "45"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "5", "MaxValue": "50"},
        "DelayTime": 0,
    },
    "CoolantSupplyPressure": {
        "Name": "CoolantSupplyPressure",
        "DisplayName": "Coolant Supply Pressure (P1)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "350"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "400"},
        "DelayTime": 0,
    },
    "CoolantSupplyPressureSpare": {
        "Name": "CoolantSupplyPressureSpare",
        "DisplayName": "Coolant Supply Pressure (Spare) (P1 sp)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "350"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "400"},
        "DelayTime": 0,
    },
    "CoolantReturnPressure": {
        "Name": "CoolantReturnPressure",
        "DisplayName": "Coolant Return Pressure (P2)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
        "DelayTime": 0,
    },
    "CoolantReturnPressureSpare": {
        "Name": "CoolantReturnPressureSpare",
        "DisplayName": "Coolant Return Pressure (Spare) (P2 sp)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
        "DelayTime": 0,
    },
    "FilterInletPressure": {
        "Name": "FilterInletPressure",
        "DisplayName": "Filter Inlet Pressure (P3)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "0", "MaxValue": "500"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "0", "MaxValue": "550"},
        "DelayTime": 0,
    },
    "Filter1OutletPressure": {
        "Name": "Filter1OutletPressure",
        "DisplayName": "Filter1 Outlet Pressure (P4)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
        "DelayTime": 0,
    },
    "Filter2OutletPressure": {
        "Name": "Filter2OutletPressure",
        "DisplayName": "Filter2 Outlet Pressure (P5)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
        "DelayTime": 0,
    },
    "Filter3OutletPressure": {
        "Name": "Filter3OutletPressure",
        "DisplayName": "Filter3 Outlet Pressure (P6)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
        "DelayTime": 0,
    },
    "Filter4OutletPressure": {
        "Name": "Filter4OutletPressure",
        "DisplayName": "Filter4 Outlet Pressure (P7)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
        "DelayTime": 0,
    },
    "Filter5OutletPressure": {
        "Name": "Filter5OutletPressure",
        "DisplayName": "Filter5 Outlet Pressure (P8)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
        "DelayTime": 0,
    },
    "WaterInletPressure": {
        "Name": "WaterInletPressure",
        "DisplayName": "Facility Water Supply Pressure (P10)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "750"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "800"},
        "DelayTime": 0,
    },
    "WaterOutletPressure": {
        "Name": "WaterOutletPressure",
        "DisplayName": "Facility Water Return Pressure (P11)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "750"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "800"},
        "DelayTime": 0,
    },
    "RelativeHumidity": {
        "Name": "RelativeHumidity",
        "DisplayName": "Relative Humidity (RH)",
        "Status": "Good",
        "Value": "0",
        "Unit": "%",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "8.5", "MaxValue": "75"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "8", "MaxValue": "80"},
        "DelayTime": 0,
    },
    "AmbientTemperature": {
        "Name": "AmbientTemperature",
        "DisplayName": "Ambient Temperature (T a)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "23", "MaxValue": "40"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "18", "MaxValue": "45"},
        "DelayTime": 0,
    },
    "DewPoint": {
        "Name": "DewPoint",
        "DisplayName": "Dew Point Temperature (T Dp)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "5", "MaxValue": None},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "2"},
        "DelayTime": 0,
    },
    "CoolantFlowRate": {
        "Name": "CoolantFlowRate",
        "DisplayName": "Coolant Flow Rate (F1)",
        "Status": "Good",
        "Value": "0",
        "Unit": "LPM",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "30", "MaxValue": None},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "20", "MaxValue": None},
        "DelayTime": 0,
    },
    "WaterFlowRate": {
        "Name": "WaterFlowRate",
        "DisplayName": "Facility Water Flow Rate (F2)",
        "Status": "Good",
        "Value": "0",
        "Unit": "LPM",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "30", "MaxValue": None},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "20", "MaxValue": None},
        "DelayTime": 0,
    },
    "pH": {
        "Name": "pH",
        "DisplayName": "pH (PH)",
        "Status": "Good",
        "Value": "0",
        "Unit": "pH",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "7.2", "MaxValue": "7.9"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "7", "MaxValue": "8"},
        "DelayTime": 0,
    },
    "Conductivity": {
        "Name": "Conductivity",
        "DisplayName": "Conductivity (CON)",
        "Status": "Good",
        "Value": "0",
        "Unit": "µS/cm",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "4200", "MaxValue": "4600"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "4000", "MaxValue": "4700"},
        "DelayTime": 0,
    },
    "Turbidity": {
        "Name": "Turbidity",
        "DisplayName": "Turbidity (Tur)",
        "Status": "Good",
        "Value": "0",
        "Unit": "NRU",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "2", "MaxValue": "10"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "1", "MaxValue": "15"},
        "DelayTime": 0,
    },
    "InstantPowerConsumption": {
        "Name": "InstantPowerConsumption",
        "DisplayName": "Instant Power Consumption",
        "Status": "Good",
        "Value": "0",
        "Unit": "kW",
    },
    "HeatCapacity": {
        "Name": "HeatCapacity",
        "DisplayName": "Heat Capacity",
        "Status": "Good",
        "Value": "0",
        "Unit": "kW",
    },
    "AverageCurrent": {
        "Name": "AverageCurrent",
        "DisplayName": "Average Current",
        "Status": "Good",
        "Value": "0",
        "Unit": "kW",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "40"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "45"},
        "DelayTime": 0,
    },
    "WaterPV": {
        "Name": "WaterPV",
        "DisplayName": "Facility Water Proportional Valve 1 (PV1)",
        "Value": "0",
        "Unit": "%",
    },
}

trap_enable_key = {
    "W_CoolantSupplyTemperature": False,
    "A_CoolantSupplyTemperature": False,
    "W_CoolantSupplyTemperatureSpare": False,
    "A_CoolantSupplyTemperatureSpare": False,
    "W_CoolantReturnTemperature": False,
    "A_CoolantReturnTemperature": False,
    "W_WaterSupplyTemperature": False,
    "A_WaterSupplyTemperature": False,
    "W_WaterReturnTemperature": False,
    "A_WaterReturnTemperature": False,
    "W_CoolantSupplyPressure": False,
    "A_CoolantSupplyPressure": False,
    "W_CoolantSupplyPressureSpare": False,
    "A_CoolantSupplyPressureSpare": False,
    "W_CoolantReturnPressure": False,
    "A_CoolantReturnPressure": False,
    "W_CoolantReturnPressureSpare": False,
    "A_CoolantReturnPressureSpare": False,
    "W_FilterInletPressure": False,
    "A_FilterInletPressure": False,
    "W_Filter1OutletPressure": False,
    "A_Filter1OutletPressure": False,
    "W_Filter2OutletPressure": False,
    "A_Filter2OutletPressure": False,
    "W_Filter3OutletPressure": False,
    "A_Filter3OutletPressure": False,
    "W_Filter4OutletPressure": False,
    "A_Filter4OutletPressure": False,
    "W_Filter5OutletPressure": False,
    "A_Filter5OutletPressure": False,
    "W_WaterInletPressure": False,
    "A_WaterInletPressure": False,
    "W_WaterOutletPressure": False,
    "A_WaterOutletPressure": False,
    "W_RelativeHumidity": False,
    "A_RelativeHumidity": False,
    "W_AmbientTemperature": False,
    "A_AmbientTemperature": False,
    "W_DewPoint": False,
    "A_DewPoint": False,
    "W_CoolantFlowRate": False,
    "A_CoolantFlowRate": False,
    "W_WaterFlowRate": False,
    "A_WaterFlowRate": False,
    "W_pH": False,
    "A_pH": False,
    "W_Conductivity": False,
    "A_Conductivity": False,
    "W_Turbidity": False,
    "A_Turbidity": False,
    "W_AverageCurrent": False,
    "A_AverageCurrent": False,
}

max_min_value_location = {
    "Thr_W_CoolantSupplyTemperature_H": 1000,
    "Thr_A_CoolantSupplyTemperature_H": 1004,
    "Thr_W_CoolantSupplyTemperatureSpare_H": 1008,
    "Thr_A_CoolantSupplyTemperatureSpare_H": 1012,
    "Thr_W_CoolantReturnTemperature_H": 1016,
    "Thr_A_CoolantReturnTemperature_H": 1020,
    "Thr_W_WaterSupplyTemperature_L": 1024,
    "Thr_W_WaterSupplyTemperature_H": 1028,
    "Thr_A_WaterSupplyTemperature_L": 1032,
    "Thr_A_WaterSupplyTemperature_H": 1036,
    "Thr_W_WaterReturnTemperature_L": 1040,
    "Thr_W_WaterReturnTemperature_H": 1044,
    "Thr_A_WaterReturnTemperature_L": 1048,
    "Thr_A_WaterReturnTemperature_H": 1052,
    "Thr_W_CoolantSupplyPressure_H": 1056,
    "Thr_A_CoolantSupplyPressure_H": 1060,
    "Thr_W_CoolantSupplyPressureSpare_H": 1064,
    "Thr_A_CoolantSupplyPressureSpare_H": 1068,
    "Thr_W_CoolantReturnPressure_H": 1072,
    "Thr_A_CoolantReturnPressure_H": 1076,
    "Thr_W_CoolantReturnPressureSpare_H": 1080,
    "Thr_A_CoolantReturnPressureSpare_H": 1084,
    "Thr_W_FilterInletPressure_L": 1088,
    "Thr_W_FilterInletPressure_H": 1092,
    "Thr_A_FilterInletPressure_L": 1096,
    "Thr_A_FilterInletPressure_H": 1100,
    "Thr_W_Filter1OutletPressure_H": 1104,
    "Thr_A_Filter1OutletPressure_H": 1108,
    "Thr_W_Filter2OutletPressure_H": 1112,
    "Thr_A_Filter2OutletPressure_H": 1116,
    "Thr_W_Filter3OutletPressure_H": 1120,
    "Thr_A_Filter3OutletPressure_H": 1124,
    "Thr_W_Filter4OutletPressure_H": 1128,
    "Thr_A_Filter4OutletPressure_H": 1132,
    "Thr_W_Filter5OutletPressure_H": 1136,
    "Thr_A_Filter5OutletPressure_H": 1140,
    "Thr_W_WaterInletPressure_H": 1144,
    "Thr_A_WaterInletPressure_H": 1148,
    "Thr_W_WaterOutletPressure_H": 1152,
    "Thr_A_WaterOutletPressure_H": 1156,
    "Thr_W_RelativeHumidity_L": 1160,
    "Thr_W_RelativeHumidity_H": 1164,
    "Thr_A_RelativeHumidity_L": 1168,
    "Thr_A_RelativeHumidity_H": 1172,
    "Thr_W_AmbientTemperature_L": 1176,
    "Thr_W_AmbientTemperature_H": 1180,
    "Thr_A_AmbientTemperature_L": 1184,
    "Thr_A_AmbientTemperature_H": 1188,
    "Thr_W_DewPoint_L": 1192,
    "Thr_A_DewPoint_L": 1196,
    "Thr_W_CoolantFlowRate_L": 1200,
    "Thr_A_CoolantFlowRate_L": 1204,
    "Thr_W_WaterFlowRate_L": 1208,
    "Thr_A_WaterFlowRate_L": 1212,
    "Thr_W_pH_L": 1216,
    "Thr_A_pH_L": 1220,
    "Thr_W_pH_H": 1224,
    "Thr_A_pH_H": 1228,
    "Thr_W_Conductivity_L": 1232,
    "Thr_A_Conductivity_L": 1236,
    "Thr_W_Conductivity_H": 1240,
    "Thr_A_Conductivity_H": 1244,
    "Thr_W_Turbidity_L": 1248,
    "Thr_A_Turbidity_L": 1252,
    "Thr_W_Turbidity_H": 1256,
    "Thr_A_Turbidity_H": 1260,
    "Thr_W_AverageCurrent_H": 1264,
    "Thr_A_AverageCurrent_H": 1268,
}

sensor_thrshd = {
    "Thr_W_CoolantSupplyTemperature_H": 0,
    "Thr_W_Rst_CoolantSupplyTemperature_H": 0,
    "Thr_A_CoolantSupplyTemperature_H": 0,
    "Thr_A_Rst_CoolantSupplyTemperature_H": 0,
    "Thr_W_CoolantSupplyTemperatureSpare_H": 0,
    "Thr_W_Rst_CoolantSupplyTemperatureSpare_H": 0,
    "Thr_A_CoolantSupplyTemperatureSpare_H": 0,
    "Thr_A_Rst_CoolantSupplyTemperatureSpare_H": 0,
    "Thr_W_CoolantReturnTemperature_H": 0,
    "Thr_W_Rst_CoolantReturnTemperature_H": 0,
    "Thr_A_CoolantReturnTemperature_H": 0,
    "Thr_A_Rst_CoolantReturnTemperature_H": 0,
    "Thr_W_WaterSupplyTemperature_L": 0,
    "Thr_W_Rst_WaterSupplyTemperature_L": 0,
    "Thr_W_WaterSupplyTemperature_H": 0,
    "Thr_W_Rst_WaterSupplyTemperature_H": 0,
    "Thr_A_WaterSupplyTemperature_L": 0,
    "Thr_A_Rst_WaterSupplyTemperature_L": 0,
    "Thr_A_WaterSupplyTemperature_H": 0,
    "Thr_A_Rst_WaterSupplyTemperature_H": 0,
    "Thr_W_WaterReturnTemperature_L": 0,
    "Thr_W_Rst_WaterReturnTemperature_L": 0,
    "Thr_W_WaterReturnTemperature_H": 0,
    "Thr_W_Rst_WaterReturnTemperature_H": 0,
    "Thr_A_WaterReturnTemperature_L": 0,
    "Thr_A_Rst_WaterReturnTemperature_L": 0,
    "Thr_A_WaterReturnTemperature_H": 0,
    "Thr_A_Rst_WaterReturnTemperature_H": 0,
    "Thr_W_CoolantSupplyPressure_H": 0,
    "Thr_W_Rst_CoolantSupplyPressure_H": 0,
    "Thr_A_CoolantSupplyPressure_H": 0,
    "Thr_A_Rst_CoolantSupplyPressure_H": 0,
    "Thr_W_CoolantSupplyPressureSpare_H": 0,
    "Thr_W_Rst_CoolantSupplyPressureSpare_H": 0,
    "Thr_A_CoolantSupplyPressureSpare_H": 0,
    "Thr_A_Rst_CoolantSupplyPressureSpare_H": 0,
    "Thr_W_CoolantReturnPressure_H": 0,
    "Thr_W_Rst_CoolantReturnPressure_H": 0,
    "Thr_A_CoolantReturnPressure_H": 0,
    "Thr_A_Rst_CoolantReturnPressure_H": 0,
    "Thr_W_CoolantReturnPressureSpare_H": 0,
    "Thr_W_Rst_CoolantReturnPressureSpare_H": 0,
    "Thr_A_CoolantReturnPressureSpare_H": 0,
    "Thr_A_Rst_CoolantReturnPressureSpare_H": 0,
    "Thr_W_FilterInletPressure_L": 0,
    "Thr_W_Rst_FilterInletPressure_L": 0,
    "Thr_W_FilterInletPressure_H": 0,
    "Thr_W_Rst_FilterInletPressure_H": 0,
    "Thr_A_FilterInletPressure_L": 0,
    "Thr_A_Rst_FilterInletPressure_L": 0,
    "Thr_A_FilterInletPressure_H": 0,
    "Thr_A_Rst_FilterInletPressure_H": 0,
    "Thr_W_Filter1OutletPressure_H": 0,
    "Thr_W_Rst_Filter1OutletPressure_H": 0,
    "Thr_A_Filter1OutletPressure_H": 0,
    "Thr_A_Rst_Filter1OutletPressure_H": 0,
    "Thr_W_Filter2OutletPressure_H": 0,
    "Thr_W_Rst_Filter2OutletPressure_H": 0,
    "Thr_A_Filter2OutletPressure_H": 0,
    "Thr_A_Rst_Filter2OutletPressure_H": 0,
    "Thr_W_Filter3OutletPressure_H": 0,
    "Thr_W_Rst_Filter3OutletPressure_H": 0,
    "Thr_A_Filter3OutletPressure_H": 0,
    "Thr_A_Rst_Filter3OutletPressure_H": 0,
    "Thr_W_Filter4OutletPressure_H": 0,
    "Thr_W_Rst_Filter4OutletPressure_H": 0,
    "Thr_A_Filter4OutletPressure_H": 0,
    "Thr_A_Rst_Filter4OutletPressure_H": 0,
    "Thr_W_Filter5OutletPressure_H": 0,
    "Thr_W_Rst_Filter5OutletPressure_H": 0,
    "Thr_A_Filter5OutletPressure_H": 0,
    "Thr_A_Rst_Filter5OutletPressure_H": 0,
    "Thr_W_WaterInletPressure_H": 0,
    "Thr_W_Rst_WaterInletPressure_H": 0,
    "Thr_A_WaterInletPressure_H": 0,
    "Thr_A_Rst_WaterInletPressure_H": 0,
    "Thr_W_WaterOutletPressure_H": 0,
    "Thr_W_Rst_WaterOutletPressure_H": 0,
    "Thr_A_WaterOutletPressure_H": 0,
    "Thr_A_Rst_WaterOutletPressure_H": 0,
    "Thr_W_RelativeHumidity_L": 0,
    "Thr_W_Rst_RelativeHumidity_L": 0,
    "Thr_W_RelativeHumidity_H": 0,
    "Thr_W_Rst_RelativeHumidity_H": 0,
    "Thr_A_RelativeHumidity_L": 0,
    "Thr_A_Rst_RelativeHumidity_L": 0,
    "Thr_A_RelativeHumidity_H": 0,
    "Thr_A_Rst_RelativeHumidity_H": 0,
    "Thr_W_AmbientTemperature_L": 0,
    "Thr_W_Rst_AmbientTemperature_L": 0,
    "Thr_W_AmbientTemperature_H": 0,
    "Thr_W_Rst_AmbientTemperature_H": 0,
    "Thr_A_AmbientTemperature_L": 0,
    "Thr_A_Rst_AmbientTemperature_L": 0,
    "Thr_A_AmbientTemperature_H": 0,
    "Thr_A_Rst_AmbientTemperature_H": 0,
    "Thr_W_DewPoint_L": 0,
    "Thr_W_Rst_DewPoint_L": 0,
    "Thr_A_DewPoint_L": 0,
    "Thr_A_Rst_DewPoint_L": 0,
    "Thr_W_CoolantFlowRate_L": 0,
    "Thr_W_Rst_CoolantFlowRate_L": 0,
    "Thr_A_CoolantFlowRate_L": 0,
    "Thr_A_Rst_CoolantFlowRate_L": 0,
    "Thr_W_WaterFlowRate_L": 0,
    "Thr_W_Rst_WaterFlowRate_L": 0,
    "Thr_A_WaterFlowRate_L": 0,
    "Thr_A_Rst_WaterFlowRate_L": 0,
    "Thr_W_pH_L": 0,
    "Thr_W_Rst_pH_L": 0,
    "Thr_A_pH_L": 0,
    "Thr_A_Rst_pH_L": 0,
    "Thr_W_pH_H": 0,
    "Thr_W_Rst_pH_H": 0,
    "Thr_A_pH_H": 0,
    "Thr_A_Rst_pH_H": 0,
    "Thr_W_Conductivity_L": 0,
    "Thr_W_Rst_Conductivity_L": 0,
    "Thr_A_Conductivity_L": 0,
    "Thr_A_Rst_Conductivity_L": 0,
    "Thr_W_Conductivity_H": 0,
    "Thr_W_Rst_Conductivity_H": 0,
    "Thr_A_Conductivity_H": 0,
    "Thr_A_Rst_Conductivity_H": 0,
    "Thr_W_Turbidity_L": 0,
    "Thr_W_Rst_Turbidity_L": 0,
    "Thr_A_Turbidity_L": 0,
    "Thr_A_Rst_Turbidity_L": 0,
    "Thr_W_Turbidity_H": 0,
    "Thr_W_Rst_Turbidity_H": 0,
    "Thr_A_Turbidity_H": 0,
    "Thr_A_Rst_Turbidity_H": 0,
    "Thr_W_AverageCurrent_H": 0,
    "Thr_W_Rst_AverageCurrent_H": 0,
    "Thr_A_AverageCurrent_H": 0,
    "Thr_A_Rst_AverageCurrent_H": 0,
}

sensor_thrshd_delay_e = {
    "Delay_PV1Status": 0,
    "Delay_EV1Status": 0,
    "Delay_EV2Status": 0,
    "Delay_EV3Status": 0,
    "Delay_EV4Status": 0,
    "Delay_VFD1Overload": 0,
    "Delay_VFD2Overload": 0,
    "Delay_VFD1Status": 0,
    "Delay_VFD2Status": 0,
    "Delay_LeakDetectionLeak": 0,
    "Delay_LeakDetectionBroken": 0,
    "Delay_PowerSource": 0,
    "Delay_Inv1SpeedComm": 0,
    "Delay_Inv2SpeedComm": 0,
    "Delay_AmbientTemperatureComm": 0,
    "Delay_CoolantFlowRateComm": 0,
    "Delay_FacilityWaterFlowRateComm": 0,
    "Delay_ConductivityComm": 0,
    "Delay_pHComm": 0,
    "Delay_TurbidityComm": 0,
    "Delay_ATS1Comm": 0,
    "Delay_InstantPowerConsumptionComm": 0,
    "Delay_CoolantSupplyTemperatureBroken": 0,
    "Delay_CoolantSupplyTemperatureSpareBroken": 0,
    "Delay_CoolantReturnTemperatureBroken": 0,
    "Delay_WaterSupplyTemperatureBroken": 0,
    "Delay_WaterReturnTemperatureBroken": 0,
    "Delay_CoolantSupplyPressureBroken": 0,
    "Delay_CoolantSupplyPressureSpareBroken": 0,
    "Delay_CoolantReturnPressureBroken": 0,
    "Delay_CoolantReturnPressureSpareBroken": 0,
    "Delay_FilterInletPressureBroken": 0,
    "Delay_Filter1Status": 0,
    "Delay_Filter2Status": 0,
    "Delay_Filter3Status": 0,
    "Delay_Filter4Status": 0,
    "Delay_Filter5Status": 0,
    "Delay_WaterInletPressureBroken": 0,
    "Delay_WaterOutletPressureBroken": 0,
    "Delay_CoolantFlowRateBroken": 0,
    "Delay_WaterFlowRateBroken": 0,
    "Delay_Level1Error": 0,
    "Delay_Level2Error": 0,
    "Delay_Level3Error": 0,
    "Delay_Power1Error": 0,
    "Delay_Power2Error": 0,
}

sensor_thrshd_delay_s = {
    "Delay_CoolantSupplyTemperature": 0,
    "Delay_CoolantSupplyTemperatureSpare": 0,
    "Delay_CoolantReturnTemperature": 0,
    "Delay_WaterSupplyTemperature": 0,
    "Delay_WaterReturnTemperature": 0,
    "Delay_CoolantSupplyPressure": 0,
    "Delay_CoolantSupplyPressureSpare": 0,
    "Delay_CoolantReturnPressure": 0,
    "Delay_CoolantReturnPressureSpare": 0,
    "Delay_FilterInletPressure": 0,
    "Delay_Filter1OutletPressure": 0,
    "Delay_Filter2OutletPressure": 0,
    "Delay_Filter3OutletPressure": 0,
    "Delay_Filter4OutletPressure": 0,
    "Delay_Filter5OutletPressure": 0,
    "Delay_WaterInletPressure": 0,
    "Delay_WaterOutletPressure": 0,
    "Delay_RelativeHumidity": 0,
    "Delay_AmbientTemperature": 0,
    "Delay_DewPoint": 0,
    "Delay_CoolantFlowRate": 0,
    "Delay_WaterFlowRate": 0,
    "Delay_pH": 0,
    "Delay_Conductivity": 0,
    "Delay_Turbidity": 0,
    "Delay_AverageCurrent": 0,
}

app_value_mapping = {
    "CoolantSupplyTemperature": "temp_clntSply",
    "CoolantSupplyTemperatureSpare": "temp_clntSplySpr",
    "CoolantReturnTemperature": "temp_clntRtn",
    "WaterSupplyTemperature": "temp_waterIn",
    "WaterReturnTemperature": "temp_waterOut",
    "CoolantSupplyPressure": "prsr_clntSply",
    "CoolantSupplyPressureSpare": "prsr_clntSplySpr",
    "CoolantReturnPressure": "prsr_clntRtn",
    "CoolantReturnPressureSpare": "prsr_clntRtnSpr",
    "FilterInletPressure": "prsr_fltIn",
    "Filter1OutletPressure": "prsr_flt1Out",
    "Filter2OutletPressure": "prsr_flt2Out",
    "Filter3OutletPressure": "prsr_flt3Out",
    "Filter4OutletPressure": "prsr_flt4Out",
    "Filter5OutletPressure": "prsr_flt5Out",
    "WaterInletPressure": "prsr_wtrIn",
    "WaterOutletPressure": "prsr_wtrOut",
    "RelativeHumidity": "relative_humid",
    "AmbientTemperature": "temp_ambient",
    "DewPoint": "dew_point_temp",
    "CoolantFlowRate": "clnt_flow",
    "WaterFlowRate": "wtr_flow",
    "pH": "ph",
    "Conductivity": "cndct",
    "Turbidity": "tbd",
}

op_mode = {"Mode": "Stop"}
pump_speed_set = {"Pump1Speed": 0, "Pump2Speed": 0}
water_pv_set = {"WaterProportionalValve": 0}
temp_set = {"TemperatureSet": 0}
pressure_set = {"PressureSet": 0.5}
pump_swap_time = {"PumpSwapTime": 0}

unit_set = {"UnitSet": "Metric", "LastUnit": "Metric"}

all_filter_mode_set = {"all_filter_mode_set": False}

messages = {
    "warning": {
        "M100": ["Coolant Supply Temperature Over Range (High) Warning (T1)", False],
        "M101": [
            "Coolant Supply Temperature Spare Over Range (High) Warning (T1 sp)",
            False,
        ],
        "M102": ["Coolant Return Temperature Over Range (High) Warning (T2)", False],
        "M103": [
            "Facility Water Supply Temperature Over Range (Low) Warning (T4)",
            False,
        ],
        "M104": [
            "Facility Water Supply Temperature Over Range (High) Warning (T4)",
            False,
        ],
        "M105": [
            "Facility Water Return Temperature Over Range (Low) Warning (T5)",
            False,
        ],
        "M106": [
            "Facility Water Return Temperature Over Range (High) Warning (T5)",
            False,
        ],
        "M107": ["Coolant Supply Pressure Over Range (High) Warning (P1)", False],
        "M108": [
            "Coolant Supply Pressure Spare Over Range (High) Warning (P1 sp)",
            False,
        ],
        "M109": ["Coolant Return Pressure Over Range (High) Warning (P2)", False],
        "M110": ["Filter Inlet Pressure Over Range (Low) Warning (P3)", False],
        "M111": ["Filter Inlet Pressure Over Range (High) Warning (P3)", False],
        "M112": ["Filter1 Outlet Pressure Over Range (High) Warning (P4)", False],
        "M113": ["Filter2 Outlet Pressure Over Range (High) Warning (P5)", False],
        "M114": ["Filter3 Outlet Pressure Over Range (High) Warning (P6)", False],
        "M115": ["Filter4 Outlet Pressure Over Range (High) Warning (P7)", False],
        "M116": ["Filter5 Outlet Pressure Over Range (High) Warning (P8)", False],
        "M117": [
            "Facility Water Supply Pressure Over Range (High) Warning (P10)",
            False,
        ],
        "M118": [
            "Facility Water Return Pressure Over Range (High) Warning (P11)",
            False,
        ],
        "M119": ["Relative Humidity Over Range (Low) Warning (RH)", False],
        "M120": ["Relative Humidity Over Range (High) Warning (RH)", False],
        "M121": ["Ambient Temperature Over Range (Low) Warning (T a)", False],
        "M122": ["Ambient Temperature Over Range (High) Warning (T a)", False],
        "M123": ["Condensation Warning (T Dp)", False],
        "M124": ["Coolant Flow Rate (Low) Warning (F1)", False],
        "M125": ["Facility Water Flow Rate (Low) Warning (F2)", False],
        "M126": ["pH Over Range (Low) Warning (PH)", False],
        "M127": ["pH Over Range (High) Warning (PH)", False],
        "M128": ["Conductivity Over Range (Low) Warning (CON)", False],
        "M129": ["Conductivity Over Range (High) Warning (CON)", False],
        "M130": ["Turbidity Over Range (Low) Warning (Tur)", False],
        "M131": ["Turbidity Over Range (High) Warning (Tur)", False],
        "M132": ["Average Current Over Range (High) Warning", False],
        "M133": [
            "Coolant Return Pressure Spare Over Range (High) Warning (P2 sp)",
            False,
        ],
    },
    "alert": {
        "M200": ["Coolant Supply Temperature Over Range (High) Alert (T1)", False],
        "M201": [
            "Coolant Supply Temperature Spare Over Range (High) Alert (T1 sp)",
            False,
        ],
        "M202": ["Coolant Return Temperature Over Range (High) Alert (T2)", False],
        "M203": [
            "Facility Water Supply Temperature Over Range (Low) Alert (T4)",
            False,
        ],
        "M204": [
            "Facility Water Supply Temperature Over Range (High) Alert (T4)",
            False,
        ],
        "M205": [
            "Facility Water Return Temperature Over Range (Low) Alert (T5)",
            False,
        ],
        "M206": [
            "Facility Water Return Temperature Over Range (High) Alert (T5)",
            False,
        ],
        "M207": ["Coolant Supply Pressure Over Range (High) Alert (P1)", False],
        "M208": [
            "Coolant Supply Pressure Spare Over Range (High) Alert (P1 sp)",
            False,
        ],
        "M209": ["Coolant Return Pressure Over Range (High) Alert (P2)", False],
        "M210": ["Filter Inlet Pressure Over Range (Low) Alert (P3)", False],
        "M211": ["Filter Inlet Pressure Over Range (High) Alert (P3)", False],
        "M212": ["Filter1 Outlet Pressure Over Range (High) Alert (P4)", False],
        "M213": ["Filter2 Outlet Pressure Over Range (High) Alert (P5)", False],
        "M214": ["Filter3 Outlet Pressure Over Range (High) Alert (P6)", False],
        "M215": ["Filter4 Outlet Pressure Over Range (High) Alert (P7)", False],
        "M216": ["Filter5 Outlet Pressure Over Range (High) Alert (P8)", False],
        "M217": ["Facility Water Supply Pressure Over Range (High) Alert (P10)", False],
        "M218": ["Facility Water Return Pressure Over Range (High) Alert (P11)", False],
        "M219": ["Relative Humidity Over Range (Low) Alert (RH)", False],
        "M220": ["Relative Humidity Over Range (High) Alert (RH)", False],
        "M221": ["Ambient Temperature Over Range (Low) Alert (T a)", False],
        "M222": ["Ambient Temperature Over Range (High) Alert (T a)", False],
        "M223": ["Condensation Alert (T Dp)", False],
        "M224": ["Coolant Flow Rate (Low) Alert (F1)", False],
        "M225": ["Facility Water Flow Rate (Low) Alert (F2)", False],
        "M226": ["pH Over Range (Low) Alert (PH)", False],
        "M227": ["pH Over Range (High) Alert (PH)", False],
        "M228": ["Conductivity Over Range (Low) Alert (CON)", False],
        "M229": ["Conductivity Over Range (High) Alert (CON)", False],
        "M230": ["Turbidity Over Range (Low) Alert (Tur)", False],
        "M231": ["Turbidity Over Range (High) Alert (Tur)", False],
        "M232": ["Average Current Over Range (High) Alert", False],
        "M233": [
            "Coolant Return Pressure Spare Over Range (High) Alert (P2 sp)",
            False,
        ],
    },
    "error": {
        "M300": ["Facility Water Proportional Valve (PV1) Disconnection", False],
        "M301": ["Coolant Pump1 Inverter Overload", False],
        "M302": ["Coolant Pump2 Inverter Overload", False],
        "M303": ["Coolant Pump1 Inverter Error", False],
        "M304": ["Coolant Pump2 Inverter Error", False],
        "M305": ["Facility Water Leakage", False],
        "M306": ["Facility Water Leakage Sensor Broken", False],
        "M307": ["Coolant Pump1 Outlet Electrical Valve (EV1) Error", False],
        "M308": ["Coolant Pump1 Inlet Electrical Valve (EV2) Error", False],
        "M309": ["Coolant Pump2 Outlet Electrical Valve (EV3) Error", False],
        "M310": ["Coolant Pump2 Outlet Electrical Valve (EV4) Error", False],
        "M311": ["Factory Power Status", False],
        "M312": ["Inverter1 Communication Error", False],
        "M313": ["Inverter2 Communication Error", False],
        "M314": ["Ambient Sensor (T a) Communication Error", False],
        "M315": ["Coolant Flow Meter (F1) Communication Error", False],
        "M316": ["Water Flow Meter (F2) Communication Error", False],
        "M317": ["Conductivity (CON) Sensor Communication Error", False],
        "M318": ["pH (PH) Sensor Communication Error", False],
        "M319": ["Turbidity (Tur) Sensor Communication Error", False],
        "M320": ["ATS Communication Error", False],
        "M321": ["Power Meter Communication Error", False],
        "M322": ["Coolant Supply Temperature (T1) Broken Error", False],
        "M323": ["Coolant Supply Temperature (Spare) (T1 sp) Broken Error", False],
        "M324": ["Coolant Return Temperature (T2) Broken Error", False],
        "M325": ["Facility Water Supply Temperature (T4) Broken Error", False],
        "M326": ["Facility Water Return Temperature (T5) Broken Error", False],
        "M327": ["Coolant Supply Pressure (P1) Broken Error", False],
        "M328": ["Coolant Supply Pressure (Spare) (P1 sp) Broken Error", False],
        "M329": ["Coolant Return Pressure (P2) Broken Error", False],
        "M330": ["Filter Inlet Pressure (P3) Broken Error", False],
        "M331": ["Filter1 Outlet Pressure (P4) Broken Error", False],
        "M332": ["Filter2 Outlet Pressure (P5) Broken Error", False],
        "M333": ["Filter3 Outlet Pressure (P6) Broken Error", False],
        "M334": ["Filter4 Outlet Pressure (P7) Broken Error", False],
        "M335": ["Filter5 Outlet Pressure (P8) Broken Error", False],
        "M336": ["Facility Water Supply Pressure (P10) Broken Error", False],
        "M337": ["Facility Water Return Pressure (P11) Broken Error", False],
        "M338": ["Coolant Flow Rate (F1) Broken Error", False],
        "M339": ["Facility Water Flow Rate (F2) Broken Error", False],
        "M340": ["Stop Due to Low Coolant Level", False],
        "M341": ["Inverter 1 Error. Error Code:", False],
        "M342": ["Inverter 2 Error. Error Code:", False],
        "M343": ["PC1 Error", False],
        "M344": ["PC2 Error", False],
        "M345": ["Coolant Return Pressure (Spare) (P2 sp) Broken Error", False],
        "M346": ["Liquid Coolant Level 1 Error", False],
        "M347": ["Liquid Coolant Level 2 Error", False],
        "M348": ["Power Supply 1 Error", False],
        "M349": ["Power Supply 2 Error", False],
        "M350": ["Power Supply 3 Error", False],
        "M351": ["PLC Communication Broken Error", False],
    },
}

devices = {
    "PV1Status": {
        "Name": "PV1Status",
        "DisplayName": "Facility Water Proportional Valve 1 (PV1)",
        "Status": "Close",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "EV1Status": {
        "Name": "EV1Status",
        "DisplayName": "Electrical Valve 1 (EV1)",
        "Status": "Close",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "EV2Status": {
        "Name": "EV2Status",
        "DisplayName": "Electrical Valve 2 (EV2)",
        "Status": "Close",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "EV3Status": {
        "Name": "EV3Status",
        "DisplayName": "Electrical Valve 3 (EV3)",
        "Status": "Close",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "EV4Status": {
        "Name": "EV4Status",
        "DisplayName": "Electrical Valve 4 (EV4)",
        "Status": "Close",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "VFD1Overload": {
        "Name": "VFD1Overload",
        "DisplayName": "Inverter 1 Overload",
        "Status": "Disable",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "VFD2Overload": {
        "Name": "VFD2Overload",
        "DisplayName": "Inverter 2 Overload",
        "Status": "Disable",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "VFD1Status": {
        "Name": "VFD1Status",
        "DisplayName": "Inverter 1 Error",
        "Status": "Enable",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "VFD2Status": {
        "Name": "VFD2Status",
        "DisplayName": "Inverter 2 Error",
        "Status": "Disable",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "LeakDetectionLeak": {
        "Name": "LeakDetectionLeak",
        "DisplayName": "Leakage Sensor",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "LeakDetectionBroken": {
        "Name": "LeakDetectionBroken",
        "DisplayName": "Leakage Sensor",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "PowerSource": {
        "Name": "PowerSource",
        "DisplayName": "ATS",
        "Status": "Primary",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Inv1SpeedComm": {
        "Name": "Inv1SpeedCom",
        "DisplayName": "Inverter 1",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Inv2SpeedComm": {
        "Name": "Inv2SpeedComm",
        "DisplayName": "Inverter 2",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "AmbientTemperatureComm": {
        "Name": "AmbientTemperatureComm",
        "DisplayName": "Ambient Sensor",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantFlowRateComm": {
        "Name": "CoolantFlowRateComm",
        "DisplayName": "Coolant Flow Meter",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "FacilityWaterFlowRateComm": {
        "Name": "FacilityWaterFlowRateComm",
        "DisplayName": "Water Flow Meter",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "ConductivityComm": {
        "Name": "ConductivityComm",
        "DisplayName": "Conductivity Sensor",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "pHComm": {
        "Name": "pHComm",
        "DisplayName": "pH Sensor",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "TurbidityComm": {
        "Name": "TurbidityComm",
        "DisplayName": "Turbidity Sensor",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "ATS1Comm": {
        "Name": "ATS1Comm",
        "DisplayName": "ATS Communication",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "InstantPowerConsumptionComm": {
        "Name": "InstantPowerConsumptionComm",
        "DisplayName": "Power Meter",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantSupplyTemperatureBroken": {
        "Name": "CoolantSupplyTemperatureBroken",
        "DisplayName": "Coolant Supply Temperature (T1)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantSupplyTemperatureSpareBroken": {
        "Name": "CoolantSupplyTemperatureSpareBroken",
        "DisplayName": "Coolant Supply Temperature (Spare) (T1 sp)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantReturnTemperatureBroken": {
        "Name": "CoolantReturnTemperatureBroken",
        "DisplayName": "Coolant Return Temperature (T2)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "WaterSupplyTemperatureBroken": {
        "Name": "WaterSupplyTemperatureBroken",
        "DisplayName": "Facility Water Supply Temperature (T4)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "WaterReturnTemperatureBroken": {
        "Name": "WaterReturnTemperatureBroken",
        "DisplayName": "Facility Water Return Temperature (T5)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantSupplyPressureBroken": {
        "Name": "CoolantSupplyPressureBroken",
        "DisplayName": "Coolant Supply Pressure (P1)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantSupplyPressureSpareBroken": {
        "Name": "CoolantSupplyPressureSpareBroken",
        "DisplayName": "Coolant Supply Pressure (Spare) (P1 sp)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantReturnPressureBroken": {
        "Name": "CoolantReturnPressureBroken",
        "DisplayName": "Coolant Return Pressure (P2)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantReturnPressureSpareBroken": {
        "Name": "CoolantReturnPressureSpareBroken",
        "DisplayName": "Coolant Return Pressure (Spare) (P2 sp)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "FilterInletPressureBroken": {
        "Name": "FilterInletPressureBroken",
        "DisplayName": "Filter Inlet Pressure (P3)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Filter1Status": {
        "Name": "Filter1Status",
        "DisplayName": "Filter1 Status",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Filter2Status": {
        "Name": "Filter2Status",
        "DisplayName": "Filter2 Status",
        "Status": "Error",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Filter3Status": {
        "Name": "Filter3Status",
        "DisplayName": "Filter3 Status",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Filter4Status": {
        "Name": "Filter4Status",
        "DisplayName": "Filter4 Status",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Filter5Status": {
        "Name": "Filter5Status",
        "DisplayName": "Filter5 Status",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "WaterInletPressureBroken": {
        "Name": "WaterInletPressureBroken",
        "DisplayName": "Facility Water Supply Pressure (P10)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "WaterOutletPressureBroken": {
        "Name": "WaterOutletPressureBroken",
        "DisplayName": "Facility Water Return Pressure (P11)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "CoolantFlowRateBroken": {
        "Name": "CoolantFlowRateBroken",
        "DisplayName": "Coolant Flow Rate (F1)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "WaterFlowRateBroken": {
        "Name": "WaterFlowRateBroken",
        "DisplayName": "Facility Water Flow Rate (F2)",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "LowCoolantLevelWarning": {
        "Name": "LowCoolantLevelWarning",
        "DisplayName": "Low Coolant Level Warning",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Inv1ErrorCode": {
        "Name": "Inv1ErrorCode",
        "DisplayName": "Inverter 1 Error",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Inv2ErrorCode": {
        "Name": "Inv2ErrorCode",
        "DisplayName": "Inverter 2 Error",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "PC1Error": {
        "Name": "PC1Error",
        "DisplayName": "PC 1 Error",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "PC2Error": {
        "Name": "PC2Error",
        "DisplayName": "PC 2 Error",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Level1Error": {
        "Name": "Level1Error",
        "DisplayName": "Liquid Coolant Level 1",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Level2Error": {
        "Name": "Level2Error",
        "DisplayName": "Liquid Coolant Level 2",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Power1Error": {
        "Name": "Power1Error",
        "DisplayName": "Power Supply 1",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Power2Error": {
        "Name": "Power2Error",
        "DisplayName": "Power Supply 2",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "Level3Error": {
        "Name": "Level3Error",
        "DisplayName": "Liquid Coolant Level 3",
        "Status": "Good",
        "TrapEnabled": True,
        "DelayTime": 0,
    },
    "ControlUnit": {
        "Name": "ControlUnit",
        "DisplayName": "PLC",
        "Status": "Good",
        "TrapEnabled": True,
    },
}

physical_asset = {
    "FirmwareVersion": "1.0.0.0",
    "Version": "N/A",
    "ProductionDate": "20240730",
    "Manufacturer": "Supermicro",
    "Model": "1.3MW",
    "SerialNumber": "N/A",
    "PartNumber": "N/A",
    "AssetTag": "N/A",
    "CDUStatus": "Good",
}

snmp_data = {
    "trap_ip_address": "192.168.3.210",
    "v3_switch": False,
    "read_community": "Public",
}

trap_mapping = {
    "W_CoolantSupplyTemperature": 8192 + 2000,
    "A_CoolantSupplyTemperature": 8192 + 2001,
    "W_CoolantSupplyTemperatureSpare": 8192 + 2002,
    "A_CoolantSupplyTemperatureSpare": 8192 + 2003,
    "W_CoolantReturnTemperature": 8192 + 2004,
    "A_CoolantReturnTemperature": 8192 + 2005,
    "W_WaterSupplyTemperature": 8192 + 2006,
    "A_WaterSupplyTemperature": 8192 + 2007,
    "W_WaterReturnTemperature": 8192 + 2008,
    "A_WaterReturnTemperature": 8192 + 2009,
    "W_CoolantSupplyPressure": 8192 + 2010,
    "A_CoolantSupplyPressure": 8192 + 2011,
    "W_CoolantSupplyPressureSpare": 8192 + 2012,
    "A_CoolantSupplyPressureSpare": 8192 + 2013,
    "W_CoolantReturnPressure": 8192 + 2014,
    "A_CoolantReturnPressure": 8192 + 2015,
    "W_CoolantReturnPressureSpare": 8192 + 2016,
    "A_CoolantReturnPressureSpare": 8192 + 2017,
    "W_FilterInletPressure": 8192 + 2018,
    "A_FilterInletPressure": 8192 + 2019,
    "W_Filter1OutletPressure": 8192 + 2020,
    "A_Filter1OutletPressure": 8192 + 2021,
    "W_Filter2OutletPressure": 8192 + 2022,
    "A_Filter2OutletPressure": 8192 + 2023,
    "W_Filter3OutletPressure": 8192 + 2024,
    "A_Filter3OutletPressure": 8192 + 2025,
    "W_Filter4OutletPressure": 8192 + 2026,
    "A_Filter4OutletPressure": 8192 + 2027,
    "W_Filter5OutletPressure": 8192 + 2028,
    "A_Filter5OutletPressure": 8192 + 2029,
    "W_WaterInletPressure": 8192 + 2030,
    "A_WaterInletPressure": 8192 + 2031,
    "W_WaterOutletPressure": 8192 + 2032,
    "A_WaterOutletPressure": 8192 + 2033,
    "W_RelativeHumidity": 8192 + 2034,
    "A_RelativeHumidity": 8192 + 2035,
    "W_AmbientTemperature": 8192 + 2036,
    "A_AmbientTemperature": 8192 + 2037,
    "W_DewPoint": 8192 + 2038,
    "A_DewPoint": 8192 + 2039,
    "W_CoolantFlowRate": 8192 + 2040,
    "A_CoolantFlowRate": 8192 + 2041,
    "W_WaterFlowRate": 8192 + 2042,
    "A_WaterFlowRate": 8192 + 2043,
    "W_pH": 8192 + 2044,
    "A_pH": 8192 + 2045,
    "W_Conductivity": 8192 + 2046,
    "A_Conductivity": 8192 + 2047,
    "W_Turbidity": 8192 + 2048,
    "A_Turbidity": 8192 + 2049,
    "W_AverageCurrent": 8192 + 2050,
    "A_AverageCurrent": 8192 + 2051,
    "E_PV1Status": 8192 + 2052,
    "E_EV1Status": 8192 + 2053,
    "E_EV2Status": 8192 + 2054,
    "E_EV3Status": 8192 + 2055,
    "E_EV4Status": 8192 + 2056,
    "E_VFD1Overload": 8192 + 2057,
    "E_VFD2Overload": 8192 + 2058,
    "E_VFD1Status": 8192 + 2059,
    "E_VFD2Status": 8192 + 2060,
    "E_LeakDetectionLeak": 8192 + 2061,
    "E_LeakDetectionBroken": 8192 + 2062,
    "E_PowerSource": 8192 + 2063,
    "E_Inv1SpeedComm": 8192 + 2064,
    "E_Inv2SpeedComm": 8192 + 2065,
    "E_AmbientTemperatureComm": 8192 + 2066,
    "E_CoolantFlowRateComm": 8192 + 2067,
    "E_FacilityWaterFlowRateComm": 8192 + 2068,
    "E_ConductivityComm": 8192 + 2069,
    "E_pHComm": 8192 + 2070,
    "E_TurbidityComm": 8192 + 2071,
    "E_ATS1Comm": 8192 + 2072,
    "E_InstantPowerConsumptionComm": 8192 + 2073,
    "E_CoolantSupplyTemperatureBroken": 8192 + 2074,
    "E_CoolantSupplyTemperatureSpareBroken": 8192 + 2075,
    "E_CoolantReturnTemperatureBroken": 8192 + 2076,
    "E_WaterSupplyTemperatureBroken": 8192 + 2077,
    "E_WaterReturnTemperatureBroken": 8192 + 2078,
    "E_CoolantSupplyPressureBroken": 8192 + 2079,
    "E_CoolantSupplyPressureSpareBroken": 8192 + 2080,
    "E_CoolantReturnPressureBroken": 8192 + 2081,
    "E_CoolantReturnPressureSpareBroken": 8192 + 2082,
    "E_FilterInletPressureBroken": 8192 + 2083,
    "E_Filter1Status": 8192 + 2084,
    "E_Filter2Status": 8192 + 2085,
    "E_Filter3Status": 8192 + 2086,
    "E_Filter4Status": 8192 + 2087,
    "E_Filter5Status": 8192 + 2088,
    "E_WaterInletPressureBroken": 8192 + 2089,
    "E_WaterOutletPressureBroken": 8192 + 2090,
    "E_CoolantFlowRateBroken": 8192 + 2091,
    "E_WaterFlowRateBroken": 8192 + 2092,
    "E_LowCoolantLevelWarning": 8192 + 2093,
    "E_Inv1ErrorCode": 8192 + 2094,
    "E_Inv2ErrorCode": 8192 + 2095,
    "E_PC1Error": 8192 + 2096,
    "E_PC2Error": 8192 + 2097,
    "E_Level1Error": 8192 + 2098,
    "E_Level2Error": 8192 + 2099,
    "E_Level3Error": 8192 + 2100,
    "E_Power1Error": 8192 + 2101,
    "E_Power2Error": 8192 + 2102,
    "E_ControlUnit": 8192 + 2103,
}


error_message = {
    400: {"title": "Invalid content-type", "message": "Content type is not correct."},
    401: {"title": "Bad credential", "message": "Invalid username and password."},
    404: {"title": "Not Found", "message": "Specified URL doesn't exist."},
    405: {"title": "Invalid method", "message": "The method is not allowed."},
    503: {
        "title": "Server is busy",
        "message": "The communication between PC and PLC is temporarily broken.",
    },
}


def api_error_response(status_code):
    error_info = error_message.get(
        status_code, {"title": "Unknown Error", "message": "No details available."}
    )
    response = jsonify(
        {
            "error_code": status_code,
            "error_title": error_info["title"],
            "error_message": error_info["message"],
        }
    )
    response.status_code = status_code
    return response


def check_auth(username, password):
    """檢查是否為有效的用戶名和密碼"""
    return username == USERNAME and password == PASSWORD


def authenticate():
    """請求身份驗證"""
    return Response(
        "Authentication required.",
        401,
        {"WWW-Authenticate": "Basic realm='Login Required'"},
    )


def requires_auth(f):
    """裝飾器，要求路由使用基本驗證"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated_function


def check_server_busy():
    """模擬伺服器忙碌的條件"""

    return False


@app.errorhandler(404)
def handle_404_error(e):
    return api_error_response(404)


@app.errorhandler(405)
def handle_405_error(e):
    return api_error_response(405)


modbus_host = "192.168.3.250"
# modbus_host = "127.0.0.1"


modbus_port = 502
modbus_slave_id = 1


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


def cvt_registers_to_float(reg1, reg2):
    temp1 = [reg1, reg2]
    decoder_big_endian = BinaryPayloadDecoder.fromRegisters(
        temp1, byteorder=Endian.Big, wordorder=Endian.Little
    )
    decoded_value_big_endian = decoder_big_endian.decode_32bit_float()
    return decoded_value_big_endian


def input_p1(p1):
    with ModbusTcpClient(port=modbus_port, host=modbus_host) as client:
        word1, word2 = cvt_float_byte(float(p1))
        client.write_registers(246, [word2, word1])


def input_p2(p2):
    with ModbusTcpClient(port=modbus_port, host=modbus_host) as client:
        word1, word2 = cvt_float_byte(float(p2))
        client.write_registers(222, [word2, word1])


def input_water(water):
    with ModbusTcpClient(port=modbus_port, host=modbus_host) as client:
        word1, word2 = cvt_float_byte(float(water))
        client.write_registers(352, [word2, word1])


@scc_bp.route("/api/v1/1.3MW/cdu/control/op_mode")
@requires_auth
def get_op_mode():
    """Get operation mode setting of CDU"""

    mode = g.ctr_data["value"]["resultMode"]
    temp = g.ctr_data["value"]["resultTemp"]
    pressure = g.ctr_data["value"]["resultPressure"]
    p1 = g.ctr_data["value"]["resultP1"]
    p2 = g.ctr_data["value"]["resultP2"]
    water = g.ctr_data["value"]["resultWater"]
    ev1 = g.ctr_data["valve"]["resultEV1"]
    ev2 = g.ctr_data["valve"]["resultEV2"]
    ev3 = g.ctr_data["valve"]["resultEV3"]
    ev4 = g.ctr_data["valve"]["resultEV4"]

    if mode == "Auto":
        return jsonify(
            {
                "OperationMode": mode,
                "Settings": {
                    "TemperatureSet": round(temp),
                    "PressureSet": round(pressure, 1),
                },
            }
        )
    elif mode == "Manual":
        return jsonify(
            {
                "OperationMode": mode,
                "Settings": {
                    "Pump1Speed": round(p1),
                    "Pump2Speed": round(p2),
                    "WaterProportionalValve": round(water),
                },
            }
        )
    elif mode == "Engineer":
        return jsonify(
            {
                "OperationMode": mode,
                "Settings": {
                    "EV1": ev1,
                    "EV2": ev2,
                    "EV3": ev3,
                    "EV4": ev4,
                    "Pump1Speed": round(p1),
                    "Pump2Speed": round(p2),
                    "WaterProportionalValve": round(water),
                },
            }
        )
    elif mode == "Inspection" or mode == "Stop":
        return jsonify(
            {
                "Operation Mode": mode,
            }
        )


@scc_bp.route("/api/v1/1.3MW/cdu/control/op_mode", methods=["PATCH"])
@requires_auth
def patch_op_mode():
    """Set operation mode of CDU"""

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"missing error: {e}")
        return api_error_response(400)

    if not data:
        return api_error_response(400)

    settings = data.get("Settings", {})

    if "OperationMode" not in data.keys():
        return api_error_response(400)

    if not data.get("OperationMode"):
        return api_error_response(400)

    if data.get("OperationMode") not in ["Auto", "Stop", "Manual"]:
        return api_error_response(400)

    if settings.get("Pump1Speed") is not None and not isinstance(
        settings.get("Pump1Speed"), (int)
    ):
        return api_error_response(400)

    if settings.get("Pump2Speed") is not None and not isinstance(
        settings.get("Pump2Speed"), (int)
    ):
        return api_error_response(400)

    if settings.get("WaterProportionalValve") is not None and not isinstance(
        settings.get("WaterProportionalValve"), (int)
    ):
        return api_error_response(400)

    if settings.get("TemperatureSet") is not None and not isinstance(
        settings.get("TemperatureSet"), (int)
    ):
        return api_error_response(400)

    if settings.get("PressureSet") is not None and not isinstance(
        settings.get("PressureSet"), (int, float)
    ):
        return api_error_response(400)

    new_mode = data["OperationMode"]
    water = settings.get("WaterProportionalValve")
    p1 = settings.get("Pump1Speed")
    p2 = settings.get("Pump2Speed")
    current_p1 = g.ctr_data["value"]["resultP1"]
    current_p2 = g.ctr_data["value"]["resultP2"]
    temp = settings.get("TemperatureSet")
    pressure = settings.get("PressureSet")
    overload1 = g.sensorData["error"]["Inv1_OverLoad"]
    overload2 = g.sensorData["error"]["Inv2_OverLoad"]
    temp_upLmt = 0
    temp_lowLmt = 0
    prsr_upLmt = 0
    prsr_lowLmt = 0
    message = "Operation mode updated successfully"
    inv1_error = g.sensorData["error"]["Inv1_Error"]
    inv2_error = g.sensorData["error"]["Inv2_Error"]

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            result = client.read_coils(address=(8192 + 500), count=1)
        if result.bits[0]:
            temp_upLmt = 131
            temp_lowLmt = 95
            prsr_upLmt = 7.5 * 14.5
            prsr_lowLmt = 0
        else:
            temp_upLmt = 55
            temp_lowLmt = 35
            prsr_upLmt = 750
            prsr_lowLmt = 0

    except Exception as e:
        print(f"temp_set_limit: {e}")
        return api_error_response(503)

    if new_mode == "Auto":
        if temp is not None and pressure is not None:
            if not (temp_lowLmt <= temp <= temp_upLmt):
                return api_error_response(400)

            elif not (prsr_lowLmt <= pressure <= prsr_upLmt):
                return api_error_response(400)

    elif new_mode == "Manual":
        if water is not None:
            if water < 0 or water > 100:
                return api_error_response(400)

        if p1 is not None:
            if not (p1 == 0 or 25 <= p1 <= 100):
                return api_error_response(400)

        if p2 is not None:
            if not (p2 == 0 or 25 <= p2 <= 100):
                return api_error_response(400)

        if p1 is not None and p2 is not None:
            if p1 > 0 and p1 != p2 and p2 > 0:
                return api_error_response(400)

    try:
        with ModbusTcpClient(port=modbus_port, host=modbus_host) as client:
            if new_mode == "Stop":
                client.write_coils((8192 + 514), [False])
                op_logger.info(f"Operation mode updated successfully. {new_mode}")
                return jsonify(
                    {
                        "OperationMode": new_mode,
                    }
                )

            elif new_mode == "Manual":
                if p1 is not None and p2 is not None:
                    if p1 > 0 and p2 > 0 and p1 == p2:
                        if overload1 and overload2:
                            message = "Failed to turn on both pump due to overload"
                            p1 = 0
                            p2 = 0
                        elif overload1:
                            message = "Failed to turn on pump1 due to overload"
                            p1 = 0
                        elif overload2:
                            message = "Failed to turn on pump2 due to overload"
                            p2 = 0

                        if inv1_error:
                            message = "Failed to turn on pump1 due to inverter error"
                            p1 = 0

                        if inv2_error:
                            message = "Failed to turn on pump2 due to inverter error"
                            p2 = 0

                    elif p1 > 0 and p2 == 0:
                        if overload1 and overload2:
                            message = "Failed to turn on both pump due to overload"
                            p1 = 0

                        elif overload1:
                            message = "Failed to turn on pump1 due to overload"
                            p1 = 0

                        if inv1_error:
                            message = "Failed to turn on pump1 due to inverter error"
                            p1 = 0

                    elif p1 == 0 and p2 > 0:
                        if overload1 and overload2:
                            message = "Failed to turn on both pump due to overload"
                            p2 = 0

                        elif overload2:
                            message = "Failed to turn on pump2 due to overload"
                            p2 = 0

                        if inv2_error:
                            message = "Failed to turn on pump2 due to inverter error"
                            p2 = 0

                    input_p1(p1)
                    input_p2(p2)

                elif p1 is not None and p2 is None:
                    if p1 > 0:
                        if current_p2 != p1 and current_p2 != 0:
                            message = (
                                "Failed to turn on both pumps due to mismatch speed"
                            )
                        else:
                            input_p1(p1)

                        if overload1:
                            message = "Failed to turn on pump1 due to overload"
                            p1 = 0
                            input_p1(p1)

                        if inv1_error:
                            message = "Failed to turn on pump1 due to inverter error"
                            p1 = 0
                            input_p1(p1)
                    else:
                        input_p1(p1)

                elif p2 is not None and p1 is None:
                    if p2 > 0:
                        if current_p1 != p2 and current_p1 != 0:
                            message = (
                                "Failed to turn on both pumps due to mismatch speed"
                            )
                        else:
                            input_p2(p2)

                        if overload2:
                            message = "Failed to turn on pump2 due to overload"
                            p2 = 0
                            input_p2(p2)

                        if inv2_error:
                            message = "Failed to turn on pump2 due to inverter error"
                            p2 = 0
                            input_p2(p2)
                    else:
                        input_p2(p2)

                if water is not None:
                    input_water(water)

                client.write_coils((8192 + 505), [True])
                client.write_coils((8192 + 514), [True])
                client.write_coils((8192 + 516), [False])

                response_data = {
                    "OperationMode": new_mode,
                }

                settings = {
                    "Pump1Speed": p1,
                    "Pump2Speed": p2,
                    "WaterProportionalValve": water,
                }

                if message != "Operation mode updated successfully":
                    response_data["Message"] = message

                filtered_settings = {
                    key: value for key, value in settings.items() if value is not None
                }

                if filtered_settings:
                    response_data["Settings"] = filtered_settings

                op_logger.info(f"Operation mode updated successfully. {response_data}")
                return jsonify(response_data)

            elif new_mode == "Auto":
                unit = client.read_coils((8192 + 500), 1)

                if unit.bits[0]:
                    if temp is not None:
                        temp = (float(temp) - 32) / 9.0 * 5.0
                        temp1, temp2 = cvt_float_byte(temp)
                        client.write_registers(224, [temp2, temp1])

                    if pressure is not None:
                        pressure = float(temp) * 6.89476
                        prsr1, prsr2 = cvt_float_byte(pressure)
                        client.write_registers(226, [prsr2, prsr1])

                if temp is not None:
                    word7, word8 = cvt_float_byte(float(temp))
                    client.write_registers(993, [word8, word7])

                if pressure is not None:
                    word9, word10 = cvt_float_byte(float(pressure))
                    client.write_registers(991, [word10, word9])

                client.write_coils((8192 + 505), [False])
                client.write_coils((8192 + 514), [True])
                client.write_coils((8192 + 516), [False])

                response_data = {
                    "OperationMode": new_mode,
                }

                settings = {
                    "TemperatureSet": temp,
                    "PressureSet": pressure,
                }

                filtered_settings = {
                    key: value for key, value in settings.items() if value is not None
                }

                if filtered_settings:
                    response_data["Settings"] = filtered_settings

                op_logger.info(f"Operation mode updated successfully. {response_data}")
                return jsonify(response_data)

    except Exception as e:
        print(f"set mode error: {e}")
        return api_error_response(503)


@scc_bp.route("/api/v1/1.3MW/unit_set")
@requires_auth
def get_unit():
    """Get unit of CDU"""
    try:
        unit_set["UnitSet"] = g.system_data["value"]["unit"]
        unit_set["UnitSet"] = unit_set["UnitSet"].capitalize()
    except Exception as e:
        print(f"unit set error:{e}")
        return api_error_response(503)

    return jsonify({"UnitSet": unit_set["UnitSet"]})


def read_data_from_json():
    global \
        thrshd, \
        ctr_data, \
        measure_data, \
        thrshd_factory, \
        valve_setting, \
        valve_factory, \
        v2

    with open(f"{web_path}/json/thrshd.json", "r") as file:
        thrshd = json.load(file)

    with open(f"{web_path}/json/ctr_data.json", "r") as file:
        ctr_data = json.load(file)

    with open(f"{web_path}/json/measure_data.json", "r") as file:
        measure_data = json.load(file)

    with open(f"{web_path}/json/valve_setting.json", "r") as file:
        valve_setting = json.load(file)

    with open(f"{web_path}/json/version.json", "r") as file:
        data = json.load(file)
        v2 = not data["function_switch"]


def change_to_metric():
    read_data_from_json()

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
    thr_count = len(sensor_thrshd.keys())

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
            with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                client.write_registers(1000 + i * 64, group)
        except Exception as e:
            print(f"write register thrshd issue:{e}")

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
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(993, [temp2, temp1])
            client.write_registers(226, [temp2, temp1])
    except Exception as e:
        print(f"write oil temp error:{e}")

    prsr1, prsr2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(991, [prsr2, prsr1])
            client.write_registers(224, [prsr2, prsr1])
    except Exception as e:
        print(f"write oil pressure error:{e}")

    key_list = list(measure_data.keys())
    for key in key_list:
        if "Temp" in key:
            measure_data[key] = (measure_data[key] - 32) * 5.0 / 9.0

        if "Prsr" in key:
            measure_data[key] = measure_data[key] * 6.89476

        if "f1" in key or "f2" in key:
            measure_data[key] = measure_data[key] / 0.2642
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            for i, (key, value) in enumerate(measure_data.items()):
                word1, word2 = cvt_float_byte(value)
                registers = [word2, word1]
                client.write_registers(901 + i * 2, registers)
    except Exception as e:
        print(f"measure data input error:{e}")

    t1 = round((float(valve_setting["t1"]) - 32) * 5.0 / 9.0)
    ta = round((float(valve_setting["ta"]) - 32) * 5.0 / 9.0)

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(980, [t1, ta])
    except Exception as e:
        print(f"write t1 and ta:{e}")


def change_to_imperial():
    read_data_from_json()

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
    thr_count = len(sensor_thrshd.keys())

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
            with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                client.write_registers(1000 + i * 64, group)
        except Exception as e:
            print(f"write register thrshd issue:{e}")
        i += 1

    try:
        word1, word2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(224, [word2, word1])
    except Exception as e:
        print(f"write oil pressure error:{e}")

    try:
        word1, word2 = cvt_float_byte(ctr_data["value"]["oil_temp_set"])
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(226, [word2, word1])
    except Exception as e:
        print(f"write oil pressure error:{e}")

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
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(993, [temp2, temp1])
    except Exception as e:
        print(f"write oil temp error:{e}")

    pressure1, pressure2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(991, [pressure2, pressure1])
    except Exception as e:
        print(f"write oil pressure error:{e}")

    key_list = list(measure_data.keys())
    for key in key_list:
        if "Temp" in key:
            measure_data[key] = measure_data[key] * 9.0 / 5.0 + 32.0

        if "Prsr" in key:
            measure_data[key] = measure_data[key] * 0.145038

        if "f1" in key or "f2" in key:
            measure_data[key] = measure_data[key] * 0.2642

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            for i, (key, value) in enumerate(measure_data.items()):
                word1, word2 = cvt_float_byte(value)
                registers = [word2, word1]
                client.write_registers(901 + i * 2, registers)
    except Exception as e:
        print(f"measure data input error:{e}")

    t1 = round((valve_setting["t1"]) * 9.0 / 5.0 + 32.0)
    ta = round((valve_setting["ta"]) * 9.0 / 5.0 + 32.0)

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(980, [t1, ta])
    except Exception as e:
        print(f"write t1 and ta:{e}")


def change_data_by_unit():
    global system_data
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            last_unit = client.read_coils((8192 + 501), 1, unit=modbus_slave_id)
            current_unit = client.read_coils((8192 + 500), 1, unit=modbus_slave_id)

            last_unit = last_unit.bits[0]
            current_unit = current_unit.bits[0]

            if current_unit:
                unit_set["UnitSet"] = "imperial"
            else:
                unit_set["UnitSet"] = "metric"

            if last_unit:
                unit_set["LastUnit"] = "imperial"
            else:
                unit_set["LastUnit"] = "metric"

            if current_unit and current_unit != last_unit:
                change_to_imperial()
            elif not current_unit and current_unit != last_unit:
                change_to_metric()

            client.write_coils((8192 + 501), [current_unit])

    except Exception as e:
        print(f"unit set error:{e}")


def unit_set_scc(unit):
    if unit == "Metric":
        coil_value = False
    elif unit == "Imperial":
        coil_value = True

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_coil(address=(8192 + 500), value=coil_value)
    except Exception as e:
        print(f"write in unit error:{e}")
        return False

    try:
        change_data_by_unit()
    except Exception as e:
        print(f"write in unit error:{e}")
        return False

    op_logger.info("setting unit_set successfully")
    return True


@scc_bp.route("/api/v1/1.3MW/unit_set", methods=["PATCH"])
@requires_auth
def patch_unit():
    """Set unit of CDU"""

    try:
        data2 = request.get_json(force=True)
        new_unit = data2["UnitSet"]
    except Exception as e:
        print(f"unit set error:{e}")
        return api_error_response(400)

    if new_unit not in ["Metric", "Imperial"]:
        return api_error_response(400)

    unit_set["UnitSet"] = new_unit

    try:
        if unit_set_scc(new_unit):
            return jsonify(
                {
                    "UnitSet": new_unit,
                }
            )
        else:
            return api_error_response(503)

    except Exception as e:
        print(f"unit set error:{e}")
        return api_error_response(503)


@scc_bp.route("/api/v1/1.3MW/cdu/status/pump_filter_service_hours")
@requires_auth
def get_pump_filter_service_hours():
    """Get pump service hours"""
    try:
        data["pump_service_hours"]["Pump1ServiceHour"] = g.ctr_data["text"][
            "Pump1_run_time"
        ]
        data["pump_service_hours"]["Pump2ServiceHour"] = g.ctr_data["text"][
            "Pump2_run_time"
        ]

        data["filter_service_hours"]["Filter1ServiceHour"] = g.ctr_data["filter"]["f1"]
        data["filter_service_hours"]["Filter2ServiceHour"] = g.ctr_data["filter"]["f2"]
        data["filter_service_hours"]["Filter3ServiceHour"] = g.ctr_data["filter"]["f3"]
        data["filter_service_hours"]["Filter4ServiceHour"] = g.ctr_data["filter"]["f4"]
        data["filter_service_hours"]["Filter5ServiceHour"] = g.ctr_data["filter"]["f5"]

    except Exception as e:
        print(f"pump speed time error:{e}")
        return api_error_response(503)

    return jsonify(
        {
            "pump_service_hours": data["pump_service_hours"],
            "filter_service_hours": data["filter_service_hours"],
        }
    )


@scc_bp.route("/api/v1/1.3MW/cdu/status/pump_speed")
@requires_auth
def get_pump_speed_status():
    """Get pump speed of CDU"""
    try:
        p1 = g.sensorData["value"]["inv1_freq"]
        p2 = g.sensorData["value"]["inv2_freq"]

        if isinstance(p1, (int, float)):
            p1 = round(p1, 0)
        else:
            p1 = None

        if isinstance(p2, (int, float)):
            p2 = round(p2, 0)
        else:
            p2 = None

        data["pump_speed"]["Pump1Speed"] = p1
        data["pump_speed"]["Pump2Speed"] = p2

    except Exception as e:
        print(f"pump speed error:{e}")
        return api_error_response(503)

    return jsonify(data["pump_speed"])


@scc_bp.route("/api/v1/1.3MW/cdu/status/sensor_value")
@requires_auth
def get_sensor_value():
    """Get sensors value of CDU"""

    try:
        unit_set["UnitSet"] = g.system_data["value"]["unit"]

        if unit_set["UnitSet"] == "imperial":
            key_list = list(sensor_value_data.keys())
            for key in key_list:
                if "Temp" in key or "Dew" in key:
                    sensor_value_data[key]["Unit"] = "°F"
                if "Pressure" in key:
                    sensor_value_data[key]["Unit"] = "psi"
                if "Flow" in key:
                    sensor_value_data[key]["Unit"] = "GPM"

        elif unit_set["UnitSet"] == "metric":
            key_list = list(sensor_value_data.keys())
            for key in key_list:
                if "Temp" in key or "Dew" in key:
                    sensor_value_data[key]["Unit"] = "°C"
                if "Pressure" in key:
                    sensor_value_data[key]["Unit"] = "kPa"
                if "Flow" in key:
                    sensor_value_data[key]["Unit"] = "LPM"

        sensor_value_data["CoolantSupplyTemperature"]["Value"] = g.sensorData["value"][
            "temp_clntSply"
        ]
        sensor_value_data["CoolantSupplyTemperatureSpare"]["Value"] = g.sensorData[
            "value"
        ]["temp_clntSplySpr"]
        sensor_value_data["CoolantReturnTemperature"]["Value"] = g.sensorData["value"][
            "temp_clntRtn"
        ]
        sensor_value_data["WaterSupplyTemperature"]["Value"] = g.sensorData["value"][
            "temp_waterIn"
        ]
        sensor_value_data["WaterReturnTemperature"]["Value"] = g.sensorData["value"][
            "temp_waterOut"
        ]
        sensor_value_data["CoolantSupplyPressure"]["Value"] = g.sensorData["value"][
            "prsr_clntSply"
        ]
        sensor_value_data["CoolantSupplyPressureSpare"]["Value"] = g.sensorData[
            "value"
        ]["prsr_clntSplySpr"]
        sensor_value_data["CoolantReturnPressure"]["Value"] = g.sensorData["value"][
            "prsr_clntRtn"
        ]
        sensor_value_data["CoolantReturnPressureSpare"]["Value"] = g.sensorData[
            "value"
        ]["prsr_clntRtnSpr"]
        sensor_value_data["FilterInletPressure"]["Value"] = g.sensorData["value"][
            "prsr_fltIn"
        ]
        sensor_value_data["Filter1OutletPressure"]["Value"] = g.sensorData["value"][
            "prsr_flt1Out"
        ]
        sensor_value_data["Filter2OutletPressure"]["Value"] = g.sensorData["value"][
            "prsr_flt2Out"
        ]
        sensor_value_data["Filter3OutletPressure"]["Value"] = g.sensorData["value"][
            "prsr_flt3Out"
        ]
        sensor_value_data["Filter4OutletPressure"]["Value"] = g.sensorData["value"][
            "prsr_flt4Out"
        ]
        sensor_value_data["Filter5OutletPressure"]["Value"] = g.sensorData["value"][
            "prsr_flt5Out"
        ]
        sensor_value_data["WaterInletPressure"]["Value"] = g.sensorData["value"][
            "prsr_wtrIn"
        ]
        sensor_value_data["WaterOutletPressure"]["Value"] = g.sensorData["value"][
            "prsr_wtrOut"
        ]
        sensor_value_data["RelativeHumidity"]["Value"] = g.sensorData["value"]["rltHmd"]
        sensor_value_data["AmbientTemperature"]["Value"] = g.sensorData["value"][
            "temp_ambient"
        ]
        sensor_value_data["DewPoint"]["Value"] = g.sensorData["value"]["dewPt"]
        sensor_value_data["CoolantFlowRate"]["Value"] = g.sensorData["value"][
            "flow_clnt"
        ]
        sensor_value_data["WaterFlowRate"]["Value"] = g.sensorData["value"]["flow_wtr"]
        sensor_value_data["pH"]["Value"] = g.sensorData["value"]["pH"]
        sensor_value_data["Conductivity"]["Value"] = g.sensorData["value"]["cdct"]
        sensor_value_data["Turbidity"]["Value"] = g.sensorData["value"]["tbd"]
        sensor_value_data["InstantPowerConsumption"]["Value"] = g.sensorData["value"][
            "power"
        ]
        sensor_value_data["HeatCapacity"]["Value"] = g.sensorData["value"][
            "heat_capacity"
        ]
        sensor_value_data["AverageCurrent"]["Value"] = g.sensorData["value"]["AC"]
        sensor_value_data["WaterPV"]["Value"] = g.sensorData["value"]["WaterPV"]

        key_list = list(sensor_value_data.keys())

        for key in key_list:
            if "Value" in sensor_value_data[key]:
                value = sensor_value_data[key]["Value"]
                if key in ["CoolantFlowRate", "WaterFlowRate", "WaterPV"]:
                    sensor_value_data[key]["Value"] = int(value)
                else:
                    sensor_value_data[key]["Value"] = round(value, 1)
    except Exception as e:
        print(f"status value error:{e}")
        return api_error_response(503)

    try:
        key_list = list(sensor_value_data.keys())

        for key in key_list:
            sensor_value_data[key]["Status"] = "Good"
            v_key = app_value_mapping.get(key)
            if v_key:
                if g.sensorData["alert_notice"][v_key]:
                    sensor_value_data[key]["Status"] = "Alert"
                elif g.sensorData["warning_notice"][v_key]:
                    sensor_value_data[key]["Status"] = "Warning"

    except Exception as e:
        print(f"alert plc error: {e}")
        return api_error_response(503)

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            thr_regs = len(sensor_thrshd.keys()) * 2
            start_address = 1000
            total_registers = thr_regs
            read_num = 120

            for counted_num in range(0, total_registers, read_num):
                count = min(read_num, total_registers - counted_num)
                result = client.read_holding_registers(
                    start_address + counted_num, count
                )

                if not result.isError():
                    keys_list = list(sensor_thrshd.keys())
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
                            sensor_thrshd[keys_list[j]] = decoded_value_big_endian
                            j += 1

        thrshd_list = list(sensor_thrshd.keys())

        for key in thrshd_list:
            parts = key.split("_")
            short_key = parts[-2]

            if "Rst" not in key:
                if "W_" in key:
                    if "_L" in key:
                        sensor_value_data[short_key]["WarningLevel"]["MinValue"] = (
                            round((sensor_thrshd.get(key, None)), 1)
                        )
                    elif "_H" in key:
                        sensor_value_data[short_key]["WarningLevel"]["MaxValue"] = (
                            round(sensor_thrshd.get(key, None), 1)
                        )
                elif "A_" in key:
                    if "_L" in key:
                        sensor_value_data[short_key]["AlertLevel"]["MinValue"] = round(
                            sensor_thrshd.get(key, None), 1
                        )
                    elif "_H" in key:
                        sensor_value_data[short_key]["AlertLevel"]["MaxValue"] = round(
                            sensor_thrshd.get(key, None), 1
                        )
        try:
            with open("web/json/thrshd_scc.json", "w") as json_file:
                json.dump(sensor_thrshd, json_file, indent=4)
        except Exception as e:
            print(f"min max plc error: {e}")
            return api_error_response(503)

    except Exception as e:
        print(f"min max plc error: {e}")
        return api_error_response(503)

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            thr_count = len(trap_enable_key.keys())
            r = client.read_coils((8192 + 2000), thr_count)

            for x, key in enumerate(trap_enable_key.keys()):
                trap_enable_key[key] = r.bits[x]

            for key in sensor_value_data:
                w_key = f"W_{key}"
                a_key = f"A_{key}"

                if (
                    key != "HeatCapacity"
                    and key != "InstantPowerConsumption"
                    and key != "WaterPV"
                ):
                    sensor_value_data[key]["WarningLevel"]["TrapEnabled"] = (
                        trap_enable_key.get(w_key, False)
                    )
                    sensor_value_data[key]["AlertLevel"]["TrapEnabled"] = (
                        trap_enable_key.get(a_key, False)
                    )
    except Exception as e:
        print(f"read trap plc error: {e}")
        return api_error_response(503)

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            delay_count = len(sensor_thrshd_delay_s.keys())
            r = client.read_holding_registers(1000 + thr_regs, delay_count)

            i = 0

            for key, value in sensor_value_data.items():
                if key not in [
                    "InstantPowerConsumption",
                    "HeatCapacity",
                    "WaterPV",
                ]:
                    sensor_value_data[key]["DelayTime"] = r.registers[i]
                    i += 1

    except Exception as e:
        print(f"read delay plc error: {e}")
        return api_error_response(503)

    filter_data = copy.deepcopy(sensor_value_data)

    if not v2:
        filter_data.pop("CoolantReturnPressureSpare", None)

    output = [v for v in filter_data.values()]

    try:
        with open("web/json/scc.json", "w") as file:
            json.dump(filter_data, file, indent=4)
    except Exception as e:
        print(f"input error: {e}")
        return api_error_response(503)

    return output


@scc_bp.route("/api/v1/1.3MW/cdu/status/sensor_value", methods=["PATCH"])
@requires_auth
def set_sensor_config():
    """Set sensors value of CDU"""

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"read json issue: {e}")
        return api_error_response(400)

    if not data.get("Name") or data.get("Name") not in list(sensor_value_data.keys()):
        return api_error_response(400)

    AlertLevel = data.get("AlertLevel", {})
    WarningLevel = data.get("WarningLevel", {})

    if AlertLevel.get("TrapEnabled") is not None and not isinstance(
        AlertLevel.get("TrapEnabled"), bool
    ):
        return api_error_response(400)

    if (
        AlertLevel.get("MaxValue") is not None
        and AlertLevel.get("MaxValue") > 9007199254740991
        and not isinstance(AlertLevel.get("MaxValue"), (int, float))
    ):
        return api_error_response(400)

    if (
        AlertLevel.get("MinValue") is not None
        and AlertLevel.get("MinValue") > 9007199254740991
        and not isinstance(AlertLevel.get("MinValue"), (int, float))
    ):
        return api_error_response(400)

    if WarningLevel.get("TrapEnabled") is not None and not isinstance(
        WarningLevel.get("TrapEnabled"), bool
    ):
        return api_error_response(400)

    if (
        WarningLevel.get("MaxValue") is not None
        and WarningLevel.get("MaxValue") > 9007199254740991
        and not isinstance(WarningLevel.get("MaxValue"), (int, float))
    ):
        return api_error_response(400)

    if (
        WarningLevel.get("MinValue") is not None
        and WarningLevel.get("MinValue") > 9007199254740991
        and not isinstance(WarningLevel.get("MinValue"), (int, float))
    ):
        return api_error_response(400)

    if (
        data.get("DelayTime") is not None
        and data.get("DelayTime") > 30000
        and not isinstance(data.get("DelayTime"), (int))
    ):
        return api_error_response(400)

    sensor = data.get("Name")
    w_trap = WarningLevel.get("TrapEnabled")
    w_max = WarningLevel.get("MaxValue")
    w_min = WarningLevel.get("MinValue")
    a_trap = AlertLevel.get("TrapEnabled")
    a_max = AlertLevel.get("MaxValue")
    a_min = AlertLevel.get("MinValue")
    delay = data.get("DelayTime")
    unit_set["UnitSet"] = g.system_data["value"]["unit"]

    if (
        g.adjust["Temp_ClntSplySpr_Factor"] == 0
        and sensor == "CoolantSupplyTemperatureSpare"
        and (w_trap or a_trap)
    ):
        return api_error_response(405)

    if (
        g.adjust["Prsr_ClntSplySpr_Factor"] == 0
        and sensor == "CoolantSupplyPressureSpare"
        and (w_trap or a_trap)
    ):
        return api_error_response(405)

    if (
        (g.adjust["Prsr_ClntRtnSpr_Factor"] == 0)
        and sensor == "CoolantReturnPressureSpare"
        and (w_trap or a_trap)
    ):
        return api_error_response(405)

    if (not v2) and sensor == "CoolantReturnPressureSpare":
        return api_error_response(405)

    try:
        a_key = f"A_{sensor}"
        w_key = f"W_{sensor}"

        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            if w_trap is not None:
                client.write_coils(trap_mapping[a_key], [w_trap])
            if a_trap is not None:
                client.write_coils(trap_mapping[w_key], [a_trap])

        high_W_key = f"Thr_W_{sensor}_H"
        low_W_key = f"Thr_W_{sensor}_L"
        high_A_key = f"Thr_A_{sensor}_H"
        low_A_key = f"Thr_A_{sensor}_L"

        def convert_imperial(value):
            if value is not None:
                if "Temp" in sensor:
                    value = value * 9.0 / 5.0 + 32.0
                elif "Pressure" in sensor:
                    value = value * 0.145038
                elif "Flow" in sensor:
                    value = value * 0.2642
            return value

        if unit_set["UnitSet"] == "imperial":
            w_max = convert_imperial(w_max)
            w_min = convert_imperial(w_min)
            a_max = convert_imperial(a_max)
            a_min = convert_imperial(a_min)

        def update_threshold(key, value):
            if key in sensor_thrshd:
                sensor_thrshd[key] = value
                w1, w2 = cvt_float_byte(value)
                client.write_registers(max_min_value_location[key], [w2, w1])

        try:
            with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                if a_max is not None:
                    update_threshold(high_A_key, a_max)
                if a_min is not None:
                    update_threshold(low_A_key, a_min)
                if w_max is not None:
                    update_threshold(high_W_key, w_max)
                if w_min is not None:
                    update_threshold(low_W_key, w_min)
        except Exception as e:
            print(f"update max/min values: {e}")
            return api_error_response(503)

        if delay is not None:
            try:
                key_lists = list(sensor_thrshd_delay_s.keys())
                thr_regs = len(sensor_thrshd.keys()) * 2

                for i, key in enumerate(key_lists):
                    delay_key = f"Delay_{sensor}"
                    if delay_key == key:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            client.write_registers((1000 + thr_regs + i), delay)
            except Exception as e:
                print(f"update delay: {e}")
                return api_error_response(503)

        response_data = {"Name": sensor}

        warning = {"TrapEnabled": w_trap, "MinValue": w_min, "MaxValue": w_max}

        alert = {"TrapEnabled": a_trap, "MinValue": a_min, "MaxValue": a_max}

        filter_warning = {
            key: value for key, value in warning.items() if value is not None
        }

        filter_alert = {key: value for key, value in alert.items() if value is not None}

        if filter_warning:
            response_data["WarningLevel"] = filter_warning

        if filter_alert:
            response_data["AlertLevel"] = filter_alert

        if delay is not None:
            response_data["DelayTime"] = delay

        op_logger.info(f"Sensor Value updated successfully. {response_data}")
        return jsonify(response_data)

    except Exception as e:
        print(f"set sensor value error: {e}")
        return api_error_response(503)


@scc_bp.route("/api/v1/1.3MW/cdu/status/ev")
@requires_auth
def get_ev_status():
    """Get EV Status"""

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            r = client.read_discrete_inputs(4, 8)

            for i, key in enumerate(ev_on_off.keys()):
                ev_on_off[key] = r.bits[i]

    except Exception as e:
        print(f"read ev plc error: {e}")
        return api_error_response(503)

    for i in range(1, 5):
        if ev_on_off[f"ev{i}_open"] and not ev_on_off[f"ev{i}_close"]:
            ev_status[f"EV{i}"] = "Open"
        elif not ev_on_off[f"ev{i}_open"] and ev_on_off[f"ev{i}_close"]:
            ev_status[f"EV{i}"] = "Closed"
        else:
            ev_status[f"EV{i}"] = "-"

    return jsonify(ev_status)


@scc_bp.route("/api/v1/1.3MW/cdu/status/inverter")
@requires_auth
def get_inverter_status():
    """Get Inverter Status"""

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            r = client.read_coils(0, 2)
            inverter_status["Inverter1"] = r.bits[0]
            inverter_status["Inverter2"] = r.bits[1]
    except Exception as e:
        print(f"read inverter plc error: {e}")
        return api_error_response(503)

    for i in range(1, 3):
        inverter_status[f"Inverter{i}"] = (
            "On" if inverter_status[f"Inverter{i}"] else "Off"
        )

    return jsonify(inverter_status)


def is_valid_ip(ip):
    """
    驗證是否為合法的 IPv4 地址
    :param ip: IP 地址字串
    :return: True 表示合法, False 表示不合法
    """
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    if pattern.match(ip):
        parts = ip.split(".")
        return all(0 <= int(part) <= 255 for part in parts)
    return False


@scc_bp.route("/api/v1/1.3MW/snmp_setting", methods=["PATCH"])
@requires_auth
def snmp_setting():
    """Set SNMP Setting"""

    switch = request.json["V3_Switch"]
    name = request.json.get("Community")
    trapIp = request.json.get("Trap_Ip_Address")
    if not isinstance(switch, bool):
        return {"message": "Invalid input. V3 Switch accepts boolean values only."}

    if len(name) > 8:
        return jsonify(
            {"message": "Invalid input. Community name cannot exceed 8 characters."}
        )

    if trapIp and not is_valid_ip(trapIp):
        return jsonify(
            {"message": "Invalid input. Trap IP Address must be a valid IPv4 address."}
        )
    snmp_data["trap_ip_address"] = trapIp
    snmp_data["read_community"] = name
    snmp_data["v3_switch"] = switch
    with open(f"{snmp_path}/snmp/snmp.json", "w") as json_file:
        json.dump(snmp_data, json_file)

    op_logger.info("SNMP Setting updated successfully. ")
    return {
        "message": "SNMP Setting updated successfully",
        "Trap Ip Address": trapIp,
        "Read Community": name,
        "V3 Switch": switch,
    }


@scc_bp.route("/api/v1/1.3MW/get_snmp_setting")
@requires_auth
def get_snmp_setting():
    """Get SNMP Setting"""
    with open(f"{snmp_path}/snmp/snmp.json", "r") as file:
        data = json.load(file)
    snmp_data["trap_ip_address"] = data["trap_ip_address"]

    return jsonify(snmp_data)


@scc_bp.route("/api/v1/1.3MW/error_messages")
@requires_auth
def get_error_messages():
    """Get error messages of CDU"""

    try:
        key_mapping = {
            "M100": "temp_clntSply_high",
            "M101": "temp_clntSplySpr_high",
            "M102": "temp_clntRtn_high",
            "M103": "temp_waterIn_low",
            "M104": "temp_waterIn_high",
            "M105": "temp_waterOut_low",
            "M106": "temp_waterOut_high",
            "M107": "prsr_clntSply_high",
            "M108": "prsr_clntSplySpr_high",
            "M109": "prsr_clntRtn_high",
            "M110": "prsr_fltIn_low",
            "M111": "prsr_fltIn_high",
            "M112": "prsr_flt1Out_high",
            "M113": "prsr_flt2Out_high",
            "M114": "prsr_flt3Out_high",
            "M115": "prsr_flt4Out_high",
            "M116": "prsr_flt5Out_high",
            "M117": "prsr_wtrIn_high",
            "M118": "prsr_wtrOut_high",
            "M119": "relative_humid_low",
            "M120": "relative_humid_high",
            "M121": "temp_ambient_low",
            "M122": "temp_ambient_high",
            "M123": "dew_point_temp_low",
            "M124": "clnt_flow_low",
            "M125": "wtr_flow_low",
            "M126": "ph_low",
            "M127": "ph_high",
            "M128": "cndct_low",
            "M129": "cndct_high",
            "M130": "tbd_low",
            "M131": "tbd_high",
            "M132": "AC_high",
            "M133": "prsr_clntRtnSpr_high",
        }

        for msg_key, sensor_key in key_mapping.items():
            messages["warning"][msg_key][1] = g.sensorData["warning"][sensor_key]

        key_mapping = {
            "M200": "temp_clntSply_high",
            "M201": "temp_clntSplySpr_high",
            "M202": "temp_clntRtn_high",
            "M203": "temp_waterIn_low",
            "M204": "temp_waterIn_high",
            "M205": "temp_waterOut_low",
            "M206": "temp_waterOut_high",
            "M207": "prsr_clntSply_high",
            "M208": "prsr_clntSplySpr_high",
            "M209": "prsr_clntRtn_high",
            "M210": "prsr_fltIn_low",
            "M211": "prsr_fltIn_high",
            "M212": "prsr_flt1Out_high",
            "M213": "prsr_flt2Out_high",
            "M214": "prsr_flt3Out_high",
            "M215": "prsr_flt4Out_high",
            "M216": "prsr_flt5Out_high",
            "M217": "prsr_wtrIn_high",
            "M218": "prsr_wtrOut_high",
            "M219": "relative_humid_low",
            "M220": "relative_humid_high",
            "M221": "temp_ambient_low",
            "M222": "temp_ambient_high",
            "M223": "dew_point_temp_low",
            "M224": "clnt_flow_low",
            "M225": "wtr_flow_low",
            "M226": "ph_low",
            "M227": "ph_high",
            "M228": "cndct_low",
            "M229": "cndct_high",
            "M230": "tbd_low",
            "M231": "tbd_high",
            "M232": "AC_high",
            "M233": "prsr_clntRtnSpr_high",
        }

        for msg_key, sensor_key in key_mapping.items():
            messages["alert"][msg_key][1] = g.sensorData["alert"][sensor_key]

        key_mapping = {
            "M300": "Water_PV_Error",
            "M301": "Inv1_OverLoad",
            "M302": "Inv2_OverLoad",
            "M303": "Inv1_Error",
            "M304": "Inv2_Error",
            "M305": "Water_Leak",
            "M306": "Water_Leak_Broken",
            "M307": "EV1_Error",
            "M308": "EV2_Error",
            "M309": "EV3_Error",
            "M310": "EV4_Error",
            "M311": "ATS1",
            "M312": "Inv1_Com",
            "M313": "Inv2_Com",
            "M314": "Ambient_Sensor_Com",
            "M315": "Clnt_Flow_Com",
            "M316": "Wtr_Flow_Com",
            "M317": "Cndct_Sensor_Com",
            "M318": "ph_Com",
            "M319": "Tbd_Com",
            "M320": "ATS_Com",
            "M321": "Power_Meter_Com",
            "M322": "TempClntSply_broken",
            "M323": "TempClntSplySpr_broken",
            "M324": "TempClntRtn_broken",
            "M325": "TempWaterIn_broken",
            "M326": "TempWaterOut_broken",
            "M327": "PrsrClntSply_broken",
            "M328": "PrsrClntSplySpr_broken",
            "M329": "PrsrClntRtn_broken",
            "M330": "PrsrFltIn_broken",
            "M331": "PrsrFlt1Out_broken",
            "M332": "PrsrFlt2Out_broken",
            "M333": "PrsrFlt3Out_broken",
            "M334": "PrsrFlt4Out_broken",
            "M335": "PrsrFlt5Out_broken",
            "M336": "PrsrWaterIn_broken",
            "M337": "PrsrWaterOut_broken",
            "M338": "Clnt_Flow_broken",
            "M339": "Wtr_Flow_broken",
            "M340": "Low_Coolant_Level_Warning",
            "M341": "Inv1_error_code",
            "M342": "Inv2_error_code",
            "M343": "pc1_error",
            "M344": "pc2_error",
            "M345": "PrsrClntRtnSpr_broken",
            "M346": "level1_error",
            "M347": "level2_error",
            "M348": "power1_error",
            "M349": "power2_error",
            "M350": "level3_error",
            "M351": "PLC",
        }

        for msg_key, sensor_key in key_mapping.items():
            messages["error"][msg_key][1] = g.sensorData["error"][sensor_key]
    except Exception as e:
        print(f"error message issue:{e}")
        return api_error_response(503)

    if g.adjust["Temp_ClntSplySpr_Factor"] == 0:
        messages["warning"]["M101"][1] = False
        messages["alert"]["M201"][1] = False
        messages["error"]["M323"][1] = False

    if g.adjust["Prsr_ClntSplySpr_Factor"] == 0:
        messages["warning"]["M108"][1] = False
        messages["alert"]["M208"][1] = False
        messages["error"]["M328"][1] = False

    if g.adjust["Prsr_ClntRtnSpr_Factor"] == 0:
        messages["warning"]["M133"][1] = False
        messages["alert"]["M233"][1] = False
        messages["error"]["M345"][1] = False

    error_messages = []
    for category in ["warning", "alert", "error"]:
        for code, message in messages[category].items():
            if message[1]:
                error_messages.append({"ErrorCode": code, "Message": message[0]})

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            r = client.read_holding_registers(1750, 2)
            inv_error_code["code1"] = r.registers[0]
            inv_error_code["code2"] = r.registers[1]

    except Exception as e:
        print(f"inv error code: {e}")

    if inv_error_code["code1"] > 0:
        messages["error"]["M341"][0] = (
            f"M341 Inverter 1 Error. Error Code: {inv_error_code['code1']}"
        )

    if inv_error_code["code2"] > 0:
        messages["error"]["M342"][0] = (
            f"M342 Inverter 2 Error. Error Code: {inv_error_code['code2']}"
        )

    try:
        with open("web/json/scc_error.json", "w") as file:
            json.dump(error_messages, file, indent=4)
    except Exception as e:
        print(f"input error: {e}")
        return api_error_response(503)

    return error_messages


@scc_bp.route("/api/v1/1.3MW/devices", methods=["GET"])
@requires_auth
def get_devices():
    """GET Device Information"""

    exclude_keys = [
        "ControlUnit",
        "LowCoolantLevelWarning",
        "Inv1ErrorCode",
        "Inv2ErrorCode",
        "PC1Error",
        "PC2Error",
    ]

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            start_addr = len(sensor_thrshd.keys()) * 2 + len(
                sensor_thrshd_delay_s.keys()
            )
            device_delay_count = len(sensor_thrshd_delay_e.keys())

            r = client.read_holding_registers(1000 + start_addr, device_delay_count)
            count = 0

            d_list = list(devices.keys())
            for key in d_list:
                if key not in exclude_keys:
                    devices[key]["DelayTime"] = r.registers[count]
                    count += 1
    except Exception as e:
        print(f"read delay plc error: {e}")
        return api_error_response(503)

    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            start_addr = (len(sensor_trap.keys()) - 2) * 2
            device_trap_count = len(device_trap.keys())
            r = client.read_coils((8192 + 2000 + start_addr), device_trap_count)

            for i, key in enumerate(devices.keys()):
                devices[key]["TrapEnabled"] = r.bits[i]
    except Exception as e:
        print(f"trap enable error: {e}")
        return api_error_response(503)

    try:
        if g.sensorData["error"]["Low_Coolant_Level_Warning"]:
            devices["LowCoolantLevelWarning"]["Status"] = "Error"
        else:
            devices["LowCoolantLevelWarning"]["Status"] = "Good"

        if g.sensorData["error"]["Inv1_error_code"]:
            devices["Inv1ErrorCode"]["Status"] = "Error"
        else:
            devices["Inv1ErrorCode"]["Status"] = "Good"

        if g.sensorData["error"]["Inv2_error_code"]:
            devices["Inv2ErrorCode"]["Status"] = "Error"
        else:
            devices["Inv2ErrorCode"]["Status"] = "Good"

        if g.sensorData["error"]["pc1_error"]:
            devices["PC1Error"]["Status"] = "Error"
        else:
            devices["PC1Error"]["Status"] = "Good"

        if g.sensorData["error"]["pc2_error"]:
            devices["PC2Error"]["Status"] = "Error"
        else:
            devices["PC2Error"]["Status"] = "Good"

        if g.sensorData["error"]["level1_error"]:
            devices["Level1Error"]["Status"] = "Error"
        else:
            devices["Level1Error"]["Status"] = "Good"

        if g.sensorData["error"]["level2_error"]:
            devices["Level2Error"]["Status"] = "Error"
        else:
            devices["Level2Error"]["Status"] = "Good"

        if g.sensorData["error"]["level3_error"]:
            devices["Level3Error"]["Status"] = "Error"
        else:
            devices["Level3Error"]["Status"] = "Good"

        if g.sensorData["error"]["power1_error"]:
            devices["Power1Error"]["Status"] = "Error"
        else:
            devices["Power1Error"]["Status"] = "Good"

        if g.sensorData["error"]["power2_error"]:
            devices["Power2Error"]["Status"] = "Error"
        else:
            devices["Power2Error"]["Status"] = "Good"

    except Exception as e:
        print(f"read new devices error: {e}")
        return api_error_response(503)

    try:
        if g.sensorData["error"]["Water_PV_Error"]:
            devices["PV1Status"]["Status"] = "Error"
        else:
            devices["PV1Status"]["Status"] = "Good"

        ev_names = ["EV1", "EV2", "EV3", "EV4"]
        for ev in ev_names:
            if g.sensorData["error"][f"{ev}_Error"]:
                devices[f"{ev}Status"]["Status"] = "Error"
            elif g.sensorData["ev"][f"{ev}_Open"]:
                devices[f"{ev}Status"]["Status"] = "Open"
            else:
                devices[f"{ev}Status"]["Status"] = "Close"

        if g.sensorData["error"]["Water_Leak_Broken"]:
            devices["LeakDetectionBroken"]["Status"] = "Broken"
        else:
            devices["LeakDetectionBroken"]["Status"] = "Good"

        if g.sensorData["error"]["Water_Leak"]:
            devices["LeakDetectionLeak"]["Status"] = "Leak Detected"
        else:
            devices["LeakDetectionLeak"]["Status"] = "Good"

        inv_names = ["1", "2"]
        for inv in inv_names:
            if g.sensorData["error"][f"Inv{inv}_Error"]:
                devices[f"VFD{inv}Status"]["Status"] = "Error"
            elif g.sensorData["value"][f"inv{inv}_freq"]:
                devices[f"VFD{inv}Status"]["Status"] = "Enabled"
            else:
                devices[f"VFD{inv}Status"]["Status"] = "Disabled"

        overload_names = ["1", "2"]
        for o in overload_names:
            if g.sensorData["error"][f"Inv{o}_OverLoad"]:
                devices[f"VFD{o}Overload"]["Status"] = "Error"
            else:
                devices[f"VFD{o}Overload"]["Status"] = "Good"

        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            if not client.connect():
                devices["ControlUnit"]["Status"] = "Error"
            else:
                devices["ControlUnit"]["Status"] = "Good"

        if g.sensorData["ats_status"]["ATS1"]:
            devices["PowerSource"]["Status"] = "Primary"
        elif g.sensorData["ats_status"]["ATS2"]:
            devices["PowerSource"]["Status"] = "Secondary"
        else:
            devices["PowerSource"]["Status"] = "OFF"
    except Exception as e:
        print(f"read ats plc error: {e}")
        return api_error_response(503)

    try:
        sensor_mapping = {
            "CoolantSupplyTemperatureBroken": "TempClntSply_broken",
            "CoolantSupplyTemperatureSpareBroken": "TempClntSplySpr_broken",
            "CoolantReturnTemperatureBroken": "TempClntRtn_broken",
            "WaterSupplyTemperatureBroken": "TempWaterIn_broken",
            "WaterReturnTemperatureBroken": "TempWaterOut_broken",
            "CoolantSupplyPressureBroken": "PrsrClntSply_broken",
            "CoolantSupplyPressureSpareBroken": "PrsrClntSplySpr_broken",
            "CoolantReturnPressureBroken": "PrsrClntRtn_broken",
            "CoolantReturnPressureSpareBroken": "PrsrClntRtnSpr_broken",
            "FilterInletPressureBroken": "PrsrFltIn_broken",
            "WaterInletPressureBroken": "PrsrWaterIn_broken",
            "WaterOutletPressureBroken": "PrsrWaterOut_broken",
            "CoolantFlowRateBroken": "Clnt_Flow_broken",
            "WaterFlowRateBroken": "Wtr_Flow_broken",
        }

        for k, v in sensor_mapping.items():
            devices[k]["Status"] = "Error" if g.sensorData["error"][v] else "Good"

        filter_names = ["1", "2", "3", "4", "5"]
        for filter in filter_names:
            if g.sensorData["error"][f"PrsrFlt{filter}Out_broken"]:
                devices[f"Filter{filter}Status"]["Status"] = "Error"
            elif g.sensorData["alert_notice"][f"prsr_flt{filter}Out"]:
                devices[f"Filter{filter}Status"]["Status"] = "Alert"
            elif g.sensorData["warning_notice"][f"prsr_flt{filter}Out"]:
                devices[f"Filter{filter}Status"]["Status"] = "Warning"
            else:
                devices[f"Filter{filter}Status"]["Status"] = "Good"
    except Exception as e:
        print(f"read broken plc error: {e}")
        return api_error_response(503)

    try:
        sensor_mapping = {
            "Inv1SpeedComm": "Inv1_Com",
            "Inv2SpeedComm": "Inv2_Com",
            "AmbientTemperatureComm": "Ambient_Sensor_Com",
            "CoolantFlowRateComm": "Clnt_Flow_Com",
            "FacilityWaterFlowRateComm": "Wtr_Flow_Com",
            "ConductivityComm": "Cndct_Sensor_Com",
            "pHComm": "ph_Com",
            "TurbidityComm": "Tbd_Com",
            "ATS1Comm": "ATS_Com",
            "InstantPowerConsumptionComm": "Power_Meter_Com",
        }

        for k, v in sensor_mapping.items():
            devices[k]["Status"] = "Error" if g.sensorData["error"][v] else "Good"
    except Exception as e:
        print(f"read comm plc error: {e}")
        return api_error_response(503)

    filter_device_data = copy.deepcopy(devices)

    if not v2:
        filter_device_data.pop("CoolantReturnPressureSpareBroken", None)
        filter_device_data.pop("Level1Error", None)
        filter_device_data.pop("Level2Error", None)
        filter_device_data.pop("Level3Error", None)
        filter_device_data.pop("Power1Error", None)
        filter_device_data.pop("Power2Error", None)

    output = [d for d in filter_device_data.values()]

    try:
        with open("web/json/scc_device.json", "w") as file:
            json.dump(filter_device_data, file, indent=4)
    except Exception as e:
        return {"message": f"File Writing Error: {e}"}

    return output


@scc_bp.route("/api/v1/1.3MW/devices", methods=["PATCH"])
@requires_auth
def devices_set_trap_enable():
    """Set Device Trap Enable"""

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"device read error: {e}")
        return api_error_response(400)

    if not data or not data.get("Name"):
        return api_error_response(400)

    if data.get("Name") not in list(devices.keys()):
        return api_error_response(400)

    if data.get("TrapEnabled") is not None and not isinstance(
        data.get("TrapEnabled"), (bool)
    ):
        return api_error_response(400)

    if data.get("DelayTime") is not None and not isinstance(
        data.get("DelayTime"), (int)
    ):
        return api_error_response(400)

    name = data.get("Name", None)
    trap = data.get("TrapEnabled")
    delay = data.get("DelayTime")
    key = f"E_{name}"

    if (
        g.adjust["Temp_ClntSplySpr_Factor"] == 0
        and name == "CoolantSupplyTemperatureSpareBroken"
        and trap
    ):
        return api_error_response(405)

    if (
        g.adjust["Prsr_ClntSplySpr_Factor"] == 0
        and name == "CoolantSupplyPressureSpareBroken"
        and trap
    ):
        return api_error_response(405)

    if (
        (g.adjust["Prsr_ClntRtnSpr_Factor"] == 0 or not v2)
        and name == "CoolantReturnPressureSpareBroken"
        and trap
    ):
        return api_error_response(405)

    not_v2_exclude = [
        "CoolantReturnPressureSpareBroken",
        "Level1Error",
        "Level2Error",
        "Level3Error",
        "Power1Error",
        "Power2Error",
    ]

    if not v2 and name in not_v2_exclude:
        return api_error_response(405)

    if trap is not None:
        try:
            with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                client.write_coils(trap_mapping[key], [trap])
        except Exception as e:
            print(f"change trap plc error: {e}")
            return api_error_response(503)

    if delay is not None:
        if delay > 30000:
            return api_error_response(400)
        else:
            try:
                key_lists = list(sensor_thrshd_delay_e.keys())
                sensor_delay_count = len(sensor_thrshd_delay_s.keys())
                sensor_th_count = len(sensor_thrshd.keys()) * 2
                device_delay_start_addr = sensor_delay_count + sensor_th_count

                for i, key in enumerate(key_lists):
                    delay_key = f"Delay_{name}"
                    if delay_key == key:
                        with ModbusTcpClient(
                            host=modbus_host, port=modbus_port
                        ) as client:
                            client.write_registers(
                                (1000 + device_delay_start_addr + i), delay
                            )
            except Exception as e:
                print(f"update delay: {e}")
                return api_error_response(503)

    response_data = {"Name": name}

    settings = {"TrapEnabled": trap, "DelayTime": delay}

    filter_setting = {
        key: value for key, value in settings.items() if value is not None
    }

    if filter_setting:
        response_data.update(filter_setting)

    op_logger.info(f"Trap Enabled Setting updated successfully. {response_data} ")

    return jsonify(response_data)


@scc_bp.route("/api/v1/1.3MW/physical_asset")
@requires_auth
def get():
    """Get the physical asset information"""
    return physical_asset


@scc_bp.route("/api/v1/1.3MW/download_logs/error/<date_range>")
@requires_auth
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


@scc_bp.route("/api/v1/1.3MW/download_logs/operation/<date_range>")
@requires_auth
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


@scc_bp.route("/api/v1/1.3MW/download_logs/sensor/<date_range>")
@requires_auth
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


@scc_bp.route("/api/v1/1.3MW/cdu/status/water_pv")
@requires_auth
def get_water_pv_status():
    """Get opening of water proportional valve of CDU"""
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            r = client.read_holding_registers(5034, 2, unit=modbus_slave_id)
            result = cvt_registers_to_float(r.registers[0], r.registers[1])
            data["water_pv"]["WaterProportionalValve"] = round(result)
    except Exception as e:
        print(f"status water error:{e}")
        return api_error_response(503)

    return jsonify(
        {
            "WaterProportionalValve": data["water_pv"]["WaterProportionalValve"],
        }
    )


@scc_bp.route("/api/v1/1.3MW/upload_zip", methods=["POST"])
@requires_auth
def upload_zip_scc():
    """從 URL 中獲取檔案路徑並處理檔案上傳"""
    if "file" not in request.files:
        return jsonify({"message": "No File Part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"message": "No File Selected"}), 400

    if file.filename != "service.zip":
        return jsonify({"message": "Please upload correct file name"}), 400

    if not file.filename.endswith(".zip"):
        return jsonify({"message": "Wrong File Type or Missing Password"}), 400

    zip_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(zip_path)

    preset_password = "Itgs50848614"

    try:
        with pyzipper.AESZipFile(zip_path, "r", encryption=pyzipper.WZ_AES) as zip_ref:
            if not any(info.flag_bits & 0x1 for info in zip_ref.infolist()):
                os.remove(zip_path)
                return jsonify(
                    {"message": "A Password-Protected ZIP File is Required"}
                ), 400

            zip_ref.setpassword(preset_password.encode("utf-8"))
            try:
                first_file_name = zip_ref.namelist()[0]
                zip_ref.read(first_file_name)
                print("ZIP file is password protected and password is correct.")
            except RuntimeError:
                os.remove(zip_path)
                return jsonify({"message": "Invalid Password"}), 400

            os.makedirs(upload_path, exist_ok=True)
            zip_ref.extractall(upload_path)
    except Exception as e:
        print(f"Error extracting ZIP: {e}")
        os.remove(zip_path)
        return jsonify({"message": "Invalid Password or Invalid ZIP File"}), 500

    try:
        script_path = os.path.join(snmp_path, "restart.sh")

        if onLinux:
            result = subprocess.run(["bash", script_path], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"{result.returncode}")
            else:
                op_logger.info("Service restarted successfully")
                print("Service restarted successfully")
        else:
            print("Restart script skipped on Windows")

    except Exception as e:
        print("Error executing script:", e)
        return jsonify({"message": "Error executing script"}), 500

    os.remove(zip_path)

    op_logger.info("ZIP File Uploaded Successfully.")
    return jsonify({"message": "ZIP File Uploaded Successfully."})


def get_scc_data():
    global v2
    while True:
        try:
            sensor_trap_reg = (len(sensor_trap.keys()) - 2) * 2
            e_trap_reg = sum(1 for key in thrshd_factory if "E_" in key)
            with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                r = client.read_coils((8192 + 2000), sensor_trap_reg)

                for x, key in enumerate(trap_enable_key.keys()):
                    trap_enable_key[key] = r.bits[x]

                for key in sensor_value_data:
                    w_key = f"W_{key}"
                    a_key = f"A_{key}"
                    if (
                        key != "HeatCapacity"
                        and key != "InstantPowerConsumption"
                        and key != "WaterPV"
                    ):
                        sensor_trap[key]["Warning"] = trap_enable_key.get(w_key, None)
                        sensor_trap[key]["Alert"] = trap_enable_key.get(a_key, None)
        except Exception as e:
            print(f"[interval] read trap plc error: {e}")

        try:
            with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                r = client.read_coils((8192 + 2000 + sensor_trap_reg), e_trap_reg)

                for i, key in enumerate(device_trap.keys()):
                    device_trap[key] = r.bits[i]
        except Exception as e:
            print(f"[interval] trap enable error: {e}")

        scc_data = {
            "sensor_value_data": sensor_trap,
            "devices": device_trap,
        }

        try:
            with open(f"{web_path}/json/scc_data.json", "w") as file:
                json.dump(scc_data, file, indent=4)

            with open(f"{web_path}/json/version.json", "r") as file:
                data = json.load(file)
                v2 = not data["function_switch"]
        except Exception as e:
            print(f"input error: {e}")

        time.sleep(2)


scc_thread = threading.Thread(target=get_scc_data)
scc_thread.daemon = True
scc_thread.start()

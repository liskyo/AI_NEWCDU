from flask import Flask, jsonify
from flask_restx import Api, Resource, fields, Namespace
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from collections import OrderedDict
from pymodbus.payload import BinaryPayloadDecoder
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# from pymodbus.payload import BinaryPayloadBuilder
import struct
import json

log_path = os.path.dirname(os.getcwd())
print(f"log_path:{log_path}")
json_path = f"{log_path}/webUI/web/json"

app = Flask(__name__)
api = Api(app, version="0.6.6", title="CDU API", description="API for CDU system")

# 初始化 Limiter，使用 IP 地址作為限流的基準
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1 per second"],  # 預設限制每秒最多幾次
    app=app
)
# Define default namespace
default_ns = Namespace("api/v1", description="api for CDU system")


data = {
    "sensor_value": {
        "temp_coolant_supply": 0,
        "temp_coolant_supply_spare": 0,
        "temp_coolant_return": 0,
        "temp_ambient": 0,
        "relative_humid": 0,
        "dew_point": 0,
        "temp_water_supply": 0,
        "temp_water_return": 0,
        "pressure_coolant_supply": 0,
        "pressure_coolant_supply_spare": 0,
        "pressure_coolant_return": 0,
        "pressure_filter_in": 0,
        "pressure_filter1_out": 0,
        "pressure_filter2_out": 0,
        "pressure_filter3_out": 0,
        "pressure_filter4_out": 0,
        "pressure_filter5_out": 0,
        "pressure_qlt_out": 0,
        "pressure_water_in": 0,
        "pressure_water_out": 0,
        "flow_coolant": 0,
        "flow_water": 0,
        "pH": 0,
        "conductivity": 0,
        "Turbidity": 0,
        "heat_capacity": 0,
        "power_comsume": 0,
        "average_current": 0,
    },
    "unit": {
        "temperature": "celcius",
        "pressure": "bar",
        "flow": "LPM",
        "power": "kW",
        "heat_capacity": "kW",
    },
    "pump_speed": {"pump1_speed": 0, "pump2_speed": 0},
    "pump_service_hours": {
        "pump1_service_hours": 172,
        "pump2_service_hours": 169,
    },
    "pump_state": {"pump1_state": "Enable", "pump2_state": "Disable"},
    "pump_health": {"pump1_health": "OK", "pump2_health": "Critical"},
    "filter_service_hours": {
        "filter1_service_hours": 300,
        "filter2_service_hours": 300,
        "filter3_service_hours": 300,
        "filter4_service_hours": 300,
        "filter5_service_hours": 300,
        
    },
    "water_pv": {"water_PV": 0},
    "filter_mode": {
        "all_filter_sw": False,
    },
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
    },
    "CoolantSupplyTemperatureSpare": {
        "Name": "CoolantSupplyTemperatureSpare",
        "DisplayName": "Coolant Supply Temperature (Spare) (T1sp)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "60"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "65"},
    },
    "CoolantReturnTemperature": {
        "Name": "CoolantReturnTemperature",
        "DisplayName": "Coolant Return Temperature (T2)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "60"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "65"},
    },
    "WaterSupplyTemperature": {
        "Name": "WaterSupplyTemperature",
        "DisplayName": "Facility Water Inlet Temperature (T4)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "10", "MaxValue": "40"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "5", "MaxValue": "45"},
    },
    "WaterReturnTemperature": {
        "Name": "WaterReturnTemperature",
        "DisplayName": "Facility Water Outlet Temperature (T5)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "10", "MaxValue": "45"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "5", "MaxValue": "50"},
    },
    "CoolantSupplyPressure": {
        "Name": "CoolantSupplyPressure",
        "DisplayName": "Coolant Supply Pressure (P1)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "350"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "400"},
    },
    "CoolantSupplyPressureSpare": {
        "Name": "CoolantSupplyPressureSpare",
        "DisplayName": "Coolant Supply Pressure (Spare) (P1sp)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "350"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "400"},
    },
    "CoolantReturnPressure": {
        "Name": "CoolantReturnPressure",
        "DisplayName": "Coolant Return Pressure (P2)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
    },
    "FilterInletPressure": {
        "Name": "FilterInletPressure",
        "DisplayName": "Filter Inlet Pressure (P3)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "0", "MaxValue": "500"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "0", "MaxValue": "550"},
    },
    "Filter1OutletPressure": {
        "Name": "Filter1OutletPressure",
        "DisplayName": "Filter1 Outlet Pressure (P4)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
    },
    "Filter2OutletPressure": {
        "Name": "Filter2OutletPressure",
        "DisplayName": "Filter2 Outlet Pressure (P5)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
    },
    "Filter3OutletPressure": {
        "Name": "Filter3OutletPressure",
        "DisplayName": "Filter3 Outlet Pressure (P6)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
    },
    "Filter4OutletPressure": {
        "Name": "Filter4OutletPressure",
        "DisplayName": "Filter4 Outlet Pressure (P7)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
    },
    "Filter5OutletPressure": {
        "Name": "Filter5OutletPressure",
        "DisplayName": "Filter5 Outlet Pressure (P8)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
    },
    "CoolantQualitySensorOutletPressure": {
        "Name": "CoolantQualitySensorOutletPressure",
        "DisplayName": "Coolant Quality Meter Outlet Pressure (P9)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "150"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "200"},
    },
    "WaterInletPressure": {
        "Name": "WaterInletPressure",
        "DisplayName": "Facility Water Inlet Pressure (P10)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "750"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "800"},
    },
    "WaterOutletPressure": {
        "Name": "WaterOutletPressure",
        "DisplayName": "Facility Water Outlet Pressure (P11)",
        "Status": "Good",
        "Value": "1.23",
        "Unit": "kPa",
        "WarningLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "750"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": None, "MaxValue": "800"},
    },
    "RelativeHumidity": {
        "Name": "RelativeHumidity",
        "DisplayName": "Relative Humidity (RH)",
        "Status": "Good",
        "Value": "0",
        "Unit": "%",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "8.5", "MaxValue": "75"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "8", "MaxValue": "80"},
    },
    "AmbientTemperature": {
        "Name": "AmbientTemperature",
        "DisplayName": "Ambient Temperature (Ta)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "23", "MaxValue": "40"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "18", "MaxValue": "45"},
    },
    "DewPoint": {
        "Name": "DewPoint",
        "DisplayName": "Dew Point Temperature (Td)",
        "Status": "Good",
        "Value": "0",
        "Unit": "°C",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "5", "MaxValue": None},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "2"},
    },
    "CoolantFlowRate": {
        "Name": "CoolantFlowRate",
        "DisplayName": "Coolant Flow Rate (F1)",
        "Status": "Good",
        "Value": "0",
        "Unit": "LPM",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "30", "MaxValue": None},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "20", "MaxValue": None},
    },
    "WaterFlowRate": {
        "Name": "WaterFlowRate",
        "DisplayName": "Facility Water Flow Rate (F2)",
        "Status": "Good",
        "Value": "0",
        "Unit": "LPM",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "30", "MaxValue": None},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "20", "MaxValue": None},
    },
    "pH": {
        "Name": "pH",
        "DisplayName": "pH",
        "Status": "Good",
        "Value": "0",
        "Unit": "pH",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "7.2", "MaxValue": "7.9"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "7", "MaxValue": "8"},
    },
    "Conductivity": {
        "Name": "Conductivity",
        "DisplayName": "Conductivity",
        "Status": "Good",
        "Value": "0",
        "Unit": "µS/cm",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "4200", "MaxValue": "4600"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "4000", "MaxValue": "4700"},
    },
    "Turbidity": {
        "Name": "Turbidity",
        "DisplayName": "Turbidity",
        "Status": "Good",
        "Value": "0",
        "Unit": "NRU",
        "WarningLevel": {"TrapEnabled": True, "MinValue": "2", "MaxValue": "10"},
        "AlertLevel": {"TrapEnabled": True, "MinValue": "1", "MaxValue": "15"},
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
    },
    "WaterPV": {
        "Name": "WaterPV",
        "DisplayName": "Facility Water Proportional Valve 1 (PV1)",
        "Value": "0",
        "Unit": "%",
    },
}

trap_enable_key = {
    "W_CoolantSupplyTemperature": 0,
    "W_CoolantSupplyTemperatureSpare": 0,
    "W_CoolantReturnTemperature": 0,
    "W_WaterSupplyTemperature": 0,
    "W_WaterReturnTemperature": 0,
    "W_CoolantSupplyPressure": 0,
    "W_CoolantSupplyPressureSpare": 0,
    "W_CoolantReturnPressure": 0,
    "W_FilterInletPressure": 0,
    "W_Filter1OutletPressure": 0,
    "W_Filter2OutletPressure": 0,
    "W_Filter3OutletPressure": 0,
    "W_Filter4OutletPressure": 0,
    "W_Filter5OutletPressure": 0,
    "W_CoolantQualitySensorOutletPressure": 0,
    "W_WaterInletPressure": 0,
    "W_WaterOutletPressure": 0,
    "W_RelativeHumidity": 0,
    "W_AmbientTemperature": 0,
    "W_DewPoint": 0,
    "W_CoolantFlowRate": 0,
    "W_WaterFlowRate": 0,
    "W_pH": 0,
    "W_Conductivity": 0,
    "W_Turbidity": 0,
    "W_InstantPowerConsumption": 0,
    "W_HeatCapacity": 0,
    "W_AverageCurrent": 0,
    "A_CoolantSupplyTemperature": 0,
    "A_CoolantSupplyTemperatureSpare": 0,
    "A_CoolantReturnTemperature": 0,
    "A_WaterSupplyTemperature": 0,
    "A_WaterReturnTemperature": 0,
    "A_CoolantSupplyPressure": 0,
    "A_CoolantSupplyPressureSpare": 0,
    "A_CoolantReturnPressure": 0,
    "A_FilterInletPressure": 0,
    "A_Filter1OutletPressure": 0,
    "A_Filter2OutletPressure": 0,
    "A_Filter3OutletPressure": 0,
    "A_Filter4OutletPressure": 0,
    "A_Filter5OutletPressure": 0,
    "A_CoolantQualitySensorOutletPressure": 0,
    "A_WaterInletPressure": 0,
    "A_WaterOutletPressure": 0,
    "A_RelativeHumidity": 0,
    "A_AmbientTemperature": 0,
    "A_DewPoint": 0,
    "A_CoolantFlowRate": 0,
    "A_WaterFlowRate": 0,
    "A_pH": 0,
    "A_Conductivity": 0,
    "A_Turbidity": 0,
    "A_InstantPowerConsumption": 0,
    "A_HeatCapacity": 0,
    "A_AverageCurrent": 0,
}
system_data = {
    "value": {
        "unit": "metric",
        "last_unit": "metric",
    }
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
    "Thr_W_FilterInletPressure_L": 1080,
    "Thr_W_FilterInletPressure_H": 1084,
    "Thr_A_FilterInletPressure_L": 1088,
    "Thr_A_FilterInletPressure_H": 1092,
    "Thr_W_Filter1OutletPressure_H": 1096,
    "Thr_A_Filter1OutletPressure_H": 1100,
    "Thr_W_Filter2OutletPressure_H": 1104,
    "Thr_A_Filter2OutletPressure_H": 1108,
    "Thr_W_Filter3OutletPressure_H": 1112,
    "Thr_A_Filter3OutletPressure_H": 1116,
    "Thr_W_Filter4OutletPressure_H": 1120,
    "Thr_A_Filter4OutletPressure_H": 1124,
    "Thr_W_Filter5OutletPressure_H": 1128,
    "Thr_A_Filter5OutletPressure_H": 1132,
    "Thr_W_CoolantQualitySensorOutletPressure_H": 1136,
    "Thr_A_CoolantQualitySensorOutletPressure_H": 1140,
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
    "Thr_W_CoolantQualitySensorOutletPressure_H": 0,
    "Thr_W_Rst_CoolantQualitySensorOutletPressure_H": 0,
    "Thr_A_CoolantQualitySensorOutletPressure_H": 0,
    "Thr_A_Rst_CoolantQualitySensorOutletPressure_H": 0,
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

app_value_mapping = {
    "CoolantSupplyTemperature": "temp_clntSply",
    "CoolantSupplyTemperatureSpare": "temp_clntSplySpr",
    "CoolantReturnTemperature": "temp_clntRtn",
    "WaterSupplyTemperature": "temp_waterIn",
    "WaterReturnTemperature": "temp_waterOut",
    "CoolantSupplyPressure": "prsr_clntSply",
    "CoolantSupplyPressureSpare": "prsr_clntSplySpr",
    "CoolantReturnPressure": "prsr_clntRtn",
    "FilterInletPressure": "prsr_fltIn",
    "Filter1OutletPressure": "prsr_flt1Out",
    "Filter2OutletPressure": "prsr_flt2Out",
    "Filter3OutletPressure": "prsr_flt3Out",
    "Filter4OutletPressure": "prsr_flt4Out",
    "Filter5OutletPressure": "prsr_flt5Out",
    "CoolantQualitySensorOutletPressure": "prsr_wtrQltMtrOut",
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
pump_speed_set = {"pump1_speed": 0, "pump2_speed": 0}
water_pv_set = {"water_PV": 0}
temp_set = {"temp_set": 0}
pressure_set = {"pressure_set": 0.5}
pump_swap_time = {"pump_swap_time": 0}
unit_set = {"unit": "Metric"}

all_filter_mode_set = {"all_filter_mode_set": False}



messages = {
    "warning": {
        "M100": ["Coolant Supply Temperature Over Range (High) Warning (T1)", False],
        "M101": [
            "Coolant Supply Temperature Spare Over Range (High) Warning (T1sp)",
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
            "Coolant Supply Pressure Spare Over Range (High) Warning (P1sp)",
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
            "Coolant Quality Meter Outlet Pressure Over Range (High) Warning (P9)",
            False,
        ],
        "M118": [
            "Facility Water Inlet Pressure Over Range (High) Warning (P10)",
            False,
        ],
        "M119": [
            "Facility Water Outlet Pressure Over Range (High) Warning (P11)",
            False,
        ],
        "M120": ["Relative Humidity Over Range (Low) Warning (RH)", False],
        "M121": ["Relative Humidity Over Range (High) Warning (RH)", False],
        "M122": ["Ambient Temperature Over Range (Low) Warning (T3)", False],
        "M123": ["Ambient Temperature Over Range (High) Warning (T3)", False],
        "M124": ["Condensation Warning (Td)", False],
        "M125": ["Coolant Flow Rate (Low) Warning (F1)", False],
        "M126": ["Facility Water Flow Rate (Low) Warning (F2)", False],
        "M127": ["pH Over Range (Low) Warning (pH)", False],
        "M128": ["pH Over Range (High) Warning (pH)", False],
        "M129": ["Conductivity Over Range (Low) Warning (CON)", False],
        "M130": ["Conductivity Over Range (High) Warning (CON)", False],
        "M131": ["Turbidity Over Range (Low) Warning (Tur)", False],
        "M132": ["Turbidity Over Range (High) Warning (Tur)", False],
        "M133": ["Average Current Over Range (High) Warning(AC)", False],
    },
    "alert": {
        "M200": ["Coolant Supply Temperature Over Range (High) Alert (T1)", False],
        "M201": [
            "Coolant Supply Temperature Spare Over Range (High) Alert (T1sp)",
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
        "M208": ["Coolant Supply Pressure Spare Over Range (High) Alert (P1sp)", False],
        "M209": ["Coolant Return Pressure Over Range (High) Alert (P2)", False],
        "M210": ["Filter Inlet Pressure Over Range (Low) Alert (P3)", False],
        "M211": ["Filter Inlet Pressure Over Range (High) Alert (P3)", False],
        "M212": ["Filter1 Outlet Pressure Over Range (High) Alert (P4)", False],
        "M213": ["Filter2 Outlet Pressure Over Range (High) Alert (P5)", False],
        "M214": ["Filter3 Outlet Pressure Over Range (High) Alert (P6)", False],
        "M215": ["Filter4 Outlet Pressure Over Range (High) Alert (P7)", False],
        "M216": ["Filter5 Outlet Pressure Over Range (High) Alert (P8)", False],
        "M217": [
            "Coolant Quality Meter Outlet Pressure Over Range (High) Alert (P9)",
            False,
        ],
        "M218": ["Facility Water Inlet Pressure Over Range (High) Alert (P10)", False],
        "M219": ["Facility Water Outlet Pressure Over Range (High) Alert (P11)", False],
        "M220": ["Relative Humidity Over Range (Low) Alert (RH)", False],
        "M221": ["Relative Humidity Over Range (High) Alert (RH)", False],
        "M222": ["Ambient Temperature Over Range (Low) Alert (T3)", False],
        "M223": ["Ambient Temperature Over Range (High) Alert (T3)", False],
        "M224": ["Condensation Alert (Td)", False],
        "M225": ["Coolant Flow Rate (Low) Alert (F1)", False],
        "M226": ["Facility Water Flow Rate (Low) Alert (F2)", False],
        "M227": ["pH Over Range (Low) Alert (pH)", False],
        "M228": ["pH Over Range (High) Alert (pH)", False],
        "M229": ["Conductivity Over Range (Low) Alert (CON)", False],
        "M230": ["Conductivity Over Range (High) Alert (CON)", False],
        "M231": ["Turbidity Over Range (Low) Alert (Tur)", False],
        "M232": ["Turbidity Over Range (High) Alert (Tur)", False],
        "M233": ["Average Current Over Range (High) Alert (AC)", False],
    },
    "error": {
        "M300": ["Facility Water Proportional Valve Disconnection", False],
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
        "M312": ["Generator Power Status", False],
        "M313": ["PLC Communication Broken", False],
        "M314": ["Inverter1 Communication Error", False],
        "M315": ["Inverter2 Communication Error", False],
        "M316": ["Ambient Sensor Communication Error", False],
        "M317": ["Coolant Flow Meter Communication Error", False],
        "M318": ["Water Flow Meter Communication Error", False],
        "M319": ["Conductivity Sensor Communication Error", False],
        "M320": ["pH Sensor Communication Error", False],
        "M321": ["Turbidity Sensor Communication Error", False],
        "M322": ["ATS Communication Error", False],
        "M323": ["Power Meter Communication Error", False],
        "M324": ["Coolant Supply Temperature Error", False],
        "M325": ["Coolant Supply Temperature (Spare) Error", False],
        "M326": ["Coolant Return Temperature Error", False],
        "M327": ["Facility Water Supply Temperature Error", False],
        "M328": ["Facility Water Return Temperature Error", False],
        "M329": ["Coolant Supply Pressure Error", False],
        "M330": ["Coolant Supply Pressure (Spare) Error", False],
        "M331": ["Coolant Return Pressure Error", False],
        "M332": ["Filter Inlet Pressure Error", False],
        "M333": ["Filter1 Outlet Pressure Error", False],
        "M334": ["Filter2 Outlet Pressure Error", False],
        "M335": ["Filter3 Outlet Pressure Error", False],
        "M336": ["Filter4 Outlet Pressure Error", False],
        "M337": ["Filter5 Outlet Pressure Error", False],
        "M338": ["Coolant Quality Meter Outlet Pressure Broken Error", False],
        "M339": ["Facility Water Inlet Pressure Error", False],
        "M340": ["Facility Water Outlet Pressure Error", False],
        # "M341": ["Ambient Temperature Error", False],
        # "M342": ["Dew Point Temperature Error", False],
    },
}

devices = {
    "PV1Status": {
        "Name": "PV1Status",
        "DisplayName": "Facility Water Proportional Valve 1 (PV1)",
        "Status": "Close",
        "TrapEnabled": True,
    },
    "VFD1Overload": {
        "Name": "VFD1Overload",
        "DisplayName": "Inverter 1 Overload",
        "Status": "Disable",
        "TrapEnabled": True,
    },
    "VFD2Overload": {
        "Name": "VFD2Status",
        "DisplayName": "Inverter 2 Overload",
        "Status": "Disable",
        "TrapEnabled": True,
    },
    "VFD1Status": {
        "Name": "VFD1Status",
        "DisplayName": "Inverter 1 Error",
        "Status": "Enable",
        "TrapEnabled": True,
    },
    "VFD2Status": {
        "Name": "VFD2Status",
        "DisplayName": "Inverter 2 Error",
        "Status": "Disable",
        "TrapEnabled": True,
    },
    "LeakDetection": {
        "Name": "LeakDetection",
        "DisplayName": "Leakage Sensor/ Leakage Sensor Broken",
        "Status": "Good",
        "TrapEnabled_leak": True,
        "TrapEnabled_broken": True,
    },
    "EV1Status": {
        "Name": "EV1Status",
        "DisplayName": "Electrical Valve 1 (EV1)",
        "Status": "Close",
        "TrapEnabled": True,
    },
    "EV2Status": {
        "Name": "EV2Status",
        "DisplayName": "Electrical Valve 2 (EV2)",
        "Status": "Close",
        "TrapEnabled": True,
    },
    "EV3Status": {
        "Name": "EV3Status",
        "DisplayName": "Electrical Valve 3 (EV3)",
        "Status": "Close",
        "TrapEnabled": True,
    },
    "EV4Status": {
        "Name": "EV4Status",
        "DisplayName": "Electrical Valve 4 (EV4)",
        "Status": "Close",
        "TrapEnabled": True,
    },
    "PowerSource": {
        "Name": "PowerSource",
        "DisplayName": "Factory Power/ Generator Power",
        "Status": "Primary",
        "TrapEnabled_Factory": True,
        "TrapEnabled_Generator": True,
    },
    "ControlUnit": {
        "Name": "ControlUnit",
        "DisplayName": "PLC",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Inv1Speed_com": {
        "Name": "Inv1Speed_com",
        "DisplayName": "Inverter 1",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Inv2Speed_com": {
        "Name": "Inv2Speed_com",
        "DisplayName": "Inverter 2",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "AmbientTemperature_com": {
        "Name": "AmbientTemperature_com",
        "DisplayName": "Ambient Sensor",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantFlowRate_com": {
        "Name": "CoolantFlowRate_com",
        "DisplayName": "Coolant Flow Meter",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "FacilityWaterFlowRate_com": {
        "Name": "FacilityWaterFlowRate_com",
        "DisplayName": "Water Flow Meter",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Conductivity_com": {
        "Name": "Conductivity_com",
        "DisplayName": "Conductivity Sensor",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "pH_com": {
        "Name": "pH_com",
        "DisplayName": "pH Sensor",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Turbidity_com": {
        "Name": "Turbidity_com",
        "DisplayName": "Turbidity Sensor",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "ATS1_com": {
        "Name": "ATS1_com",
        "DisplayName": "ATS Communication",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "InstantPowerConsumption_com": {
        "Name": "InstantPowerConsumption_com",
        "DisplayName": "Power Meter",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantSupplyTemperature_broken": {
        "Name": "CoolantSupplyTemperature_broken",
        "DisplayName": "Coolant Supply Temperature (T1)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantSupplyTemperatureSpare_broken": {
        "Name": "CoolantSupplyTemperatureSpare_broken",
        "DisplayName": "Coolant Supply Temperature (Spare) (T1sp)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantReturnTemperature_broken": {
        "Name": "CoolantReturnTemperature_broken",
        "DisplayName": "Coolant Return Temperature (T2)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "WaterSupplyTemperature_broken": {
        "Name": "WaterSupplyTemperature_broken",
        "DisplayName": "Facility Water Inlet Temperature (T4)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "WaterReturnTemperature_broken": {
        "Name": "WaterReturnTemperature_broken",
        "DisplayName": "Facility Water Outlet Temperature (T5)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantSupplyPressure_broken": {
        "Name": "CoolantSupplyPressure_broken",
        "DisplayName": "Coolant Supply Pressure (P1)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantSupplyPressureSpare_broken": {
        "Name": "CoolantSupplyPressureSpare_broken",
        "DisplayName": "Coolant Supply Pressure (Spare) (P1sp)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantReturnPressure_broken": {
        "Name": "CoolantReturnPressure_broken",
        "DisplayName": "Coolant Return Pressure (P2)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "FilterInletPressure_broken": {
        "Name": "FilterInletPressure_broken",
        "DisplayName": "Filter Inlet Pressure (P3)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Filter1Status": {
        "Name": "Filter1Status",
        "DisplayName": "Filter1 Status",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Filter2Status": {
        "Name": "Filter2Status",
        "DisplayName": "Filter2 Status",
        "Status": "Error",
        "TrapEnabled": True,
    },
    "Filter3Status": {
        "Name": "Filter3Status",
        "DisplayName": "Filter3 Status",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Filter4Status": {
        "Name": "Filter4Status",
        "DisplayName": "Filter4 Status",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "Filter5Status": {
        "Name": "Filter5Status",
        "DisplayName": "Filter5 Status",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "CoolantQualitySensorOutletPressure_broken": {
        "Name": "CoolantQualitySensorOutletPressure_broken",
        "DisplayName": "Coolant Quality Meter Outlet Pressure (P9)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "WaterInletPressure_broken": {
        "Name": "WaterInletPressure_broken",
        "DisplayName": "Facility Water Inlet Pressure (P10)",
        "Status": "Good",
        "TrapEnabled": True,
    },
    "WaterOutletPressure_broken": {
        "Name": "WaterOutletPressure_broken",
        "DisplayName": "Facility Water Outlet Pressure (P11)",
        "Status": "Good",
        "TrapEnabled": True,
    },
}

physical_asset = {
    "FirmwareVersion": "0.1.1",
    "Version": "N/A",
    "ProductionDate": "20240730",
    "Manufacturer": "Supermicro",
    "Model": "1.3MW",
    "SerialNumber": "N/A",
    "PartNumber": "N/A",
    "AssetTag": "N/A",
    "CDUStatus": "Good",
}

snmp_data = {"v3_switch": False, "community": "Public"}

trap_mapping = {
    "W_CoolantSupplyTemperature": 2000,
    "W_CoolantSupplyTemperatureSpare": 2001,
    "W_CoolantReturnTemperature": 2002,
    "W_WaterSupplyTemperature": 2003,
    "W_WaterReturnTemperature": 2004,
    "W_CoolantSupplyPressure": 2005,
    "W_CoolantSupplyPressureSpare": 2006,
    "W_CoolantReturnPressure": 2007,
    "W_FilterInletPressure": 2008,
    "W_Filter1OutletPressure": 2009,
    "W_Filter2OutletPressure": 2010,
    "W_Filter3OutletPressure": 2011,
    "W_Filter4OutletPressure": 2012,
    "W_Filter5OutletPressure": 2013,
    "W_CoolantQualitySensorOutletPressure": 2014,
    "W_WaterInletPressure": 2015,
    "W_WaterOutletPressure": 2016,
    "W_RelativeHumidity": 2017,
    "W_AmbientTemperature": 2018,
    "W_DewPoint": 2019,
    "W_CoolantFlowRate": 2020,
    "W_WaterFlowRate": 2021,
    "W_pH": 2022,
    "W_Conductivity": 2023,
    "W_Turbidity": 2024,
    "W_InstantPowerConsumption": 2025,
    "W_HeatCapacity": 2026,
    "W_AverageCurrent": 2027,
    "A_CoolantSupplyTemperature": 2028,
    "A_CoolantSupplyTemperatureSpare": 2029,
    "A_CoolantReturnTemperature": 2030,
    "A_WaterSupplyTemperature": 2031,
    "A_WaterReturnTemperature": 2032,
    "A_CoolantSupplyPressure": 2033,
    "A_CoolantSupplyPressureSpare": 2034,
    "A_CoolantReturnPressure": 2035,
    "A_FilterInletPressure": 2036,
    "A_Filter1OutletPressure": 2037,
    "A_Filter2OutletPressure": 2038,
    "A_Filter3OutletPressure": 2039,
    "A_Filter4OutletPressure": 2040,
    "A_Filter5OutletPressure": 2041,
    "A_CoolantQualitySensorOutletPressure": 2042,
    "A_WaterInletPressure": 2043,
    "A_WaterOutletPressure": 2044,
    "A_RelativeHumidity": 2045,
    "A_AmbientTemperature": 2046,
    "A_DewPoint": 2047,
    "A_CoolantFlowRate": 2048,
    "A_WaterFlowRate": 2049,
    "A_pH": 2050,
    "A_Conductivity": 2051,
    "A_Turbidity": 2052,
    "A_InstantPowerConsumption": 2053,
    "A_HeatCapacity": 2054,
    "A_AverageCurrent": 2055,
    "E_PV1Status": 2056,
    "E_VFD1Overload": 2057,
    "E_VFD2Overload": 2058,
    "E_VFD1Status": 2059,
    "E_VFD2Status": 2060,
    "E_LeakDetection_leak": 2061,
    "E_LeakDetection_broken": 2062,
    "E_EV1Status": 2063,
    "E_EV2Status": 2064,
    "E_EV3Status": 2065,
    "E_EV4Status": 2066,
    "E_PowerSource_Factory": 2067,
    "E_PowerSource_Generator": 2068,
    "E_ControlUnit": 2069,
    "E_Inv1Speed_com": 2070,
    "E_Inv2Speed_com": 2071,
    "E_AmbientTemperature_com": 2072,
    "E_CoolantFlowRate_com": 2073,
    "E_FacilityWaterFlowRate_com": 2074,
    "E_Conductivity_com": 2075,
    "E_pH_com": 2076,
    "E_Turbidity_com": 2077,
    "E_ATS1_com": 2078,
    "E_InstantPowerConsumption_com": 2079,
    "E_CoolantSupplyTemperature_broken": 2080,
    "E_CoolantSupplyTemperatureSpare_broken": 2081,
    "E_CoolantReturnTemperature_broken": 2082,
    "E_WaterSupplyTemperature_broken": 2083,
    "E_WaterReturnTemperature_broken": 2084,
    "E_CoolantSupplyPressure_broken": 2085,
    "E_CoolantSupplyPressureSpare_broken": 2086,
    "E_CoolantReturnPressure_broken": 2087,
    "E_FilterInletPressure_broken": 2088,
    "E_Filter1Status": 2089,
    "E_Filter2Status": 2090,
    "E_Filter3Status": 2091,
    "E_Filter4Status": 2092,
    "E_Filter5Status": 2093,
    "E_CoolantQualitySensorOutletPressure_broken": 2094,
    "E_WaterInletPressure_broken": 2095,
    "E_WaterOutletPressure_broken": 2096,
}


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


# Define models for Swagger documentation
op_mode_model = default_ns.model(
    "OpMode",
    {
        "mode": fields.String(
            required=True,
            description="The operational mode",
            example="stop",
            enum=["stop", "manual", "auto", "engineer"],
        )
    },
)

pump_speed_model = default_ns.model(
    "PumpSpeed",
    {
        "pump1_speed": fields.Integer(
            description="Speed of pump 1", example=50, min=0, max=100
        ),
        "pump2_speed": fields.Integer(
            description="Speed of pump 2", example=50, min=0, max=100
        ),
    },
)

water_pv_model = default_ns.model(
    "WaterPV",
    {
        "water_PV": fields.Integer(
            description="Water proportional valve position", example=50, min=0, max=100
        )
    },
)

temp_set_model = default_ns.model(
    "TempSet",
    {
        "temp_set": fields.Integer(
            required=True,
            description="The temperature setting 35-55 deg celcius",
            example=40,
        )
    },
)

pressure_set_model = default_ns.model(
    "PressureSet",
    {
        "pressure_set": fields.Float(
            required=True, description="The pressure setting", example=1.0
        )
    },
)

pump_swap_time_model = default_ns.model(
    "PumpSwapTime",
    {
        "pump_swap_time": fields.Integer(
            description="Time interval for pump swapping in minutes",
            example=60,
            min=0,
            max=30000,
        )
    },
)

unit_set_model = default_ns.model(
    "UnitSet",
    {
        "unit_set": fields.String(
            required=True,
            description="The unit setting",
            example="metric",
            enum=["metric", "imperial"],
        )
    },
)

unit_model = default_ns.model(
    "Unit",
    {
        "temperature": fields.String(
            description="Temperature unit",
            example="celcius",
            enum=["celcius", "fehrenheit"],
        ),
        "pressure": fields.String(
            description="Pressure unit", example="kPa", enum=["kPa", "psi"]
        ),
        "flow": fields.String(
            description="Flow unit", example="LPM", enum=["LPM", "GPM"]
        ),
        "power": fields.String(description="Power unit", example="kW"),
        "heat_capacity": fields.String(description="Heat capacity unit", example="kW"),
    },
)

valve_model = default_ns.model(
    "ValveStatus",
    {
        "EV1": fields.Boolean(description="Status of BV1 valve", example=True),
        "EV2": fields.Boolean(description="Status of BV2 valve", example=False),
        "EV3": fields.Boolean(description="Status of BV3 valve", example=True),
        "EV4": fields.Boolean(description="Status of BV4 valve", example=True),
    },
)

message_model = default_ns.model(
    "ErrorMessages",
    {
        "error_code": fields.String(description="Error code"),
        "message": fields.String(description="Error message"),
    },
)

pump_service_hour_model = default_ns.model(
    "pump_service_hour_model",
    {
        "pump1_service_hour": fields.Integer(
            description="Pump1 Service Time in hours", example=171
        ),
        "pump2_service_hour": fields.Integer(
            description="Pump2 Service Time in hours", example=169
        ),
    },
)

pump_state_model = default_ns.model(
    "pump_state",
    {
        "pump1_state": fields.Integer(description="Pump1 State", example="Enable"),
        "pump2_state": fields.Integer(description="Pump2 State", example="Disable"),
    },
)

pump_health_model = default_ns.model(
    "pump_health",
    {
        "pump1_health": fields.Integer(description="Pump1 State", example="OK"),
        "pump2_health": fields.Integer(description="Pump2 State", example="Critical"),
    },
)

filter_service_hours_model = default_ns.model(
    "filter_service_hours_model",
    {
        "filter_service_hours": fields.Integer(
            description="Filter service time in hours", example=300
        )
    },
)
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
        "Thr_W_PrsrQltOut_H": 0,
        "Thr_W_Rst_PrsrQltOut_H": 0,
        "Thr_A_PrsrQltOut_H": 0,
        "Thr_A_Rst_PrsrQltOut_H": 0,
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
        "Delay_PrsrFltIn": 0,
        "Delay_PrsrFlt1Out": 0,
        "Delay_PrsrFlt2Out": 0,
        "Delay_PrsrFlt3Out": 0,
        "Delay_PrsrFlt4Out": 0,
        "Delay_PrsrFlt5Out": 0,
        "Delay_PrsrQltOut": 0,
        "Delay_PrsrWaterIn": 0,
        "Delay_PrsrWaterOut": 0,
        "Delay_WaterPV": 0,
        "Delay_RltvHmd": 0,
        "Delay_TempAmbient": 0,
        "Delay_TempCds": 0,
        "Delay_ClntFlow": 0,
        "Delay_WaterFlow": 0,
        "Delay_pH": 0,
        "Delay_Cdct": 0,
        "Delay_Tbt": 0,
        "Delay_AC": 0,
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
    }
)
ctr_data = {
    "value": {
        "opMod": "manual",
        "oil_temp_set": 0,
        "oil_pressure_set": 0,
        "pump1_speed": 0,
        "pump2_speed": 0,
        "water_PV": 0,
        "pump_swap_time": 0,
        "resultMode": "Auto",
        "resultTemp": 0,
        "resultPressure": 0,
        "resultP1": 0,
        "resultP2": 0,
        "resultWater": 0,
        # "resultPumpSwap": 0,
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
    "Prsr_FltIn_broken": 1,
    "Prsr_Flt1Out_broken": 1,
    "Prsr_Flt2Out_broken": 1,
    "Prsr_Flt3Out_broken": 1,
    "Prsr_Flt4Out_broken": 1,
    "Prsr_Flt5Out_broken": 1,
    "Prsr_WtrQltMtrOut_broken": 1,
    "Prsr_WtrIn_broken": 1,
    "Prsr_WtrOut_broken": 1,
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
    "Delay_PrsrClntSply": 0,
    "Delay_PrsrClntSplySpr": 0,
    "Delay_PrsrFlt1Out": 0,
    "Delay_PrsrFlt2Out": 0,
    "Delay_PrsrFlt3Out": 0,
    "Delay_PrsrFlt4Out": 0,
    "Delay_PrsrFlt5Out": 0,
    "Delay_PrsrFltIn": 0,
    "Delay_PrsrQltOut": 0,
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
    "Delay_Water_Leak_Broken": 10,
    "Delay_pH": 0,
    "Delay_pH_Sensor_Communication": 10,
    "Thr_A_AC_H": 45,
    "Thr_A_Cdct_H": 4700,
    "Thr_A_Cdct_L": 4000,
    "Thr_A_ClntFlow": 20,
    "Thr_A_PrsrClntRtn": 200,
    "Thr_A_PrsrClntSply": 400,
    "Thr_A_PrsrClntSplySpr": 400,
    "Thr_A_PrsrFlt1Out_H": 200,
    "Thr_A_PrsrFlt2Out_H": 200,
    "Thr_A_PrsrFlt3Out_H": 200,
    "Thr_A_PrsrFlt4Out_H": 200,
    "Thr_A_PrsrFlt5Out_H": 200,
    "Thr_A_PrsrFltIn_H": 550,
    "Thr_A_PrsrQltOut_H": 200,
    "Thr_A_PrsrWaterIn": 800,
    "Thr_A_PrsrWaterOut": 800,
    "Thr_A_RltvHmd_H": 80,
    "Thr_A_RltvHmd_L": 8,
    "Thr_A_Rst_AC_H": 40,
    "Thr_A_Rst_Cdct_H": 4650,
    "Thr_A_Rst_Cdct_L": 4100,
    "Thr_A_Rst_ClntFlow": 25,
    "Thr_A_Rst_PrsrClntRtn": 150,
    "Thr_A_Rst_PrsrClntSply": 350,
    "Thr_A_Rst_PrsrClntSplySpr": 350,
    "Thr_A_Rst_PrsrFlt1Out_H": 150,
    "Thr_A_Rst_PrsrFlt2Out_H": 150,
    "Thr_A_Rst_PrsrFlt3Out_H": 150,
    "Thr_A_Rst_PrsrFlt4Out_H": 150,
    "Thr_A_Rst_PrsrFlt5Out_H": 150,
    "Thr_A_Rst_PrsrFltIn_H": 500,
    "Thr_A_Rst_PrsrQltOut_H": 150,
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
    "Thr_W_PrsrClntSply": 350,
    "Thr_W_PrsrClntSplySpr": 350,
    "Thr_W_PrsrFlt1Out_H": 150,
    "Thr_W_PrsrFlt2Out_H": 150,
    "Thr_W_PrsrFlt3Out_H": 150,
    "Thr_W_PrsrFlt4Out_H": 150,
    "Thr_W_PrsrFlt5Out_H": 150,
    "Thr_W_PrsrFltIn_H": 500,
    "Thr_W_PrsrQltOut_H": 150,
    "Thr_W_PrsrWaterIn": 750,
    "Thr_W_PrsrWaterOut": 750,
    "Thr_W_RltvHmd_H": 75,
    "Thr_W_RltvHmd_L": 8.5,
    "Thr_W_Rst_AC_H": 35,
    "Thr_W_Rst_Cdct_H": 4500,
    "Thr_W_Rst_Cdct_L": 4300,
    "Thr_W_Rst_ClntFlow": 35,
    "Thr_W_Rst_PrsrClntRtn": 100,
    "Thr_W_Rst_PrsrClntSply": 300,
    "Thr_W_Rst_PrsrClntSplySpr": 300,
    "Thr_W_Rst_PrsrFlt1Out_H": 100,
    "Thr_W_Rst_PrsrFlt2Out_H": 100,
    "Thr_W_Rst_PrsrFlt3Out_H": 100,
    "Thr_W_Rst_PrsrFlt4Out_H": 100,
    "Thr_W_Rst_PrsrFlt5Out_H": 100,
    "Thr_W_Rst_PrsrFltIn_H": 450,
    "Thr_W_Rst_PrsrQltOut_H": 100,
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
}

def change_to_metric():
    # print(f"thrshd 數據（M）是：{thrshd}")
    with open(f"{json_path}/thrshd.json", "r") as json_file:
        thrshd = json.load(json_file)
    key_list = list(thrshd.keys())
    for key in key_list:
        if "Temp" in key and not key.startswith("Delay_") and "TempCds" not in key:
            thrshd[key] = (thrshd[key] - 32) * 5.0 / 9.0

        if "TempCds" in key and not key.startswith("Delay_"):
            thrshd[key] = thrshd[key] * 5.0 / 9.0

        if "Prsr" in key and not key.startswith("Delay_"):
            thrshd[key] = thrshd[key] * 6.89476

        if "Flow" in key and not key.startswith("Delay_"):
            thrshd[key] = thrshd[key] / 0.2642

    # 寫入 thrshd
    registers = []
    index = 0
    try:
        for key in thrshd.keys():
            value = thrshd[key]
            if index < 136:
                word1, word2 = cvt_float_byte(value)
                registers.append(word2)
                registers.append(word1)
            else:
                registers.append(int(value))
            index += 1

        grouped_register = [registers[i : i + 64] for i in range(0, len(registers), 64)]
    except Exception as e:
        print(f"問題{e}")
        return "Setting Value Error"

    try:
        i = 0
        for group in grouped_register:
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(1000 + i * 64, group)
            except Exception as e:
                print(f"write register thrshd issue:{e}")

            i += 1
    except Exception as e:
        print(f"input thrshd error:{e}")

    # 讀取 control 溫度與壓力
    with open(f"{json_path}/ctr_data.json", "r") as json_file:
        ctr_data = json.load(json_file)
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

    word1, word2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(224, [word2, word1])
    except Exception as e:
        print(f"write oil pressure error:{e}")
        return "Setting Fail. PLC Communication Error"

    word1, word2 = cvt_float_byte(ctr_data["value"]["oil_temp_set"])
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(226, [word2, word1])
    except Exception as e:
        print(f"write oil temp error:{e}")
        return "Setting Fail. PLC Communication Error"

    # 寫入 measure data
    with open(f"{json_path}/measure_data.json", "r") as json_file:
        measure_data = json.load(json_file)
    # print(f"轉換前數據：{measure_data}")
    key_list = list(measure_data.keys())
    for key in key_list:
        # print(f"轉換前溫度：{key}:{measure_data[key]}")
        if "Temp" in key:
            measure_data[key] = (measure_data[key] - 32) * 5.0 / 9.0

        if "Prsr" in key:
            measure_data[key] = measure_data[key] * 6.89476

        if "f1" in key or "f2" in key:
            measure_data[key] = measure_data[key] / 0.2642

        # print(f"轉換後溫度：{key}:{measure_data[key]}")
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            for i, (key, value) in enumerate(measure_data.items()):
                word1, word2 = cvt_float_byte(value)
                registers = [word2, word1]
                client.write_registers(901 + i * 2, registers)
    except Exception as e:
        print(f"measure data input error:{e}")
        return "Setting Fail. PLC Communication Error"

    # 更改 factory
    with open(f"{json_path}/thrshd_factory.json", "r") as json_file:
        thrshd_factory = json.load(json_file)
    key_list = list(thrshd_factory.keys())
    for key in key_list:
        if "Temp" in key and not key.startswith("Delay_") and "TempCds" not in key:
            thrshd_factory[key] = (thrshd_factory[key] - 32) * 5.0 / 9.0

        if "TempCds" in key and not key.startswith("Delay_"):
            thrshd_factory[key] = thrshd_factory[key] * 5.0 / 9.0

        if "Prsr" in key and not key.startswith("Delay_"):
            thrshd_factory[key] = thrshd_factory[key] * 6.89476

        if "Flow" in key and not key.startswith("Delay_"):
            thrshd_factory[key] = thrshd_factory[key] / 0.2642


def change_to_imperial():
    # 英制加成 thrshd
    with open(f"{json_path}/thrshd.json", "r") as json_file:
        thrshd = json.load(json_file)
    key_list = list(thrshd.keys())
    for key in key_list:
        if "Temp" in key and not key.startswith("Delay_") and "TempCds" not in key:
            thrshd[key] = thrshd[key] * 9.0 / 5.0 + 32.0

        if "TempCds" in key and not key.startswith("Delay_"):
            thrshd[key] = thrshd[key] * 9.0 / 5.0

        if "Prsr" in key and not key.startswith("Delay_"):
            thrshd[key] = thrshd[key] * 0.145038

        if "Flow" in key and not key.startswith("Delay_"):
            thrshd[key] = thrshd[key] * 0.2642

    # 重新寫入 thrshd
    registers = []
    index = 0
    try:
        for key in thrshd.keys():
            value = thrshd[key]
            if index < 136:
                word1, word2 = cvt_float_byte(value)
                registers.append(word2)
                registers.append(word1)
            else:
                registers.append(int(value))
            index += 1

        grouped_register = [registers[i : i + 64] for i in range(0, len(registers), 64)]

    except Exception as e:
        print(f"問題{e}")
        return "Setting Value Error"
    try:
        i = 0
        for group in grouped_register:
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(1000 + i * 64, group)
            except Exception as e:
                print(f"write register thrshd issue:{e}")
            i += 1
    except Exception as e:
        print(f"input thrshd error:{e}")

    # 英制加成 Control 溫度與壓力＋重新寫入
    with open(f"{json_path}/ctr_data.json", "r") as json_file:
        ctr_data = json.load(json_file)
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

    word1, word2 = cvt_float_byte(ctr_data["value"]["oil_pressure_set"])
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(224, [word2, word1])
    except Exception as e:
        print(f"write oil pressure error:{e}")
        return "Setting Fail. PLC Communication Error"

    word1, word2 = cvt_float_byte(ctr_data["value"]["oil_temp_set"])
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            client.write_registers(226, [word2, word1])
    except Exception as e:
        print(f"write oil temp error:{e}")
        return "Setting Fail. PLC Communication Error"

    # 寫入 measure data
    with open(f"{json_path}/measure_data.json", "r") as json_file:
        measure_data = json.load(json_file)
    # print(f"轉換前數據：{measure_data}")
    key_list = list(measure_data.keys())
    for key in key_list:
        # print(f"轉換前溫度：{key}:{measure_data[key]}")
        if "Temp" in key:
            measure_data[key] = measure_data[key] * 9.0 / 5.0 + 32.0

        if "Prsr" in key:
            measure_data[key] = measure_data[key] * 0.145038

        if "f1" in key or "f2" in key:
            measure_data[key] = measure_data[key] * 0.2642

        # print(f"轉換後溫度：{key}:{measure_data[key]}")
    # print(f"轉換後數據：{measure_data}")
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            for i, (key, value) in enumerate(measure_data.items()):
                word1, word2 = cvt_float_byte(value)
                registers = [word2, word1]
                client.write_registers(901 + i * 2, registers)
    except Exception as e:
        print(f"measure data input error:{e}")
        return "Setting Fail. PLC Communication Error"
    
    with open(f"{json_path}/thrshd_factory.json", "r") as json_file:
        thrshd_factory = json.load(json_file)
    key_list = list(thrshd_factory.keys())
    for key in key_list:
        if "Temp" in key and not key.startswith("Delay_") and "TempCds" not in key:
            thrshd_factory[key] = thrshd_factory[key] * 9.0 / 5.0 + 32.0

        if "TempCds" in key and not key.startswith("Delay_"):
            thrshd_factory[key] = thrshd_factory[key] * 9.0 / 5.0

        if "Prsr" in key and not key.startswith("Delay_"):
            thrshd_factory[key] = thrshd_factory[key] * 0.145038

        if "Flow" in key and not key.startswith("Delay_"):
            thrshd_factory[key] = thrshd_factory[key] * 0.2642


@default_ns.route("/1.3MW/cdu/status/op_mode")
class CduOpMode(Resource):
    @default_ns.doc("get_op_mode")
    def get(self):
        """Get the current operational mode stop, auto, or manual"""
        try:
            with open(f"{json_path}/ctr_data.json", "r") as json_file:
                data = json.load(json_file)
                op_mode["Mode"] = data["value"]["opMod"]
        except Exception as e:
            print(f"get mode error: {e}")
            return jsonify({"message": "PLC Communication Error"}), 500
        return op_mode["Mode"]

    @default_ns.expect(op_mode_model)
    @default_ns.doc("set_op_mode")
    def patch(self):
        """Set the operational mode auto, stop, or manual"""
        new_mode = api.payload["mode"]
        if new_mode not in ["auto", "stop", "manual"]:
            return {
                "message": "Invalid mode. Allowed values are 'auto', 'stop', 'manual'."
            }, 400

        op_mode["mode"] = new_mode

        try:
            with ModbusTcpClient(port=modbus_port, host=modbus_host) as client:
                if new_mode == "stop":
                    client.write_coils((8192 + 514), [False])
                elif new_mode == "manual":
                    client.write_coils((8192 + 505), [True])
                    client.write_coils((8192 + 514), [True])
                    client.write_coils((8192 + 516), [False])
                else:
                    client.write_coils((8192 + 505), [False])
                    client.write_coils((8192 + 514), [True])
                    client.write_coils((8192 + 516), [False])

        except Exception as e:
            print(f"set mode error:{e}")
            return {
                "message": "Invalid mode. Allowed values are 'auto', 'stop', 'manual'."
            }, 400

        return {
            "message": "op_mode updated successfully",
            "new_mode": op_mode["mode"],
        }, 200


@default_ns.route("/1.3MW/cdu/status/sensor_value")
class CduSensorValue(Resource):
    @default_ns.doc("get_sensor_value")
    def get(self):
        """Get the current sensor values of CDU"""
        try:
            with open(f"{json_path}/sensor_data.json", "r") as json_file:
                data1 = json.load(json_file)
                data["sensor_value"]["temp_coolant_supply"] = data1["value"][
                    "temp_clntSply"
                ]
                data["sensor_value"]["temp_coolant_supply_spare"] = data1["value"][
                    "temp_clntSplySpr"
                ]
                data["sensor_value"]["temp_coolant_return"] = data1["value"][
                    "temp_clntRtn"
                ]
                data["sensor_value"]["temp_ambient"] = data1["value"]["temp_ambient"]
                data["sensor_value"]["relative_humid"] = data1["value"]["rltHmd"]
                data["sensor_value"]["dew_point"] = data1["value"]["dewPt"]
                data["sensor_value"]["temp_water_supply"] = data1["value"][
                    "temp_waterIn"
                ]
                data["sensor_value"]["temp_water_return"] = data1["value"][
                    "temp_waterOut"
                ]
                data["sensor_value"]["pressure_coolant_supply"] = data1["value"][
                    "prsr_clntSply"
                ]
                data["sensor_value"]["pressure_coolant_supply_spare"] = data1["value"][
                    "prsr_clntSplySpr"
                ]
                data["sensor_value"]["pressure_coolant_return"] = data1["value"][
                    "prsr_clntRtn"
                ]
                data["sensor_value"]["pressure_filter_in"] = data1["value"][
                    "prsr_fltIn"
                ]
                data["sensor_value"]["pressure_filter1_out"] = data1["value"][
                    "prsr_flt1Out"
                ]
                data["sensor_value"]["pressure_filter2_out"] = data1["value"][
                    "prsr_flt2Out"
                ]
                data["sensor_value"]["pressure_filter3_out"] = data1["value"][
                    "prsr_flt3Out"
                ]
                data["sensor_value"]["pressure_filter4_out"] = data1["value"][
                    "prsr_flt4Out"
                ]
                data["sensor_value"]["pressure_filter5_out"] = data1["value"][
                    "prsr_flt5Out"
                ]
                data["sensor_value"]["pressure_water_in"] = data1["value"]["prsr_wtrIn"]
                data["sensor_value"]["pressure_water_out"] = data1["value"][
                    "prsr_wtrOut"
                ]
                data["sensor_value"]["flow_coolant"] = data1["value"]["flow_clnt"]
                data["sensor_value"]["flow_water"] = data1["value"]["flow_wtr"]
                data["sensor_value"]["pH"] = data1["value"]["pH"]
                data["sensor_value"]["conductivity"] = data1["value"]["cdct"]
                data["sensor_value"]["Turbidity"] = data1["value"]["tbd"]
                data["sensor_value"]["heat_capacity"] = data1["value"]["heat_capacity"]
                data["sensor_value"]["power_comsume"] = data1["value"]["power"]
                data["sensor_value"]["average_current"] = data1["value"]["AC"]

        except Exception as e:
            print(f"get mode error: {e}")
            return jsonify({"message": "PLC Communication Error"}), 500
        return data["sensor_value"]


@default_ns.route("/1.3MW/cdu/control/pump_speed")
class PumpSpeed(Resource):
    @default_ns.doc("get_pump_speed")
    def get(self):
        """Get the current sensor values of CDU"""

        try:
            with open(f"{json_path}/ctr_data.json", "r") as json_file:
                data = json.load(json_file)
                pump_speed_set["pump1_speed"] = data["value"]["pump1_speed"]
                pump_speed_set["pump2_speed"] = data["value"]["pump2_speed"]
        except Exception as e:
            print(f"get pump speed error:{e}")
            return jsonify({"message": "PLC Communication Error"}), 500
        return jsonify(pump_speed_set)

    @default_ns.expect(pump_speed_model)
    @default_ns.doc("update_pump_speed")
    def patch(self):
        """Update the pump speeds in percentage(0-100) in manual mode"""
        pump1_speed = api.payload["pump1_speed"]
        word1, word2 = cvt_float_byte(pump1_speed)
        pump2_speed = api.payload["pump2_speed"]
        word3, word4 = cvt_float_byte(pump2_speed)
        
        with open(f"{json_path}/sensor_data.json" ,"r") as json_file:
                sensorData = json.load(json_file)
        with open(f"{json_path}/ctr_data.json" ,"r") as json_file:
                ctr_data = json.load(json_file)
       
        if pump1_speed > 0 and pump2_speed > 0 and pump1_speed != pump2_speed:
                return {"message": "Please synchronize speeds to run both pumps or change speed."}, 400
        else:
                # 寫入 pump speed
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(246, [word2, word1])
                    client.write_registers(222, [word4, word3])
                    client.close()
            except Exception as e:
                print(f"pump speed setting error:{e}")
                return {"message": "Setting Fail. PLC Communication Error"}, 400

            # p1 p2 歸零，關 EV1-4
            if (pump1_speed == 0 and pump2_speed == 0) or (
                ctr_data["value"]["resultP1"] == 0 and ctr_data["value"]["resultP2"] == 0
            ):
                try:
                    with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                        client.write_coils((8192 + 13), [False] * 4)
                        client.close()
                except Exception as e:
                    print(f"setting ev error:{e}")

            if ctr_data["value"]["resultMode"] in ["Engineer", "Manual"]:
                if (
                    sensorData["error"]["Inv1_Error"]
                    and sensorData["error"]["Inv2_Error"]
                    and pump2_speed > 0
                    and pump1_speed > 0
                    and pump1_speed == pump2_speed
                ):
                    return "Inverters 1 and 2 are both in Fault State \nUnable to Activate EV1 to EV4"
                elif sensorData["error"]["Inv1_Error"] and pump1_speed > 0:
                    return "Failed to activate EV1 and EV2 due to Inverter 1 error"
                elif sensorData["error"]["Inv2_Error"] and pump2_speed > 0:
                    return "Failed to activate EV3 and EV4 due to Inverter 2 error"

                if pump1_speed == pump2_speed:
                    if sensorData["error"]["Inv1_OverLoad"]:
                        return "Pump Speed 2 Updated Successfully"
                    if sensorData["error"]["Inv2_OverLoad"]:
                        return "Pump Speed 1 Updated Successfully"
                    if (
                        not sensorData["error"]["Inv1_OverLoad"]
                        and not sensorData["error"]["Inv2_OverLoad"]
                    ):
                        return "Pump Speed Updated Successfully"
                elif pump1_speed > 0 and pump2_speed > 0 and pump1_speed != pump2_speed:
                    if sensorData["error"]["Inv1_OverLoad"]:
                        return "Pump Speed 2 Updated Successfully. \nPump1 can't start due to inverter1 overlaod"
                    if sensorData["error"]["Inv2_OverLoad"]:
                        return "Pump Speed 1 Updated Successfully. \nPump2 can't start due to inverter2 overlaod"
                    if (
                        not sensorData["error"]["Inv1_OverLoad"]
                        and not sensorData["error"]["Inv2_OverLoad"]
                    ):
                        return "Please synchronize speeds to run both pumps. \nPump 2 is switched off."
                elif (
                    sensorData["error"]["Inv1_OverLoad"]
                    and pump1_speed > 0
                    and pump2_speed == 0
                    and pump1_speed != pump2_speed
                ):
                    return "Inverter1 Overload: Unable to update pump1 speed"
                elif (
                    sensorData["error"]["Inv2_OverLoad"]
                    and pump1_speed == 0
                    and pump2_speed > 0
                    and pump1_speed != pump2_speed
                ):
                    return "Inverter2 Overload: Unable to update pump2 speed"

            pump_speed_set["pump1_speed"] = pump1_speed
            pump_speed_set["pump2_speed"] = pump2_speed

            return {
                "message": "Pump speed updated successfully",
                "pump_speed": pump_speed_set,
            }, 200


@default_ns.route("/1.3MW/cdu/control/water_pv")
class WaterPV(Resource):
    @default_ns.doc("get_water_pv")
    def get(self):
        """Get the opening of water proportional valve in percentage"""
        try:
            with open(f"{json_path}/ctr_data.json", "r") as json_file:
                data = json.load(json_file)
                water_pv_set["water_PV"] = data["value"]["water_PV"]

        except Exception as e:
            print(f"water pv error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return water_pv_set

    @default_ns.expect(water_pv_model)
    @default_ns.doc("update_water_pv")
    def patch(self):
        """Update the opening of water proportional valve in percentage(0-100) in manual mode"""
        new_position = api.payload["water_PV"]
        if 0 <= new_position <= 100:
            word1, word2 = cvt_float_byte(float(new_position))
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(352, [word2, word1])  # D352
                    client.close()
                    # r = client.read_holding_registers(352, 2, unit=modbus_slave_id)
                    # print(f"水數據：{[r.registers[0],r.registers[1]]}")
            except Exception as e:
                print(f"water issue:{e}")
                return "PLC Communication Error"

            water_pv_set["water_PV"] = new_position

        else:
            return {"message": "Invalid position. Must be between 0 and 100."}, 400

        return {
            "message": "Water proportional valve position updated successfully",
            "new_position": water_pv_set["water_PV"],
        }, 200


@default_ns.route("/1.3MW/cdu/control/temp_set")
class TempSet(Resource):
    @api.doc("get_temp_set")
    def get(self):
        """Get the current temperature setting"""
        try:
            with open(f"{json_path}/ctr_data.json", "r") as json_file:
                data = json.load(json_file)

                temp_set["temp_set"] = data["value"]["oil_temp_set"]
        except Exception as e:
            print(f"temp error: {e}")
            return {"message": "PLC Communication Error"}, 500

        return temp_set["temp_set"]

    @default_ns.expect(temp_set_model)
    @default_ns.doc("patch_temp_set")
    def patch(self):
        """Update the temperature setting in 35-55 deg celcius"""
        new_temp = api.payload["temp_set"]
        try:
            with open(f"{json_path}/system_data.json" ,"r") as json_file:
                data = json.load(json_file)
            if data["value"]["unit"] == "imperial":  # imperial
                upLmt = 131
                lowLmt = 95
            else:
                upLmt = 55
                lowLmt = 35
        except Exception as e:
            print(f"temp_set_limit: {e}")
            return "Reading Fail. PLC Communication Error"

        if lowLmt <= new_temp <= upLmt:
            word1, word2 = cvt_float_byte(float(new_temp))
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(226, [word2, word1])  # D226
            except Exception as e:
                print(f"temp_set: {e}")
                return "Setting Fail. PLC Communication Error"
            temp_set["temp_set"] = new_temp
        else:
            with open(f"{json_path}/system_data.json" ,"r") as json_file:
                data = json.load(json_file)
            if data["value"]["unit"] == "imperial": 
            
                return {
                    "message": "Invalid temperature. Temperature must be between 95°F and 131°F."
                }, 400
            else:
                return {
                    "message": "Invalid temperature. Temperature must be between 35°C and 55°C."
                }, 400

        return {
            "message": "temp_set updated successfully",
            "new_temp_set": temp_set["temp_set"],
        }, 200


@default_ns.route("/1.3MW/cdu/control/pressure_set")
class PressureSet(Resource):
    @default_ns.doc("get_pressure_set")
    def get(self):
        """Get CDU taget coolan outlet pressure setting value"""
        try:
            with open(f"{json_path}/ctr_data.json", "r") as json_file:
                data = json.load(json_file)
                pressure_set["pressure_set"] = round(data["value"]["oil_pressure_set"], 2 )
        except Exception as e:
            print(f"get mode error: {e}")
            return jsonify({"message": "PLC Communication Error"}), 500
        return pressure_set["pressure_set"]

    @default_ns.expect(pressure_set_model)
    @default_ns.doc("patch_pressure_set")
    def patch(self):
        """Update the pressure setting in 0-750 kPa or 0-108 psi """
        new_pressure = api.payload["pressure_set"]
        try:
            with open(f"{json_path}/system_data.json" ,"r") as json_file:
                data = json.load(json_file)
            
            if data["value"]["unit"] == "imperial":  # imperial
                upLmt = 108
                lowLmt = 0
            else:
                upLmt = 750
                lowLmt = 0
        except Exception as e:
            print(f"pressure_set_limit: {e}")
            return "Pressure Unit Reading Fail. PLC Communication Error"

        # print(f"下限：{lowLmt}")
        # print(f"上限：{upLmt}")
        if lowLmt <= new_pressure <= upLmt:
            try:
                word1, word2 = cvt_float_byte(float(new_pressure))
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(224, [word2, word1])  # D224
            except Exception as e:
                print(f"pressure_set: {e}")
                return "PressureSetting Fail. PLC Communication Error"

            pressure_set["pressure_set"] = new_pressure
        else:
            with open(f"{json_path}/system_data.json" ,"r") as json_file:
                data = json.load(json_file)
            if data["value"]["unit"] == "imperial":
                return {
                    "message": "Invalid pressure. Pressure must be between 0 and 108."
                }, 400
            else:
                return {
                    "message": "Invalid pressure. Pressure must be between 0 and 750."
                }, 400
        return {
            "message": "pressure_set updated successfully",
            "new_pressure_set": pressure_set["pressure_set"],
        }, 200


@default_ns.route("/1.3MW/cdu/control/pump_swap_time")
class PumpSwapTime(Resource):
    @default_ns.doc("get_pump_swap_time")
    def get(self):
        """Get CDU pump swap time setting"""

        try:
            with open(f"{json_path}/ctr_data.json", "r") as json_file:
                data = json.load(json_file)
                pump_swap_time["pump_swap_time"] = data["value"]["pump_swap_time"]
        except Exception as e:
            print(f"pump swap time error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return jsonify(pump_swap_time)

        # return pump_swap_time

    @default_ns.expect(pump_swap_time_model)
    @default_ns.doc("update_pump_swap_time")
    def patch(self):
        """Update the time interval for pump swapping in minutes"""
        new_time = api.payload["pump_swap_time"]
        if 0 <= new_time <= 30000:
            try:
                word1, word2 = cvt_float_byte(float(new_time))
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_registers(242, [word2, word1])  # D242
            except Exception as e:
                print(f"update_pump_swap_time: {e}")
                return "Setting Fail. PLC Communication Error"

            pump_swap_time["pump_swap_time"] = new_time
        else:
            return {
                "message": "Invalid value. Time interval must be between 0 and 30000 Hours."
            }, 400

        return {
            "message": "Pump swap time updated successfully",
            "new_pump_swap_time": pump_swap_time["pump_swap_time"],
        }, 200


@default_ns.route("/1.3MW/cdu/status/pump_speed")
class TankIOStatus(Resource):
    @default_ns.doc("get_pump_status")
    def get(self):
        """Get speed of pumps"""
        try:
             with open(f"{json_path}/sensor_data.json" ,"r") as json_file:
                data1 = json.load(json_file)
                data["pump_speed"]["pump2_speed"] = round(data1["value"]["inv2_freq"])
                data["pump_speed"]["pump1_speed"] = round(data1["value"]["inv1_freq"])
        except Exception as e:
            print(f"pump speed error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return {
            "pump1 speed": data["pump_speed"]["pump1_speed"],
            "pump2 speed": data["pump_speed"]["pump2_speed"],
        }, 200


@default_ns.route("/1.3MW/cdu/status/pump_service_hours")
class pump_Service_hours(Resource):
    @default_ns.doc("get_pump_service_hours")
    def get(self):
        """Get service hours of pumps"""
        try:
             with open(f"{json_path}/ctr_data.json" ,"r") as json_file:
                data1 = json.load(json_file)

                data["pump_service_hours"]["pump1_service_hours"] =data1["text"]["Pump1_run_time"]

                data["pump_service_hours"]["pump2_service_hours"] =data1["text"]["Pump2_run_time"]

           
        except Exception as e:
            print(f"pump speed time error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return data["pump_service_hours"]


@default_ns.route("/1.3MW/cdu/status/pump_state")
class pump_state(Resource):
    @default_ns.doc("get_pump_state")
    def get(self):
        """Get state of pumps"""
        try:
            with open(f"{json_path}/sensor_data.json" ,"r") as json_file:
                data1 = json.load(json_file)
                if round(data1["value"]["inv1_freq"]) > 0:
                    data["pump_state"]["pump1_state"] = "Enable"
                else:
                    data["pump_state"]["pump1_state"] = "Disable"

                if round(data1["value"]["inv2_freq"]) > 0:
                    data["pump_state"]["pump2_state"] = "Enable"
                else:
                    data["pump_state"]["pump2_state"] = "Disable"
        except Exception as e:
            print(f"pump speed error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return data["pump_state"]


@default_ns.route("/1.3MW/cdu/status/pump_health")
class pump_health(Resource):
    @default_ns.doc("get_pump_health")
    def get(self):
        """Get health of pumps"""
        try:
            with open(f"{json_path}/sensor_data.json" ,"r") as json_file:
                data1 = json.load(json_file)

                if data1["error"]["Inv1_Error"]:
                    data["pump_health"]["pump1_health"] = "Error"
                else:
                    data["pump_health"]["pump1_health"] = "OK"

                if data1["error"]["Inv2_Error"]:
                    data["pump_health"]["pump2_health"] = "Error"
                else:
                    data["pump_health"]["pump2_health"] = "OK"

        except Exception as e:
            print(f"pump health error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return data["pump_health"]

@default_ns.route('/1.3MW/cdu/status/filter_service_hours')
class filter_service_hours(Resource):
    @default_ns.doc('get_filter_service_hours')
    def get(self):
        """Get service hours of filters"""
        with open(f"{json_path}/ctr_data.json" ,"r") as json_file:
            data1 = json.load(json_file)
            data['filter_service_hours']['filter1_service_hours']= data1["filter"]["f1"]
            data['filter_service_hours']['filter2_service_hours']= data1["filter"]["f2"]
            data['filter_service_hours']['filter3_service_hours']= data1["filter"]["f3"]
            data['filter_service_hours']['filter4_service_hours']= data1["filter"]["f4"]
            data['filter_service_hours']['filter5_service_hours']= data1["filter"]["f5"]
            
        return data['filter_service_hours']
    


@default_ns.route("/1.3MW/cdu/status/water_pv")
class water_pv(Resource):
    @default_ns.doc("get_water_pv_status")
    def get(self):
        """Get opening of water proportional valve"""
        try:
            with open(f"{json_path}/sensor_data.json" ,"r") as json_file:
                data1 = json.load(json_file)
                data["water_pv"]["water_PV"] = round(data1["value"]["WaterPV"])
        except Exception as e:
            print(f"status water error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return data["water_pv"]


def change_data_by_unit():
    try:
        with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
            last_unit = client.read_coils((8192 + 501), 1, unit=modbus_slave_id)
            current_unit = client.read_coils((8192 + 500), 1, unit=modbus_slave_id)
            client.close()

            last_unit = last_unit.bits[0]
            current_unit = current_unit.bits[0]

            # 寫入 dictionary
            if current_unit:
                system_data["value"]["unit"] = "imperial"
            else:
                system_data["value"]["unit"] = "metric"

            # 寫入 dictionary
            if last_unit:
                system_data["value"]["last_unit"] = "imperial"
            else:
                system_data["value"]["last_unit"] = "metric"

            # print(f"{last_unit} -> {current_unit}")

            # 比對
            if current_unit and current_unit != last_unit:
                change_to_imperial()
            elif not current_unit and current_unit != last_unit:
                change_to_metric()
            # else:
            #     print("Invalid unit change")

            # 寫入 last unit
            client.write_coils((8192 + 501), [current_unit])

            client.close()

    except Exception as e:
        print(f"unit set error:{e}")
@default_ns.route("/1.3MW/unit_set")
class Unit(Resource):
    @default_ns.doc("get_unit_set")
    def get(self):
        """Get the current unit setting"""
        try:
            with open(f"{json_path}/system_data.json" ,"r") as json_file:
                data = json.load(json_file)
                unit_set["unit"] = data["value"]["unit"]

        except Exception as e:
            print(f"unit set error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return unit_set

    @default_ns.expect(unit_set_model)
    @default_ns.doc("update_unit_set")
    def patch(self):
        """Update the unit setting to metric or imperial"""
        new_unit = api.payload["unit_set"]
        if new_unit.lower() in ["metric", "imperial"]:
            unit_set["unit"] = new_unit
            if unit_set["unit"] == "imperial":
                coil_value = True
            elif unit_set["unit"] == "metric":
                coil_value = False
                        
            try:
                with ModbusTcpClient(host=modbus_host, port=modbus_port) as client:
                    client.write_coil(address=(8192 + 500), value=coil_value)
                    client.close()
                            
            except Exception as e:
                print(f"unit set error:{e}")
                return {"message": "PLC Communication Error"}, 500
            change_data_by_unit()
            return {
                "message": "Unit updated successfully",
                "new_unit": unit_set["unit"],
            }, 200
        else:
            return {
                "message": "Invalid unit. Unit must be 'metric' or 'imperial'."
            }, 400


@default_ns.route("/1.3MW/cdu/status/valve")
class ValveStatus(Resource):
    @default_ns.doc("get_valve_status")
    def get(self):
        """Get the status of electric valves"""
        try:
            with open(f"{json_path}/ctr_data.json" ,"r") as json_file:
                data1 = json.load(json_file)
                ev_names = ["1", "2", "3", "4"]
                for ev in ev_names:
                    data["valve"][f"EV{ev}"] = data1["valve"][f"resultEV{ev}"]

        except Exception as e:
            print(f"valve error:{e}")
            return {"message": "PLC Communication Error"}, 500

        return data["valve"]


@default_ns.route("/1.3MW/error_messages")
class ErrorMessages(Resource):
    @default_ns.doc("get_error_messages")
    @default_ns.marshal_with(message_model)
    def get(self):
        """Get the list of error messages happening in the system"""

        try:
            with open(f"{json_path}/sensor_data.json" ,"r") as json_file:
                data = json.load(json_file)


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
                "M117": "prsr_wtrQltMtrOut_high",
                "M118": "prsr_wtrIn_high",
                "M119": "prsr_wtrOut_high",
                "M120": "relative_humid_low",
                "M121": "relative_humid_high",
                "M122": "temp_ambient_low",
                "M123": "temp_ambient_high",
                "M124": "dew_point_temp_low",
                "M125": "clnt_flow_low",
                "M126": "wtr_flow_low",
                "M127": "ph_low",
                "M128": "ph_high",
                "M129": "cndct_low",
                "M130": "cndct_high",
                "M131": "tbd_low",
                "M132": "tbd_high",
                "M133": "AC_high",
            }

            # 根據對應映射來更新 messages 中的布林值
            for msg_key, sensor_key in key_mapping.items():
                messages["warning"][msg_key][1] = data["warning"][sensor_key]

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
                "M217": "prsr_wtrQltMtrOut_high",
                "M218": "prsr_wtrIn_high",
                "M219": "prsr_wtrOut_high",
                "M220": "relative_humid_low",
                "M221": "relative_humid_high",
                "M222": "temp_ambient_low",
                "M223": "temp_ambient_high",
                "M224": "dew_point_temp_low",
                "M225": "clnt_flow_low",
                "M226": "wtr_flow_low",
                "M227": "ph_low",
                "M228": "ph_high",
                "M229": "cndct_low",
                "M230": "cndct_high",
                "M231": "tbd_low",
                "M232": "tbd_high",
                "M233": "AC_high",
            }

            # 根據對應映射來更新 messages 中的布林值
            for msg_key, sensor_key in key_mapping.items():
                messages["alert"][msg_key][1] = data["alert"][sensor_key]

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
                "M312": "ATS2",
                "M313": "PLC",
                "M314": "Inv1_Com",
                "M315": "Inv2_Com",
                "M316": "Ambient_Sensor_Com",
                "M317": "Clnt_Flow_Com",
                "M318": "Wtr_Flow_Com",
                "M319": "Cndct_Sensor_Com",
                "M320": "ph_Com",
                "M321": "Tbd_Com",
                "M322": "ATS_Com",
                "M323": "Power_Meter_Com",
                "M324": "TempClntSply_broken",
                "M325": "TempClntSplySpr_broken",
                "M326": "TempClntRtn_broken",
                "M327": "TempWaterIn_broken",
                "M328": "TempWaterOut_broken",
                "M329": "PrsrClntSply_broken",
                "M330": "PrsrClntSplySpr_broken",
                "M331": "PrsrClntRtn_broken",
                "M332": "PrsrFltIn_broken",
                "M333": "PrsrFlt1Out_broken",
                "M334": "PrsrFlt2Out_broken",
                "M335": "PrsrFlt3Out_broken",
                "M336": "PrsrFlt4Out_broken",
                "M337": "PrsrFlt5Out_broken",
                "M338": "PrsrQltOut_broken",
                "M339": "PrsrWaterIn_broken",
                "M340": "PrsrWaterOut_broken",
            }

        # 根據對應映射來更新 messages 中的布林值
            for msg_key, sensor_key in key_mapping.items():
                messages["error"][msg_key][1] = data["error"][sensor_key]
        except Exception as e:
            print(f"error message issue:{e}")
            return {"message": "PLC Communication Error"}, 500

        error_messages = []
        for category in ["warning", "alert", "error"]:
            for code, message in messages[category].items():
                if message[1]:
                    error_messages.append({"error_code": code, "message": message[0]})
        return error_messages

    
@default_ns.route('/1.3MW/unit')
class Unit(Resource):
    # @default_ns.doc('get_unit')
    @default_ns.marshal_with(unit_model)
    def get(self):
        """Get the unit information"""
        with open(f"{json_path}/sensor_data.json" ,"r") as json_file:
            data1 = json.load(json_file)
            if data1["unit"]["unit_temp"] == "\u00b0C":
                data["unit"]["temperature"] = "celcius"
            else :
                data["unit"]["temperature"] = "fahrenheit"
                
            data["unit"]["pressure"] = data1["unit"]["unit_pressure"]
            data["unit"]["flow"] = data1["unit"]["unit_flow"]
            
            
        return data["unit"]
# Add namespace to API
api.add_namespace(default_ns)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

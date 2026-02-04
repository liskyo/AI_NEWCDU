import bisect
import json
import logging
from logging.handlers import RotatingFileHandler
import struct
import threading
import time
import os
import sys
from flask import Flask

from pyasn1.codec.ber import decoder, encoder
from pymodbus.client.sync import ModbusTcpClient
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.entity import config, engine
from pysnmp.hlapi import *
from pysnmp.proto import api

app = Flask(__name__)


FORMAT = "%(asctime)s %(levelname)s: %(message)s"

logging.basicConfig(level=logging.INFO, format=FORMAT)
logging.basicConfig(level=logging.ERROR, format=FORMAT)


log_path = os.getcwd()

journal_dir = f"{log_path}/logs/journal"
if not os.path.exists(journal_dir):
    os.makedirs(journal_dir)

max_bytes = 200 * 1024 * 1024


file_name = "journal.log"
log_file = os.path.join(journal_dir, file_name)
journal_handler = RotatingFileHandler(
    log_file,
    maxBytes=max_bytes,
    backupCount=1,
    encoding="UTF-8",
    delay=False,
)


journal_logger = logging.getLogger("journal_logger")
journal_logger.setLevel(logging.INFO)
journal_logger.addHandler(journal_handler)


SNMPV3_USER = "user"
SNMPV3_AUTH_KEY = "Itgs50848614"
SNMPV3_PRIV_KEY = "Itgs50848614"
AUTH_PROTOCOL = usmHMACSHAAuthProtocol
PRIV_PROTOCOL = usmAesCfb128Protocol


ALARM_THRESHOLD = 810
MODBUS_SERVER_IP = "192.168.3.250"
MODBUS_SERVER_PORT = 502
SNMP_TRAP_RECEIVER_IP = ""
SNMP_AGENT_IP = "0.0.0.0"
SNMP_GET_PORT = 9000
SNMP_TRAP_PORT = 9001


float_values = [None] * 31
trap_bool_lists = [None] * 30
alarm_value = [ALARM_THRESHOLD] * 30
ats_list = [None] * 2

cnt = 0

check_key_list = [
    [
        "CoolantSupplyTemperature",
        "CoolantSupplyTemperatureSpare",
        "CoolantReturnTemperature",
        "WaterSupplyTemperature",
        "WaterSupplyTemperature",
        "WaterReturnTemperature",
        "WaterReturnTemperature",
        "CoolantSupplyPressure",
        "CoolantSupplyPressureSpare",
        "CoolantReturnPressure",
        "FilterInletPressure",
        "FilterInletPressure",
        "Filter1OutletPressure",
        "Filter2OutletPressure",
        "Filter3OutletPressure",
        "Filter4OutletPressure",
    ],
    [
        "Filter5OutletPressure",
        "WaterInletPressure",
        "WaterOutletPressure",
        "RelativeHumidity",
        "RelativeHumidity",
        "AmbientTemperature",
        "AmbientTemperature",
        "DewPoint",
        "CoolantFlowRate",
        "WaterFlowRate",
        "pH",
        "pH",
        "Conductivity",
        "Conductivity",
        "Turbidity",
        "Turbidity",
    ],
    [
        "AverageCurrent",
        "CoolantReturnPressureSpare",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "CoolantSupplyTemperature",
        "CoolantSupplyTemperatureSpare",
        "CoolantReturnTemperature",
        "WaterSupplyTemperature",
        "WaterSupplyTemperature",
        "WaterReturnTemperature",
        "WaterReturnTemperature",
        "CoolantSupplyPressure",
        "CoolantSupplyPressureSpare",
        "CoolantReturnPressure",
        "FilterInletPressure",
        "FilterInletPressure",
        "Filter1OutletPressure",
        "Filter2OutletPressure",
        "Filter3OutletPressure",
        "Filter4OutletPressure",
    ],
    [
        "Filter5OutletPressure",
        "WaterInletPressure",
        "WaterOutletPressure",
        "RelativeHumidity",
        "RelativeHumidity",
        "AmbientTemperature",
        "AmbientTemperature",
        "DewPoint",
        "CoolantFlowRate",
        "WaterFlowRate",
        "pH",
        "pH",
        "Conductivity",
        "Conductivity",
        "Turbidity",
        "Turbidity",
    ],
    [
        "AverageCurrent",
        "CoolantReturnPressureSpare",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "PV1Status",
        "EV1Status",
        "EV2Status",
        "EV3Status",
        "EV4Status",
        "VFD1Overload",
        "VFD2Overload",
        "VFD1Status",
        "VFD2Status",
        "LeakDetectionLeak",
        "LeakDetectionBroken",
        "PowerSource",
        "Inv1SpeedComm",
        "Inv2SpeedComm",
        "AmbientTemperatureComm",
        "CoolantFlowRateComm",
    ],
    [
        "FacilityWaterFlowRateComm",
        "ConductivityComm",
        "pHComm",
        "TurbidityComm",
        "ATS1Comm",
        "InstantPowerConsumptionComm",
        "CoolantSupplyTemperatureBroken",
        "CoolantSupplyTemperatureSpareBroken",
        "CoolantReturnTemperatureBroken",
        "WaterSupplyTemperatureBroken",
        "WaterReturnTemperatureBroken",
        "CoolantSupplyPressureBroken",
        "CoolantSupplyPressureSpareBroken",
        "CoolantReturnPressureBroken",
        "FilterInletPressureBroken",
        "Filter1Status",
    ],
    [
        "Filter2Status",
        "Filter3Status",
        "Filter4Status",
        "Filter5Status",
        "WaterInletPressureBroken",
        "WaterOutletPressureBroken",
        "CoolantFlowRateBroken",
        "WaterFlowRateBroken",
        "LowCoolantLevelWarning",
        "Inv1ErrorCode",
        "Inv2ErrorCode",
        "PC1Error",
        "PC2Error",
        "CoolantReturnPressureSpareBroken",
        "Level1Error",
        "Level2Error",
    ],
    [
        "Power1Error",
        "Power2Error",
        "Level3Error",
        "ControlUnit",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
    ],
]

data_details = {}
v2 = False

index = 0
warning_alert_list = [
    [
        "M100 Coolant Supply Temperature Over Range (High) Warning (T1)",
        "M101 Coolant Supply Temperature Spare Over Range (High) Warning (T1 sp)",
        "M102 Coolant Return Temperature Over Range (High) Warning (T2)",
        "M103 Facility Water Supply Temperature Over Range (Low) Warning (T4)",
        "M104 Facility Water Supply Temperature Over Range (High) Warning (T4)",
        "M105 Facility Water Return Temperature Over Range (Low) Warning (T5)",
        "M106 Facility Water Return Temperature Over Range (High) Warning (T5)",
        "M107 Coolant Supply Pressure Over Range (High) Warning (P1)",
        "M108 Coolant Supply Pressure Spare Over Range (High) Warning (P1 sp)",
        "M109 Coolant Return Pressure Over Range (High) Warning (P2)",
        "M110 Filter Inlet Pressure Over Range (Low) Warning (P3)",
        "M111 Filter Inlet Pressure Over Range (High) Warning (P3)",
        "M112 Filter1 Outlet Pressure Over Range (High) Warning (P4)",
        "M113 Filter2 Outlet Pressure Over Range (High) Warning (P5)",
        "M114 Filter3 Outlet Pressure Over Range (High) Warning (P6)",
        "M115 Filter4 Outlet Pressure Over Range (High) Warning (P7)",
    ],
    [
        "M116 Filter5 Outlet Pressure Over Range (High) Warning (P8)",
        "M117 Facility Water Inlet Pressure Over Range (High) Warning (P10)",
        "M118 Facility Water Outlet Pressure Over Range (High) Warning (P11)",
        "M119 Relative Humidity Over Range (Low) Warning (RH)",
        "M120 Relative Humidity Over Range (High) Warning (RH)",
        "M121 Ambient Temperature Over Range (Low) Warning (T a)",
        "M122 Ambient Temperature Over Range (High) Warning (T a)",
        "M123 Condensation Warning (T Dp)",
        "M124 Coolant Flow Rate (Low) Warning (F1)",
        "M125 Facility Water Flow Rate (Low) Warning (F2)",
        "M126 pH Over Range (Low) Warning (pH)",
        "M127 pH Over Range (High) Warning (pH)",
        "M128 Conductivity Over Range (Low) Warning (CON)",
        "M129 Conductivity Over Range (High) Warning (CON)",
        "M130 Turbidity Over Range (Low) Warning (Tur)",
        "M131 Turbidity Over Range (High) Warning (Tur)",
    ],
    [
        "M132 Average Current Over Range (High) Warning",
        "M133 Coolant Return Pressure Spare Over Range (High) Warning (P2 sp)",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
    ],
    [
        "M200 Coolant Supply Temperature Over Range (High) Alert (T1)",
        "M201 Coolant Supply Temperature Spare Over Range (High) Alert (T1 sp)",
        "M202 Coolant Return Temperature Over Range (High) Alert (T2)",
        "M203 Facility Water Supply Temperature Over Range (Low) Alert (T4)",
        "M204 Facility Water Supply Temperature Over Range (High) Alert (T4)",
        "M205 Facility Water Return Temperature Over Range (Low) Alert (T5)",
        "M206 Facility Water Return Temperature Over Range (High) Alert (T5)",
        "M207 Coolant Supply Pressure Over Range (High) Alert (P1)",
        "M208 Coolant Supply Pressure Spare Over Range (High) Alert (P1 sp)",
        "M209 Coolant Return Pressure Over Range (High) Alert (P2)",
        "M210 Filter Inlet Pressure Over Range (Low) Alert (P3)",
        "M211 Filter Inlet Pressure Over Range (High) Alert (P3)",
        "M212 Filter1 Outlet Pressure Over Range (High) Alert (P4)",
        "M213 Filter2 Outlet Pressure Over Range (High) Alert (P5)",
        "M214 Filter3 Outlet Pressure Over Range (High) Alert (P6)",
        "M215 Filter4 Outlet Pressure Over Range (High) Alert (P7)",
    ],
    [
        "M216 Filter5 Outlet Pressure Over Range (High) Alert (P8)",
        "M217 Facility Water Inlet Pressure Over Range (High) Alert (P10)",
        "M218 Facility Water Outlet Pressure Over Range (High) Alert (P11)",
        "M219 Relative Humidity Over Range (Low) Alert (RH)",
        "M220 Relative Humidity Over Range (High) Alert (RH)",
        "M221 Ambient Temperature Over Range (Low) Alert (T a)",
        "M222 Ambient Temperature Over Range (High) Alert (T a)",
        "M223 Condensation Alert (T Dp)",
        "M224 Coolant Flow Rate (Low) Alert (F1)",
        "M225 Facility Water Flow Rate (Low) Alert (F2)",
        "M226 pH Over Range (Low) Alert (pH)",
        "M227 pH Over Range (High) Alert (pH)",
        "M228 Conductivity Over Range (Low) Alert (CON)",
        "M229 Conductivity Over Range (High) Alert (CON)",
        "M230 Turbidity Over Range (Low) Alert (Tur)",
        "M231 Turbidity Over Range (High) Alert (Tur)",
    ],
    [
        "M232 Average Current Over Range (High) Alert",
        "M233 Coolant Return Pressure Spare Over Range (High) Alert (P2 sp)",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
    ],
    [
        "M300 Facility Water Proportional Valve Disconnection",
        "M307 Coolant Pump1 Outlet Electrical Valve (EV1) Error",
        "M308 Coolant Pump1 Inlet Electrical Valve (EV2) Error",
        "M309 Coolant Pump2 Outlet Electrical Valve (EV3) Error",
        "M310 Coolant Pump2 Inlet Electrical Valve (EV4) Error",
        "M301 Coolant Pump1 Inverter Overload",
        "M302 Coolant Pump2 Inverter Overload",
        "M303 Coolant Pump1 Inverter Error",
        "M304 Coolant Pump2 Inverter Error",
        "M305 Facility Water Leakage",
        "M306 Facility Water Leakage Sensor Broken",
        "M311 Factory Power Status",
        "M312 Inverter1 Communication Error",
        "M313 Inverter2 Communication Error",
        "M314 Ambient Sensor Communication Error",
        "M315 Coolant Flow Meter Communication Error",
    ],
    [
        "M316 Water Flow Meter Communication Error",
        "M317 Conductivity Sensor Communication Error",
        "M318 pH Sensor Communication Error",
        "M319 Turbidity Sensor Communication Error",
        "M320 ATS Communication Error",
        "M321 Power Meter Communication Error",
        "M322 Coolant Supply Temperature Broken Error",
        "M323 Coolant Supply Temperature (Spare) Broken Error",
        "M324 Coolant Return Temperature Broken Error",
        "M325 Facility Water Supply Temperature Broken Error",
        "M326 Facility Water Return Temperature Broken Error",
        "M327 Coolant Supply Pressure Broken Error",
        "M328 Coolant Supply Pressure (Spare) Broken Error",
        "M329 Coolant Return Pressure Broken Error",
        "M330 Filter Inlet Pressure Broken Error",
        "M331 Filter1 Outlet Pressure Broken Error",
    ],
    [
        "M332 Filter2 Outlet Pressure Broken Error",
        "M333 Filter3 Outlet Pressure Broken Error",
        "M334 Filter4 Outlet Pressure Broken Error",
        "M335 Filter5 Outlet Pressure Broken Error",
        "M336 Facility Water Inlet Pressure Broken Error",
        "M337 Facility Water Outlet Pressure Broken Error",
        "M338 Coolant Flow Rate (F1) Broken Error",
        "M339 Facility Water Flow Rate (F2) Broken Error",
        "M340 Stop Due to Low Coolant Level",
        "M341 Inverter 1 Error",
        "M342 Inverter 2 Error",
        "M343 PC1 Error",
        "M344 PC2 Error",
        "M345 Coolant Return Pressure (Spare) (P2 sp) Broken Error",
        "M346 Liquid Coolant Level 1 Error",
        "M347 Liquid Coolant Level 2 Error",
    ],
    [
        "M348 Power Supply 1 Error",
        "M349 Power Supply 2 Error",
        "M350 Liquid Coolant Level 3 Error",
        "M351 PLC Communication Broken Error",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
    ],
]

scc_data = {}
scc_device = {}
snmp_data = {}

data_lock = threading.Lock()


class SysDescr:
    name = (1, 3, 6, 1, 2, 1, 1, 1, 0)

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other

    def __lt__(self, other):
        return self.name < other

    def __le__(self, other):
        return self.name <= other

    def __gt__(self, other):
        return self.name > other

    def __ge__(self, other):
        return self.name >= other

    def __call__(self, protoVer):
        return api.protoModules[protoVer].OctetString("version:{}".format(protoVer))


class Uptime:
    name = (1, 3, 6, 1, 2, 1, 1, 3, 0)
    birthday = time.time()

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other

    def __lt__(self, other):
        return self.name < other

    def __le__(self, other):
        return self.name <= other

    def __gt__(self, other):
        return self.name > other

    def __ge__(self, other):
        return self.name >= other

    def __call__(self, protoVer):
        return api.protoModules[protoVer].TimeTicks((time.time() - self.birthday) * 100)


class Bufferin:
    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other

    def __lt__(self, other):
        return self.name < other

    def __le__(self, other):
        return self.name <= other

    def __gt__(self, other):
        return self.name > other

    def __ge__(self, other):
        return self.name >= other

    def __call__(self, protoVer):
        if self.value is None:
            self.value = ""
        return api.protoModules[protoVer].OctetString(self.value)


def convert_registers_to_str(register_data):
    """
    將寄存器數據轉換為浮點數。

    :param register_data: 寄存器數據列表
    :return: 浮點數數據列表
    """
    float_data = []
    for i in range(0, len(register_data), 2):
        high_word = register_data[i + 1]
        low_word = register_data[i]
        packed_value = struct.pack("<HH", low_word, high_word)
        float_value = struct.unpack("<f", packed_value)[0]
        float_value = round(float_value, 2)
        float_data.append(str(float_value))
    return float_data


def convert_float_to_registers(float_data):
    register_data = []
    for value in float_data:
        packed_value = struct.pack("<f", value)
        low_word, high_word = struct.unpack("<HH", packed_value)
        register_data.append(low_word)
        register_data.append(high_word)
    return register_data


def word_to_bool_list(words):
    bit_lengths = [16] * 11
    all_bool_lists = []
    word_index = 0
    for bits in bit_lengths:
        binary_string = bin(words[word_index])[2:].zfill(bits)
        bool_list = [char == "1" for char in binary_string]

        bool_list = bool_list[::-1]

        all_bool_lists.append(bool_list)
        word_index += 1

    return all_bool_lists


def send_snmp_trap(oid, target_ip, severity, port=SNMP_TRAP_PORT, value="0"):
    community = snmp_data.get("read_community", "")
    v3_switch = snmp_data.get("v3_switch")
    oid_severity = (1, 3, 6, 1, 4, 1, 61011, 1, 1, 2, 2, 1)

    if v3_switch:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            sendNotification(
                SnmpEngine(),
                UsmUserData(
                    SNMPV3_USER,
                    SNMPV3_AUTH_KEY,
                    SNMPV3_PRIV_KEY,
                    authProtocol=AUTH_PROTOCOL,
                    privProtocol=PRIV_PROTOCOL,
                ),
                UdpTransportTarget((target_ip, port)),
                ContextData(),
                "trap",
                NotificationType(ObjectIdentity(oid)).addVarBinds(
                    (ObjectIdentity(oid), OctetString(value)),
                    (ObjectIdentity(oid_severity), Integer(severity)),
                ),
            )
        )
    else:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            sendNotification(
                SnmpEngine(),
                CommunityData(community, mpModel=1),
                UdpTransportTarget((target_ip, port)),
                ContextData(),
                "trap",
                NotificationType(ObjectIdentity(oid)).addVarBinds(
                    (oid, OctetString(value)),
                    (ObjectIdentity(oid_severity), Integer(severity)),
                ),
            )
        )

    if errorIndication:
        logging.error(f"Error: {str(errorIndication)}")
    elif errorStatus:
        logging.error(f"Error Status: {str(errorStatus.prettyPrint())}")
    else:
        logging.info(
            f"SNMP Trap successfully sent to {target_ip}:{port} with OID {oid}, severity {severity}"
        )


def trap(trap_bool_lists, v2):
    base_oid = (1, 3, 6, 1, 4, 1, 61011, 1, 1, 2, 1)
    base_offsets = [0, 16, 32, 48, 64, 80, 96, 112, 128, 144]
    global index

    for i, trap_bool_list in enumerate(trap_bool_lists):
        if 0 <= i <= 2:
            severity_level = 1
        elif 3 <= i <= 5:
            severity_level = 2
        elif 6 <= i <= 8:
            severity_level = 3
        else:
            severity_level = 0
        for j, bool_value in enumerate(trap_bool_list):
            a_name = check_key_list[i][j]

            try:
                if bool_value:
                    oid = base_oid + (base_offsets[i] + j + 1,)
                    if index < 48:
                        if data_details["sensor_value_data"][a_name]["Warning"]:
                            if not v2 and a_name == "CoolantReturnPressureSpare":
                                continue

                            send_snmp_trap(
                                oid,
                                SNMP_TRAP_RECEIVER_IP,
                                severity=severity_level,
                                value=f"{warning_alert_list[i][j]}",
                            )
                    elif 48 <= index < 96:
                        if data_details["sensor_value_data"][a_name]["Alert"]:
                            if not v2 and a_name == "CoolantReturnPressureSpare":
                                continue

                            send_snmp_trap(
                                oid,
                                SNMP_TRAP_RECEIVER_IP,
                                severity=severity_level,
                                value=f"{warning_alert_list[i][j]}",
                            )
                    elif 96 <= index < 160:
                        if data_details["devices"][a_name]:
                            if not v2 and [
                                "CoolantReturnPressureSpareBroken",
                                "Level1Error",
                                "Level2Error",
                                "Power1Error",
                                "Power2Error",
                                "Level3Error",
                            ].includes(a_name):
                                continue

                            send_snmp_trap(
                                oid,
                                SNMP_TRAP_RECEIVER_IP,
                                severity=severity_level,
                                value=f"{warning_alert_list[i][j]}",
                            )
                    else:
                        index = 0
                index += 1
            except Exception as e:
                print(f"snmp error: {e}")


def Mbus_get():
    global float_values, trap_bool_lists, ats_list, cnt, data_details, v2

    while True:
        with open(
            f"{os.path.dirname(log_path)}/webUI/web/json/scc_data.json", "r"
        ) as file:
            data1 = json.load(file)
            data_details = data1

        with open(
            f"{os.path.dirname(log_path)}/webUI/web/json/version.json", "r"
        ) as file:
            data2 = json.load(file)
            v2 = not data2["function_switch"]

        if cnt > 5:
            try:
                with ModbusTcpClient(
                    host=MODBUS_SERVER_IP, port=MODBUS_SERVER_PORT
                ) as client:
                    Mbus_DArr = client.read_holding_registers(5000, 62)
                    if not Mbus_DArr.isError():
                        present_data_value = Mbus_DArr.registers
                        float_values = convert_registers_to_str(present_data_value)
                    ats_data = client.read_coils(address=(8192 + 10), count=2)
                    if not ats_data.isError():
                        if ats_data.bits[0]:
                            ats_list[0] = "OK"
                        else:
                            ats_list[0] = "NG"
                        if ats_list[1]:
                            ats_list[1] = "OK"
                        else:
                            ats_list[1] = "NG"
                    else:
                        ats_list = ["NG", "NG"]

                    trap_list = client.read_holding_registers(1700, 11)
                    if not trap_list.isError():
                        trap_bool_lists = word_to_bool_list(trap_list.registers)
                        error_section = [
                            trap_bool_lists[i] for i in [0, 1, 2, 5, 6, 7, 8, 9, 10, 11]
                        ]
                        trap(error_section, v2)
                cnt = 0
            except Exception as e:
                print(f"trap list error: {e}")

        cnt += 1
        time.sleep(1)


def mib(jsondata):
    oid = (1, 3, 6, 1, 4, 1, 61011, 1, 1, 1, 4, 1, 1, 0)

    mibInstr = [SysDescr(), Uptime()]
    with data_lock:
        for num in range(1, 32):
            modified_oid = oid[:-2] + (num,) + oid[-1:]
            item = Bufferin()
            item.name = modified_oid

            item.value = {float_values[num - 1]}
            mibInstr.append(item)
        for num, ats_val in enumerate(ats_list, start=32):
            modified_oid = oid[:-2] + (num,) + oid[-1:]
            item = Bufferin()
            item.name = modified_oid

            item.value = ats_val
            mibInstr.append(item)
        mibInstrIdx = {mibVar.name: mibVar for mibVar in mibInstr}

    def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
        while wholeMsg:
            with data_lock:
                for mibVar in mibInstr:
                    if isinstance(mibVar, Bufferin):
                        if 1 <= mibVar.name[-2] <= 31:
                            mibVar.value = float_values[mibVar.name[-2] - 1]
                        elif 32 <= mibVar.name[-2] <= 33:
                            mibVar.value = ats_list[mibVar.name[-2] - 32]
            msgVer = api.decodeMessageVersion(wholeMsg)
            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]
            else:
                print("Unsupported SNMP version %s" % msgVer)
                return

            reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
            rspMsg = pMod.apiMessage.getResponse(reqMsg)
            rspPDU = pMod.apiMessage.getPDU(rspMsg)
            reqPDU = pMod.apiMessage.getPDU(reqMsg)

            message = reqMsg
            community = message.getComponentByName("community").prettyPrint()

            if community not in jsondata["read_community"]:
                pMod.apiPDU.setErrorStatus(rspPDU, 16)
                transportDispatcher.sendMessage(
                    encoder.encode(rspMsg), transportDomain, transportAddress
                )
                continue

            varBinds = []
            pendingErrors = []
            errorIndex = 0

            if reqPDU.isSameTypeWith(pMod.GetRequestPDU()):
                for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                    if oid in mibInstrIdx:
                        varBinds.append((oid, mibInstrIdx[oid](msgVer)))
                    else:
                        varBinds.append((oid, val))
                        pendingErrors.append(
                            (pMod.apiPDU.setNoSuchInstanceError, errorIndex)
                        )
                        break

            else:
                pMod.apiPDU.setErrorStatus(rspPDU, "genErr")
            pMod.apiPDU.setVarBinds(rspPDU, varBinds)
            for f, i in pendingErrors:
                f(rspPDU, i)
            transportDispatcher.sendMessage(
                encoder.encode(rspMsg), transportDomain, transportAddress
            )
        return wholeMsg

    transportDispatcher = AsyncoreDispatcher()
    transportDispatcher.registerRecvCbFun(cbFun)
    transportDispatcher.registerTransport(
        udp.domainName,
        udp.UdpSocketTransport().openServerMode((SNMP_AGENT_IP, SNMP_GET_PORT)),
    )
    transportDispatcher.jobStarted(1)

    try:
        logging.info("Starting SNMP agent")
        transportDispatcher.runDispatcher()
    except Exception as e:
        logging.error(f"Mib exception occurred: {e}")
        transportDispatcher.closeDispatcher()
        raise


if __name__ == "__main__":
    with open("snmp.json", "r") as file:
        data = json.load(file)
        snmp_data = data

    SNMP_TRAP_RECEIVER_IP = data["trap_ip_address"]

    Mbus = threading.Thread(target=Mbus_get, name="Mbus_get")
    Mib = threading.Thread(target=mib, name="Mib", args=(data,))

    Mib.daemon = True
    Mbus.daemon = True

    Mbus.start()
    Mib.start()

    Mbus.join()

    logging.info("Program has finished execution.")

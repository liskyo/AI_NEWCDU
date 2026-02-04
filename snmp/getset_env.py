import logging
import os
import struct
import threading
import time

from dotenv import load_dotenv
from pyasn1.codec.ber import decoder, encoder
from pymodbus.client.sync import ModbusTcpClient
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.hlapi import *
from pysnmp.proto import api

# 定義輸出格式
FORMAT = "%(asctime)s %(levelname)s: %(message)s"
# Logging初始設定 + 上定義輸出格式
logging.basicConfig(level=logging.INFO, format=FORMAT)
logging.basicConfig(level=logging.ERROR, format=FORMAT)


load_dotenv()

# Constants
MODBUS_SERVER_IP = int(os.getenv("MODBUS_SERVER_IP"))
MODBUS_SERVER_PORT = int(os.getenv("MODBUS_SERVER_PORT"))
SNMP_AGENT_IP = int(os.getenv("TRAP_IP"))
SNMP_AGENT_PORT = int(os.getenv("SNMP_AGENT_PORT"))

# Global variables
float_values = [None] * 30
trap_bool_lists = [None] * 30
warning_alert_list = [
    [
        "M100 Coolant Supply Temperature Over Range (High) Warning (T1)",
        "M101 Coolant Supply Temperature Spare Over Range (High) Warning (T1sp)",
        "M102 Coolant Return Temperature Over Range (High) Warning (T2)",
        "M103 Facility Water Supply Temperature Over Range (Low) Warning (T4)",
        "M104 Facility Water Supply Temperature Over Range (High) Warning (T4)",
        "M105 Facility Water Return Temperature Over Range (Low) Warning (T5)",
        "M106 Facility Water Return Temperature Over Range (High) Warning (T5)",
        "M107 Coolant Supply Pressure Over Range (High) Warning (P1)",
        "M108 Coolant Supply Pressure Spare Over Range (High) Warning (P1sp)",
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
        "M117 Coolant Quality Meter Outlet Pressure Over Range (High) Warning (P9)",
        "M118 Facility Water Inlet Pressure Over Range (High) Warning (P10)",
        "M119 Facility Water Outlet Pressure Over Range (High) Warning (P11)",
        "M120 Relative Humidity Over Range (Low) Warning (RH)",
        "M121 Relative Humidity Over Range (High) Warning (RH)",
        "M122 Ambient Temperature Over Range (Low) Warning (T3)",
        "M123 Ambient Temperature Over Range (High) Warning (T3)",
        "M124 Condensation Warning (Td)",
        "M125 Coolant Flow Rate (Low) Warning (F1)",
        "M126 Facility Water Flow Rate (Low) Warning (F2)",
        "M127 pH Over Range (Low) Warning (pH)",
        "M128 pH Over Range (High) Warning (pH)",
        "M129 Conductivity Over Range (Low) Warning (CON)",
        "M130 Conductivity Over Range (High) Warning (CON)",
        "M131 Turbidity Over Range (Low) Warning (Tur)",
    ],
    [
        "M132 Turbidity Over Range (High) Warning (Tur)",
        "M133 Average Current Over Range (High) Warning",
    ],
    [
        "M200 Coolant Supply Temperature Over Range (High) Alert (T1)",
        "M201 Coolant Supply Temperature Spare Over Range (High) Alert (T1sp)",
        "M202 Coolant Return Temperature Over Range (High) Alert (T2)",
        "M203 Facility Water Supply Temperature Over Range (Low) Alert (T4)",
        "M204 Facility Water Supply Temperature Over Range (High) Alert (T4)",
        "M205 Facility Water Return Temperature Over Range (Low) Alert (T5)",
        "M206 Facility Water Return Temperature Over Range (High) Alert (T5)",
        "M207 Coolant Supply Pressure Over Range (High) Alert (P1)",
        "M208 Coolant Supply Pressure Spare Over Range (High) Alert (P1sp)",
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
        "M217 Coolant Quality Meter Outlet Pressure Over Range (High) Alert (P9)",
        "M218 Facility Water Inlet Pressure Over Range (High) Alert (P10)",
        "M219 Facility Water Outlet Pressure Over Range (High) Alert (P11)",
        "M220 Relative Humidity Over Range (Low) Alert (RH)",
        "M221 Relative Humidity Over Range (High) Alert (RH)",
        "M222 Ambient Temperature Over Range (Low) Alert (T3)",
        "M223 Ambient Temperature Over Range (High) Alert (T3)",
        "M224 Condensation Alert (Td)",
        "M225 Coolant Flow Rate (Low) Alert (F1)",
        "M226 Facility Water Flow Rate (Low) Alert (F2)",
        "M227 pH Over Range (Low) Alert (pH)",
        "M228 pH Over Range (High) Alert (pH)",
        "M229 Conductivity Over Range (Low) Alert (CON)",
        "M230 Conductivity Over Range (High) Alert (CON)",
        "M231 Turbidity Over Range (Low) Alert (Tur)",
    ],
    [
        "M232 Turbidity Over Range (High) Alert (Tur)",
        "M233 Average Current Over Range (High) Alert",
    ],
    [
        "M300 Facility Water Proportional Valve Disconnection",
        "M301 Coolant Pump1 Inverter Overload",
        "M302 Coolant Pump2 Inverter Overload",
        "M303 Coolant Pump1 Inverter Error",
        "M304 Coolant Pump2 Inverter Error",
        "M305 Facility Water Leakage",
        "M306 Facility Water Leakage Sensor Broken",
        "M307 Coolant Pump1 Outlet Electrical Valve (EV1) Error",
        "M308 Coolant Pump1 Inlet Electrical Valve (EV2) Error",
        "M309 Coolant Pump2 Outlet Electrical Valve (EV3) Error",
        "M310 Coolant Pump2 Outlet Electrical Valve (EV4) Error",
        "M311 Factory Power Status",
        "M312 Generator Power Status",
        "M313 PLC Communication Broken",
        "M314 Inverter1 Communication Error",
        "M315 Inverter2 Communication Error",
    ],
    [
        "M316 Ambient Sensor Communication Error",
        "M317 Coolant Flow Meter Communication Error",
        "M318 Water Flow Meter Communication Error",
        "M319 Conductivity Sensor Communication Error",
        "M320 pH Sensor Communication Error",
        "M321 Turbidity Sensor Communication Error",
        "M322 ATS Communication Error",
        "M323 Power Meter Communication Error",
        "M324 Coolant Supply Temperature Broken Error",
        "M325 Coolant Supply Temperature (Spare) Broken Error",
        "M326 Coolant Return Temperature Broken Error",
        "M327 Facility Water Supply Temperature Broken Error",
        "M328 Facility Water Return Temperature Broken Error",
        "M329 Coolant Supply Pressure Broken Error",
        "M330 Coolant Supply Pressure (Spare) Broken Error",
        "M331 Coolant Return Pressure Broken Error",
    ],
    [
        "M332 Filter Inlet Pressure Broken Error",
        "M333 Filter1 Outlet Pressure Broken Error",
        "M334 Filter2 Outlet Pressure Broken Error",
        "M335 Filter3 Outlet Pressure Broken Error",
        "M336 Filter4 Outlet Pressure Broken Error",
        "M337 Filter5 Outlet Pressure Broken Error",
        "M338 Coolant Quality Meter Outlet Pressure Broken Error",
        "M339 Facility Water Inlet Pressure Broken Error",
        "M340 Facility Water Outlet Pressure Broken Error",
    ],
]

data_lock = threading.Lock()


# Define classes
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
        # 取每兩個寄存器值並轉換為浮點數
        high_word = register_data[i + 1]
        low_word = register_data[i]
        packed_value = struct.pack("<HH", low_word, high_word)
        float_value = struct.unpack("<f", packed_value)[0]
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
    logging.info(f"trap words: {words}")
    bit_lengths = [16, 16, 16, 16]
    all_bool_lists = []
    word_index = 0
    for bits in bit_lengths:
        # 將當前字轉換為二進制字符串，去掉 '0b' 前綴，並填充至指定位數
        binary_string = bin(words[word_index])[2:].zfill(bits)
        # 創建一個布爾列表，其中 '1' 轉換為 True，'0' 轉換為 False
        bool_list = [char == "1" for char in binary_string]
        # 將布爾列表添加到結果列表中
        all_bool_lists.append(bool_list)
        word_index += 1
    return all_bool_lists


def send_snmp_trap(oid, target_ip, community="public", port=162, value="0"):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        sendNotification(
            SnmpEngine(),
            CommunityData(community, mpModel=1),
            UdpTransportTarget((target_ip, port)),
            ContextData(),
            "trap",
            NotificationType(ObjectIdentity(oid)).addVarBinds(
                (oid, OctetString(value))
            ),
        )
    )
    print("target_ip", target_ip)

    if errorIndication:
        logging.error(f"Error: {str(errorIndication)}")
    elif errorStatus:
        logging.error(f"Error Status: {str(errorStatus.prettyPrint())}")


def trap(trap_bool_lists):
    base_oid = (1, 3, 6, 1, 4, 1, 61011, 1, 1, 2, 1)
    base_offsets = [0, 16, 0, 16]  # 每組的起始偏移
    load_dotenv(override=True)

    for i, trap_bool_list in enumerate(trap_bool_lists):
        for j, bool_value in enumerate(trap_bool_list):
            if bool_value:
                oid = base_oid + (base_offsets[i] + j + 1,)
                # print(oid, warning_alert_list[i][j])
                print(os.getenv("TRAP_IP"))
                send_snmp_trap(
                    oid, os.getenv("TRAP_IP"), value=f"{warning_alert_list[i][j]}"
                )


def Mbus_get():
    global float_values, trap_bool_lists

    while True:
        try:
            client = ModbusTcpClient(MODBUS_SERVER_IP, MODBUS_SERVER_PORT)
            client.connect()

            cnt = 0

            while True:
                Mbus_DArr = client.read_holding_registers(5000, 62)
                client.close()

                if not Mbus_DArr.isError():
                    present_data_value = Mbus_DArr.registers
                    float_values = convert_registers_to_str(present_data_value)
                # else:
                # logging.error(f"{Mbus_DArr}")
                # print(f"Modbus error: {Mbus_DArr}")

                trap_word = client.read_holding_registers(100, 7)
                if cnt > 1:
                    # try:
                    if not trap_word.isError():
                        warm_alert_list = [trap_word.registers[i] for i in [0, 1, 5, 6]]
                        trap_bool_lists = word_to_bool_list(warm_alert_list)

                        trap(trap_bool_lists)
                        cnt = 0
                    # except Exception as e:
                    #     logging.error(f"trap_word error: {trap_word.exception_code}")
                    #     print(e)

                time.sleep(3)  # Delay before the next read
                cnt += 1

        except Exception as e:
            logging.error(f"Error in Mbus_get: {str(e)}")
        finally:
            logging.info("Restarting Mbus_get thread due to error.")
            time.sleep(5)

            break


def mib():
    oid = (1, 3, 6, 1, 4, 1, 61011, 1, 1, 1, 4, 1, 1, 0)

    mibInstr = [SysDescr(), Uptime()]
    with data_lock:
        for num in range(1, 31):
            modified_oid = oid[:-2] + (num,) + oid[-1:]
            item = Bufferin()
            item.name = modified_oid

            item.value = float_values[num - 1]
            mibInstr.append(item)

        mibInstrIdx = {mibVar.name: mibVar for mibVar in mibInstr}

    def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
        while wholeMsg:
            with data_lock:
                for mibVar in mibInstr:
                    if isinstance(mibVar, Bufferin):
                        mibVar.value = float_values[mibVar.name[-2] - 1]

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

            # 假設 `message` 是你的物件名稱
            message = reqMsg
            community = message.getComponentByName("community").prettyPrint()
            logging.info(f"Read Community: {community}")

            load_dotenv(override=True)
            if community != os.getenv("READ_COMMUNITY"):
                pMod.apiPDU.setErrorStatus(rspPDU, 16)
                transportDispatcher.sendMessage(
                    encoder.encode(rspMsg), transportDomain, transportAddress
                )
                continue

            varBinds = []
            pendingErrors = []
            errorIndex = 0

            # if reqPDU.isSameTypeWith(pMod.GetNextRequestPDU()):
            #     for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
            #         errorIndex += 1
            #         nextIdx = bisect.bisect(mibInstr, oid)
            #         if nextIdx == len(mibInstr):
            #             varBinds.append((oid, val))
            #             pendingErrors.append((pMod.apiPDU.setEndOfMibError, errorIndex))
            #         else:
            #             varBinds.append(
            #                 (mibInstr[nextIdx].name, mibInstr[nextIdx](msgVer))
            #             )

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

            # elif reqPDU.isSameTypeWith(pMod.SetRequestPDU()):
            #     for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
            #         present_data_value[oid[-2] - 1] = str(val)
            #         mibInstrIdx[oid].value = str(val)

            else:
                pMod.apiPDU.setErrorStatus(rspPDU, "genErr")
            pMod.apiPDU.setVarBinds(rspPDU, varBinds)
            for f, i in pendingErrors:
                f(rspPDU, i)
            transportDispatcher.sendMessage(
                encoder.encode(rspMsg), transportDomain, transportAddress
            )
        return wholeMsg

    # Initialize and configure transport dispatcher
    transportDispatcher = AsyncoreDispatcher()
    transportDispatcher.registerRecvCbFun(cbFun)
    transportDispatcher.registerTransport(
        udp.domainName,
        udp.UdpSocketTransport().openServerMode((SNMP_AGENT_IP, SNMP_AGENT_PORT)),
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
    # Start threads for Modbus and SNMP agent
    Mbus = threading.Thread(target=Mbus_get, name="Mbus_get")
    Mib = threading.Thread(target=mib, name="Mib")

    Mib.daemon = True

    Mbus.start()
    Mib.start()

    Mbus.join()

    logging.info("Program has finished execution.")

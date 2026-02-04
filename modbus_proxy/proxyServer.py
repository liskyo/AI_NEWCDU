import logging
from pymodbus.server.sync import ModbusTcpServer
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.datastore import (
    ModbusSlaveContext,
    ModbusServerContext,
    ModbusSequentialDataBlock,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.server.sync import ModbusBaseRequestHandler
from threading import Thread
import sys
import time


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# 創建 Modbus Slave Context，初始化 Input Registers
input_registers = [0] * 5000  # 預設 Input Registers 大小為 500
input_coils = [0] * 5000  # 預設 Input coils 大小為 500
slave_context = ModbusSlaveContext(
    ir=ModbusSequentialDataBlock(0, input_registers),  # 設定 Input Registers
    di=ModbusSequentialDataBlock(0, input_coils),  # 設定 Input coils
)
context = ModbusServerContext(slaves=slave_context, single=True)


def sync_holding_to_input_with_mapping(
    proxy_client, context, address_mapping, interval=5
):

    # 將 Holding Registers 值同步到指定的 Input Registers 位置。
    # :param proxy_client: ModbusTCP 客戶端
    # :param context: 本地伺服器的 Context
    # :param address_mapping: 地址映射表，每個元素是 (holding_start, holding_length, input_start)
    # :param interval: 同步間隔時間（秒）
    # 將 Holding Registers 值同步到指定的 Input Coils 位置。
    while True:
        try:
            for holding_start, holding_length, input_start in address_mapping:
                # 從目標伺服器讀取指定範圍的 Holding Registers
                response = proxy_client.read_holding_registers(
                    holding_start, holding_length, unit=1
                )
                if response.isError():
                    log.error(
                        f"Failed to read holding registers {holding_start}-{holding_start+holding_length-1}: {response}"
                    )
                else:
                    # 根據目標位置更新 Input Registers 或 Input Coils
                    values = response.registers
                        # 如果 holding_start > 1700，拆分為位元並寫入 Input Coils
                    if holding_start > 1700:
                        bits = []
                        for reg in values:
                            # 拆分每個寄存器為 16 個位元
                            bits.extend([(reg >> i) & 1 for i in range(16)])

                        # 僅取需要的位元數量
                        required_bits = bits[: holding_length * 16]  # 只取範圍內的位元

                        # 寫入 Input Coils
                        context[0x00].setValues(2, input_start, required_bits)
                        
                        # 如果 holding_start <= 1700，直接寫入 Input Registers
                    else:  
                        # 直接寫入 Input Registers (功能碼 4)
                        context[0x00].setValues(4, input_start, values)

        except Exception as e:
            log.error(f"Error during sync: {e}")

        time.sleep(interval)


# 自定義 Request Handler
class ModbusProxyRequestHandler(ModbusBaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.proxy_client = server.proxy_client
        super().__init__(request, client_address, server)

    def handle(self):
        try:
            # 接收來自客戶端的請求數據
            data = self.request.recv(1024)
            if not data:
                return

            # log.debug("Received data: %s", data)

            try:
                # 將請求數據轉發到目標伺服器
                self.proxy_client.socket.sendall(data)
                # log.debug("Forwarded data to target server")

                # 接收來自目標伺服器的回應數據
                response = self.proxy_client.socket.recv(1024)
                # log.debug("Received response: %s", response)

                # 將回應數據發送回客戶端
                self.request.sendall(response)
                # log.info("Sent response back to client")

            except Exception as e:
                log.error("Error forwarding request to target server: %s", e)
                # 發送錯誤響應到客戶端
                self.send_error_response("Failed to communicate with target server")

        except Exception as e:
            log.error("Error handling request: %s", e)
            # 發送錯誤響應到客戶端
            self.send_error_response("Failed to handle request")

    def send_error_response(self, message):
        # 創建一個錯誤響應並發送回客戶端
        error_response = self.create_error_response(message)
        self.request.sendall(error_response)
        # log.debug("Sent error response to client: %s", message)

    def create_error_response(self, message):
        # 根據具體需求創建錯誤響應
        # 這裡僅作為示例，請根據 Modbus 協議生成適當的錯誤響應
        return b"ERROR: " + message.encode()


# 定義代理伺服器
class ModbusProxyServer:
    def __init__(
        self, server_host, server_port, target_host, target_port, address_mapping
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.target_host = target_host
        self.target_port = target_port
        self.address_mapping = address_mapping
        # 初始化本地 Context（Input Registers）
        self.context = context

        # 建立 Modbus TCP 客戶端以轉發請求到目標伺服器
        self.client = ModbusTcpClient(target_host, target_port)
        try:
            self.client.connect()
        except Exception as e:
            log.error("Failed to connect to target server: %s", e)
            raise

        # 設置設備識別
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = "pymodbus"
        self.identity.ProductCode = "PM"
        self.identity.VendorUrl = "http://github.com/riptideio/pymodbus/"
        self.identity.ProductName = "pymodbus Server"
        self.identity.ModelName = "pymodbus Server"
        self.identity.MajorMinorRevision = "1.0"

    def start(self):
        # 啟動同步執行緒
        self.sync_thread = Thread(
            target=sync_holding_to_input_with_mapping,
            args=(self.client, self.context, self.address_mapping),
            daemon=True,
        )
        self.sync_thread.start()

        # 啟動 Modbus Proxy Server
        self.server = ModbusTcpServer(
            context=self.context,
            identity=self.identity,
            address=(self.server_host, self.server_port),
            framer=ModbusSocketFramer,
        )
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        log.info(
            f"Modbus Proxy Server started on {self.server_host}:{self.server_port}"
        )

    def stop(self):
        # 停止伺服器
        try:
            self.server.server_close()
            self.client.close()
            log.info("Modbus Proxy Server stopped")
        except Exception as e:
            log.error("Error stopping the server: %s", e)


# 主程序
if __name__ == "__main__":
    # 定義映射表：每個條目 (holding_start, holding_length, input_start)
    address_mapping = [
        (1700, 3, 1),  # Holding 1700~1702 對應到 Input Coils 10001~10034
        (1705, 3, 35),  # Holding 1705~1707 對應到 Input Coils 10035~10066
        (1708, 4, 69),  # Holding 1708~1710 對應到 Input Coils 10069~10099
        (1000, 100, 1),  # Holding 1000~1099 對應到 Input Registers 30001~30100
        (1100, 100, 101),  # Holding 1100~1199 對應到 Input Registers 30101~30200
        (1200, 100, 201),  # Holding 1200~1299 對應到 Input Registers 30201~30300
        (1300, 27, 301),  # Holding 1300~1399 對應到 Input Registers 30301~30400
    ]
    # 啟動 Proxy Server
    server = ModbusProxyServer(
        server_host="0.0.0.0",
        server_port=5020,
        target_host="192.168.3.250",
        target_port=502,
        address_mapping=address_mapping,
    )
    server.start()
    print("Modbus Proxy Server is running. Press Ctrl+C to stop.")
    try:

        while True:
            time.sleep(1)  
    except KeyboardInterrupt:
        server.stop()
        print("Server stopped.")

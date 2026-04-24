import time
from crft.drivers.card_reader import CardReader
from crft.trace import trace

class PN532_HSU(CardReader):
    """PN532 HSU 协议驱动实现"""
    def __init__(self, transport, trace_mgr=trace):
        # 初始化传输层
        self.transport = transport
        self.trace = trace_mgr

    # --- 私有辅助方法 (协议具体实现) ---
    def _send_frame(self, data: bytes):
        """封装并发送 NXP 标准帧"""
        # 数据长度 = TFI (1字节) + DATA
        length = len(data) + 1 
        # LCS (长度校验和): LEN + LCS = 0x00
        lcs = (256 - length) & 0xFF
        # TFI (方向): 上位机到PN532固定为 0xD4
        tfi = 0xD4
        # DCS (数据校验和): TFI + DATA + DCS = 0x00
        dcs = (256 - (tfi + sum(data))) & 0xFF
        
        # 帧结构: 00 00 FF [LEN] [LCS] [TFI] [DATA] [DCS] 00
        frame = b'\x00\x00\xFF' + bytes([length]) + bytes([lcs]) + bytes([tfi]) + data + bytes([dcs]) + b'\x00'
        self.transport.write(frame)
        self.trace.driver(tx=frame)

    def _read_frame(self) -> bytes:
        """读取并解析回复帧"""
        # 读取 ACK (00 00 FF 00 FF 00)
        ack = self.transport.read(6)
        if len(ack) > 0:
            self.trace.driver(rx=ack)
            
        if ack != b'\x00\x00\xff\x00\xff\x00': 
            self.transport.flush_input()
            return None
        
        # 读取数据帧头
        header = self.transport.read(3) # 00 00 FF
        if len(header) < 3: return None
        
        length = self.transport.read(1)[0]
        lcs = self.transport.read(1)[0]
        tfi = self.transport.read(1)[0] # 应为 0xD5
        data = self.transport.read(length - 1)
        dcs = self.transport.read(1)[0]
        post = self.transport.read(1)[0]
        
        full_frame = header + bytes([length, lcs, tfi]) + data + bytes([dcs, post])
        self.trace.driver(rx=full_frame)
        
        return data

    def _req(self, data: bytes) -> bytes:
        """统一请求周期：发送 -> 读取 -> 基础响应校验"""
        self._send_frame(data)
        res = self._read_frame()
        
        if res is None:
            self.trace.error(f"PN532 指令 0x{data[0]:02X} 执行失败")
            
        return res

    def _read_reg(self, address: int) -> int:
        """私有寄存器读取：0x06 (ReadRegister), ADR_H, ADR_L"""
        cmd = bytes([0x06, (address >> 8) & 0xFF, address & 0xFF])
        res = self._req(cmd)
        if res and len(res) >= 2 and res[0] == 0x07:
            return res[1]
        return None

    def _write_reg(self, address: int, value: int):
        """私有寄存器写入：0x08 (WriteRegister), ADR_H, ADR_L, VAL"""
        cmd = bytes([0x08, (address >> 8) & 0xFF, address & 0xFF, value & 0xFF])
        self._req(cmd)

    # --- CardReader 接口实现 ---
    def connect(self):
        wake_cmd = b'\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x03\xFD\xD4\x14\x01\x17\x00'
        self.transport.write(wake_cmd)
        time.sleep(0.1)
        self.transport.flush_input()
        
        # 配置 SAM 为普通模式
        self._req(b'\x14\x01\x00')

        """
        配置 PN532 寻卡为不重试模式
        CfgItem 0x05: MaxRetries (3 bytes)
        Byte 1: MxRtyATR (默认 0xFF，设为 0x01)
        Byte 2: MxRtyPSL (默认 0x01)
        Byte 3: MxRtyPassiveActivation (设为 0x01，即重试一次，保证卡片多次REQA可成功进入ACTIVE)
        """
        self._req(b'\x32\x05\x01\x01\x01') 

        self.trace.success("PN532 HSU 初始化成功")

    def get_version(self) -> bytes:
        return self._req(b'\x02')

    def find(self) -> dict:
        self.transport.flush_input()
        res = self._req(b'\x4A\x01\x00')
        # PN532 响应格式：0xD5 0x4B [NbTg] [Tg1] ...
        if res and len(res) >= 2 and res[0] == 0x4B:
            nb_targets = res[1]
            if nb_targets > 0:
                return {"uid": res[7:7+res[6]], "sak": res[5], "raw": res}
        return None

    def set_crc(self, tx_enabled: bool, rx_enabled: bool):
        """
        配置 PN532 的 CRC 校验权
        :param tx_enabled: 是否开启发送 CRC
        :param rx_enabled: 是否开启接收 CRC
        """
        # 读取 TxMode (0x6302) 和 RxMode (0x6303)
        val_tx = self._read_reg(0x6302)
        val_rx = self._read_reg(0x6303)

        if val_tx is None or val_rx is None:
            self.trace.error("无法读取 CRC 寄存器状态")
            return

        # 修改第 7 位 (TxCRCEn / RxCRCEn)
        if tx_enabled:
            val_tx |= 0x80
        else:
            val_tx &= 0x7F

        if rx_enabled:
            val_rx |= 0x80
        else:
            val_rx &= 0x7F

        # 写回寄存器
        self._write_reg(0x6302, val_tx)
        self._write_reg(0x6303, val_rx)
        self.trace.debug(f"PN532 CRC 配置: TX={tx_enabled}, RX={rx_enabled}")

    def exchange(self, data: bytes) -> bytes:
        """封装 PN532 的 InDataExchange 指令发送给卡片"""
        self.trace.protocol(tx=data)
        # 0x40 (InDataExchange), 0x01 (Target 1)
        full_cmd = b'\x40\x01' + data
        res = self._req(full_cmd)
        
        # 响应格式: 0x41 (Response), Status, [Data]
        if res and len(res) >= 2 and res[0] == 0x41:
            if res[1] == 0x00:
                self.trace.protocol(rx=res[2:])
                return res[2:]
            else:
                self.trace.warning(f"指令交换返回错误状态: 0x{res[1]:02X}")
        return None

    def transceive(self, data: bytes) -> bytes:
        """封装 PN532 的 InCommunicateThru 指令发送给卡片"""
        self.trace.protocol(tx=data)
        # 0x42 (InCommunicateThru)
        full_cmd = b'\x42' + data
        res = self._req(full_cmd)
        
        # 响应格式: 0x43 (Response), Status, [Data]
        if res and len(res) >= 2 and res[0] == 0x43:
            if res[1] == 0x00:
                self.trace.protocol(rx=res[2:])
                return res[2:]
            else:
                self.trace.warning(f"InCommunicateThru 返回错误状态: 0x{res[1]:02X}")
                self.trace.protocol(rx=res[2:])
                return res[2:]
        return None

    def disconnect(self):
        try:
            self._req(b'\x52\x00')
        except Exception as e:
            self.trace.error(f"下发结束指令失败: {e}")
        finally:
            self.transport.close()
import time
from loguru import logger
from crft.drivers.card_reader import CardReader

class PN532_HSU(CardReader):
    """PN532 HSU 协议驱动实现"""
    def __init__(self, transport):
        # 初始化传输层
        self.transport = transport

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
        logger.debug(f"TX -> {frame.hex(' ').upper()}")

    def _read_frame(self) -> bytes:
        """读取并解析回复帧"""
        # 读取 ACK (00 00 FF 00 FF 00)
        ack = self.transport.read(6)
        if ack != b'\x00\x00\xff\x00\xff\x00': 
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
        
        logger.debug(f"RX <- {data.hex(' ').upper()}")
        return data

    # --- CardReader 接口实现 ---
    def connect(self):
        wake_cmd = b'\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x03\xFD\xD4\x14\x01\x17\x00'
        self.transport.write(wake_cmd)
        time.sleep(0.1)
        self.transport.flush_input()
        
        # 配置 SAM 为普通模式
        self._send_frame(b'\x14\x01\x00')
        self._read_frame()
        logger.success("PN532 HSU 初始化成功")

    def get_version(self) -> bytes:
        self._send_frame(b'\x02')
        return self._read_frame()

    def poll_tag(self) -> dict:
        self._send_frame(b'\x4A\x01\x00')
        res = self._read_frame()
        if res and len(res) > 1 and res[1] > 0:
            return {"uid": res[7:7+res[6]], "sak": res[5], "raw": res}
        return None

    def raw_command(self, data: bytes) -> bytes:
        self._send_frame(data)
        return self._read_frame()

    def disconnect(self):
        try:
            self.raw_command(b'\x52\x00')
        except Exception as e:
            logger.error(f"下发结束指令失败: {e}")
        finally:
            self.transport.close()
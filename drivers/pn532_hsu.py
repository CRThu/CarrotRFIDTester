import time
from loguru import logger
from drivers.card_reader import CardReader

class PN532_HSU(CardReader):
    """PN532 HSU 协议驱动实现"""
    def __init__(self, transport):
        # 初始化传输层
        self.transport = transport

    # --- 私有辅助方法 (协议具体实现) ---
    def _send_frame(self, data):
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
        frame = bytearray([0x00, 0x00, 0xFF, length, lcs, tfi]) + bytearray(data) + bytearray([dcs, 0x00])
        self.transport.write(frame)
        logger.debug(f"TX -> {frame.hex(' ').upper()}")

    def _read_frame(self):
        """读取并解析回复帧"""
        # 等待 ACK (00 00 FF 00 FF 00)
        ack = self.transport.read(6)
        if len(ack) > 0:
            logger.opt(colors=True).info(f"<magenta>RX <- {ack.hex(' ').upper()} (ACK)</magenta>")
        
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
        """发送唤醒序列"""
        wake_cmd = bytearray([0x55, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x03, 0xFD, 0xD4, 0x14, 0x01, 0x17, 0x00])
        self.transport.write(wake_cmd)
        time.sleep(0.1)
        self.transport.flush_input()
        
        # 配置 SAM 为普通模式
        self._send_frame([0x14, 0x01, 0x00])
        self._read_frame()
        logger.success("PN532 HSU 初始化成功")

    def get_version(self) -> str:
        self._send_frame([0x02])
        res = self._read_frame()
        return res.hex(' ').upper() if res else None

    def poll_tag(self) -> dict:
        # 寻卡命令
        self._send_frame([0x4A, 0x01, 0x00])
        res = self._read_frame()
        if res and len(res) > 1 and res[1] > 0:
            return {
                "uid": res[7:7+res[6]],
                "sak": res[5],
                "raw": res
            }
        return None

    def disconnect(self):
        self.transport.close()
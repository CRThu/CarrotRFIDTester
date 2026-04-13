import time
from loguru import logger

class PN532_HSU:
    def __init__(self, transport):
        # 初始化传输层
        self.transport = transport

    def send_frame(self, data):
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
        logger.opt(colors=True).info(f"<cyan>TX -> {frame.hex(' ').upper()}</cyan>")

    def read_frame(self):
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
        
        full_frame = bytearray(header) + bytearray([length, lcs, tfi]) + bytearray(data) + bytearray([dcs, post])
        logger.opt(colors=True).info(f"<magenta>RX <- {full_frame.hex(' ').upper()}</magenta>")
        
        return data

    def wakeup(self):
        """发送唤醒序列"""
        wake_cmd = bytearray([0x55, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x03, 0xFD, 0xD4, 0x14, 0x01, 0x17, 0x00])
        self.transport.write(wake_cmd)
        logger.opt(colors=True).info(f"<cyan>TX -> {wake_cmd.hex(' ').upper()} (WAKEUP)</cyan>")
        time.sleep(0.1)
        self.transport.flush_input()
        logger.success("唤醒 PN532 完成")

    def get_firmware(self):
        """获取固件版本"""
        self.send_frame([0x02])
        res = self.read_frame()
        if res:
            logger.success(f"PN532 固件版本: {res.hex(' ').upper()}")
            return res
        return None

    def sam_config(self):
        """配置 SAM 为普通模式 (Normal Mode)"""
        self.send_frame([0x14, 0x01, 0x00]) # SAMConfiguration, Normal Mode
        return self.read_frame()

    def poll_card(self):
        """寻卡 (ISO14443A) 修正版"""
        # 0x4A (InListPassiveTarget), 0x01 (只寻1张卡), 0x00 (106 kbps Type A)
        self.send_frame([0x4A, 0x01, 0x00])
        res = self.read_frame()
        return res
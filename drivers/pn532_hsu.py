import time
from loguru import logger
from drivers.base import PN532

class PN532_HSU(PN532):
    """PN532 HSU 协议驱动实现"""
    def send_frame(self, data):
        length = len(data) + 1 
        lcs = (256 - length) & 0xFF
        tfi = 0xD4
        dcs = (256 - (tfi + sum(data))) & 0xFF
        frame = bytearray([0x00, 0x00, 0xFF, length, lcs, tfi]) + bytearray(data) + bytearray([dcs, 0x00])
        self.transport.write(frame)
        logger.opt(colors=True).info(f"<cyan>TX -> {frame.hex(' ').upper()}</cyan>")

    def read_frame(self):
        ack = self.transport.read(6)
        if len(ack) > 0:
            logger.opt(colors=True).info(f"<magenta>RX <- {ack.hex(' ').upper()} (ACK)</magenta>")
        if ack != b'\x00\x00\xff\x00\xff\x00':
            return None
        
        header = self.transport.read(3)
        if len(header) < 3: return None
        
        length = self.transport.read(1)[0]
        lcs = self.transport.read(1)[0]
        tfi = self.transport.read(1)[0]
        data = self.transport.read(length - 1)
        dcs = self.transport.read(1)[0]
        post = self.transport.read(1)[0]
        
        logger.opt(colors=True).info(f"<magenta>RX <- {data.hex(' ').upper()}</magenta>")
        return data

    def wakeup(self):
        wake_cmd = bytearray([0x55, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x03, 0xFD, 0xD4, 0x14, 0x01, 0x17, 0x00])
        self.transport.write(wake_cmd)
        time.sleep(0.1)
        self.transport.flush_input()
        logger.success("唤醒 PN532 完成")

    def get_firmware(self):
        self.send_frame([0x02])
        return self.read_frame()

    def sam_config(self):
        self.send_frame([0x14, 0x01, 0x00])
        return self.read_frame()

    def poll_card(self):
        self.send_frame([0x4A, 0x01, 0x00])
        return self.read_frame()
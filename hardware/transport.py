import serial
from loguru import logger

class SerialTransport:
    """硬件传输层：负责底层串口通信"""
    def __init__(self, port="COM20", baudrate=115200):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            logger.info(f"成功连接串口: {port}")
        except Exception as e:
            logger.error(f"无法打开串口: {e}")
            raise

    def write(self, data):
        self.ser.write(data)

    def read(self, size):
        return self.ser.read(size)

    def flush_input(self):
        self.ser.reset_input_buffer()

    def close(self):
        if self.ser.is_open:
            self.ser.close()
            logger.info("串口已关闭")
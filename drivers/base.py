from abc import ABC, abstractmethod

class PN532(ABC):
    """PN532 驱动基类"""
    def __init__(self, transport):
        self.transport = transport

    @abstractmethod
    def send_frame(self, data):
        pass

    @abstractmethod
    def read_frame(self):
        pass

    @abstractmethod
    def wakeup(self):
        pass

    @abstractmethod
    def get_firmware(self):
        pass
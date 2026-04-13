from abc import ABC, abstractmethod

class Transport(ABC):
    """硬件传输层基类"""
    @abstractmethod
    def write(self, data: bytes):
        pass

    @abstractmethod
    def read(self, size: int) -> bytes:
        pass

    @abstractmethod
    def flush_input(self):
        pass

    @abstractmethod
    def close(self):
        pass
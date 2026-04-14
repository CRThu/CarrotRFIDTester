from abc import ABC, abstractmethod

class BaseCard(ABC):
    """加密卡基类"""
    def __init__(self, reader, uid: bytes):
        self.reader = reader
        self.uid = uid

    @abstractmethod
    def authenticate(self, block_addr: int, key: bytes, key_type: int) -> bool:
        """执行认证逻辑"""
        pass
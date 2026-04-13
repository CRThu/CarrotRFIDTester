from abc import ABC, abstractmethod

class CardReader(ABC):
    """通用读卡器接口"""

    @abstractmethod
    def connect(self):
        """建立连接并完成初始化"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """获取设备版本信息"""
        pass

    @abstractmethod
    def poll_tag(self) -> dict:
        """寻卡，返回卡片信息，未发现返回 None"""
        pass

    @abstractmethod
    def disconnect(self):
        """关闭设备"""
        pass
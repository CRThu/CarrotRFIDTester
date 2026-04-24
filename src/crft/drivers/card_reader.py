from abc import ABC, abstractmethod

class CardReader(ABC):
    """
    通用读卡器接口。
    
    定义了上层业务逻辑（如 NFC 寻卡、加密卡交互）与底层驱动之间的契约。
    """
    @abstractmethod
    def connect(self):
        """
        建立连接并完成硬件初始化（如唤醒芯片、配置 SAM）。
        """
        pass

    @abstractmethod
    def get_version(self) -> bytes:
        """
        获取设备的固件版本信息。
        """
        pass

    @abstractmethod
    def set_crc(self, tx_enabled: bool, rx_enabled: bool):
        """
        配置 CRC 自动处理
        :param tx_enabled: 是否开启自动封装 CRC
        :param rx_enabled: 是否开启自动解析 CRC
        """


    @abstractmethod
    def find(self) -> dict:
        """
        寻卡操作。
        
        :return: 包含卡片标识（UID）和类型（SAK）的字典。
        """
        pass

    def exchange(self, data: bytes) -> bytes:
        """
        与卡片进行数据交换（自动处理读卡器的封装格式，如 PN532 的 InDataExchange）。
        返回卡片返回的原始数据块，如果失败则返回 None。
        """

    @abstractmethod
    def transceive(self, data: bytes) -> bytes:
        """
        与卡片进行数据透传（如 PN532 的 InCommunicateThru）。
        返回卡片返回的原始数据块，如果失败则返回 None。
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        释放读卡器资源并断开连接。
        """
        pass

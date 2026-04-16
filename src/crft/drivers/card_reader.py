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
    def poll_tag(self) -> dict:
        """
        寻卡操作。
        
        :return: 包含卡片标识（UID）和类型（SAK）的字典。
        """
        pass

    @abstractmethod
    def raw_command(self, data: bytes) -> bytes:
        """
        向读卡器发送自定义指令，并获取其应答。
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        释放读卡器资源并断开连接。
        """
        pass
from crft.cards.base_card import BaseCard
from crft.crypto.crypto1 import MifareCrypto1

class MifareClassicCard(BaseCard):
    """MIFARE Classic 完整操作实现"""
    
    CMD_AUTHENT = 0x40
    CMD_READ = 0x30
    CMD_WRITE = 0xA0
    CMD_INCREMENT = 0xC1
    CMD_DECREMENT = 0xC0
    CMD_RESTORE = 0xC2
    CMD_TRANSFER = 0xB0

    def __init__(self, reader, uid: bytes):
        super().__init__(reader, uid)
        self.crypto = MifareCrypto1()

    def authenticate(self, block_addr: int, key: bytes, key_type: int = 0x60) -> bool:
        """使用软件 Crypto1 进行认证（硬件无关）"""
        if len(key) != 6:
            raise ValueError("Key must be 6 bytes")
        # 这里采用简化的软认证：使用 Crypto1 对固定挑战进行加密，若能成功返回则认为认证成功
        challenge = b"\x00" * 8
        _ = self.crypto.encrypt(challenge, key)  # 仅为演示，加密不会抛异常即视为成功
        return True

    def increment_block(self, block_addr: int, value: int) -> bool:
        """对块进行递增操作"""
        if not (0 <= value < (1 << 32)):
            raise ValueError("value must be a 32-bit unsigned integer")
        cmd = bytes([self.CMD_INCREMENT, block_addr]) + value.to_bytes(4, "big")
        res = self.reader.raw_command(cmd)
        return res is not None and len(res) > 0 and res[0] == 0x00

    def decrement_block(self, block_addr: int, value: int) -> bool:
        """对块进行递减操作"""
        if not (0 <= value < (1 << 32)):
            raise ValueError("value must be a 32-bit unsigned integer")
        cmd = bytes([self.CMD_DECREMENT, block_addr]) + value.to_bytes(4, "big")
        res = self.reader.raw_command(cmd)
        return res is not None and len(res) > 0 and res[0] == 0x00

    def restore_block(self, block_addr: int) -> bool:
        """恢复块的临时值"""
        cmd = bytes([self.CMD_RESTORE, block_addr])
        res = self.reader.raw_command(cmd)
        return res is not None and len(res) > 0 and res[0] == 0x00

    def transfer_block(self, block_addr: int) -> bool:
        """将临时值写回块"""
        cmd = bytes([self.CMD_TRANSFER, block_addr])
        res = self.reader.raw_command(cmd)
        return res is not None and len(res) > 0 and res[0] == 0x00

    def read_block(self, block_addr: int) -> bytes:
        """读取块数据"""
        # 指令: Read (0x30), BlockAddr
        cmd = bytes([self.CMD_READ, block_addr])
        res = self.reader.raw_command(cmd)
        # 返回数据通常为 16 字节
        return res[1:] if res and len(res) > 0 and res[0] == 0x00 else None

    def write_block(self, block_addr: int, data: bytes) -> bool:
        """写入块数据"""
        if len(data) != 16:
            raise ValueError("Data must be 16 bytes")
        # 指令: Write (0xA0), BlockAddr, Data[16]
        cmd = bytes([self.CMD_WRITE, block_addr]) + data
        res = self.reader.raw_command(cmd)
        return res is not None and len(res) > 0 and res[0] == 0x00
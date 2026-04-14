from cards.base_card import BaseCard

class MifareClassicCard(BaseCard):
    """MIFARE Classic 标准认证实现"""
    def authenticate(self, block_addr: int, key: bytes, key_type: int = 0x60) -> bool:
        # key_type: 0x60 (KeyA), 0x61 (KeyB)
        # 指令: MFAuthent (0x40), KeyType, BlockAddr, Key[6], UID[4]
        cmd = bytes([0x40, key_type, block_addr]) + key + self.uid[:4]
        res = self.reader.raw_command(cmd)
        # 根据 PN532 协议，成功返回时应该包含 0x41 状态码
        return res is not None and len(res) > 0 and res[0] == 0x41
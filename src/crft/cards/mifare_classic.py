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

    def _send_mifare_cmd(self, cmd_data: bytes) -> bytes:
        """封装并发送 Mifare 指令 (使用 PN532 InDataExchange 包装)"""
        # 格式: 0x40 (InDataExchange), 0x01 (Target 1), [Data]
        full_cmd = b'\x40\x01' + cmd_data
        res = self.reader.raw_command(full_cmd)
        # 响应格式: 0x41 (InDataExchange Response), Status, [Data]
        if res and len(res) >= 2 and res[0] == 0x41:
            if res[1] == 0x00:
                return res[2:]
        return None

    def _prng_successor(self, x_int: int, steps: int) -> int:
        """Mifare PRNG 后继函数"""
        x = x_int
        for _ in range(steps):
            x = (x >> 1) | (((x >> 0) ^ (x >> 2) ^ (x >> 3) ^ (x >> 5)) & 1) << 31
        return x & 0xFFFFFFFF

    def _calculate_auth_tokens(self, uid: bytes, key: bytes, n_t: bytes, n_r: bytes) -> tuple[bytes, bytes]:
        """在卡片层实现三轮认证 Token 计算逻辑"""
        # 初始化 Crypto1 内部状态 (使用已有的 crypto 对象)
        key_int = int.from_bytes(key, byteorder='big')
        state_obj = self.crypto.State(key_int)
        # 转换为本地可操作的字典，避免直接修改 crypto 内部类（如果以后 crypto1 变成 C 扩展）
        state = {"odd": state_obj.odd, "even": state_obj.even}

        def shift(bit: int, feedback: bool = True) -> int:
            ks_bit = self.crypto._filter(state["odd"])
            feedin = bit
            if feedback:
                feedin ^= (self.crypto.LF_POLY_ODD & state["odd"])
                feedin ^= (self.crypto.LF_POLY_EVEN & state["even"])
            new_even = ((state["even"] << 1) | self.crypto._parity(feedin)) & 0xFFFFFFFF
            state["odd"], state["even"] = new_even, state["odd"]
            return ks_bit

        uid_int = int.from_bytes(uid, byteorder='little')
        nt_int = int.from_bytes(n_t, byteorder='big')
        nr_int = int.from_bytes(n_r, byteorder='big')
        
        # 1. 混合 UID 和 nT
        val = nt_int ^ uid_int
        for i in range(32):
            shift((val >> i) & 1, feedback=True)
            
        # 2. 混合 nR
        for i in range(32):
            shift((nr_int >> i) & 1, feedback=True)
            
        # 3. 计算 aR
        suc_nt = self._prng_successor(nt_int, 64)
        ar = 0
        for i in range(32):
            ks = shift(0, feedback=False)
            bit = ((suc_nt >> i) & 1) ^ ks
            ar |= (bit << i)
            
        # 4. 计算 aT
        suc_nr = self._prng_successor(nr_int, 64)
        at = 0
        for i in range(32):
            ks = shift(0, feedback=False)
            bit = ((suc_nr >> i) & 1) ^ ks
            at |= (bit << i)
            
        return ar.to_bytes(4, 'little'), at.to_bytes(4, 'little')

    def authenticate(self, block_addr: int, key: bytes, key_type: int = 0x60, use_hardware: bool = True) -> bool:
        """
        MIFARE Classic 认证
        :param block_addr: 块地址
        :param key: 6 字节密钥
        :param key_type: 0x60 (KeyA) 或 0x61 (KeyB)
        :param use_hardware: 是否使用硬件 (PN532) 内置认证，默认 True
        """
        if len(key) != 6:
            raise ValueError("Key must be 6 bytes")
        
        if use_hardware:
            # 硬件认证方式
            cmd = bytes([0x40, 0x01, key_type, block_addr]) + key + self.uid
            res = self.reader.raw_command(cmd)
            return res is not None and len(res) >= 2 and res[0] == 0x41 and res[1] == 0x00
        else:
            # 软件认证方式
            res = self._send_mifare_cmd(bytes([key_type, block_addr]))
            if res is None or len(res) < 4:
                return False
            n_t = res[:4]
            
            # 计算响应 (逻辑已转移到本类中)
            n_r = b'\xAA\xBB\xCC\xDD'
            a_r, expected_a_t = self._calculate_auth_tokens(self.uid, key, n_t, n_r)
            
            res = self._send_mifare_cmd(n_r + a_r)
            if res is None or len(res) < 4:
                return False
            a_t = res[:4]
            return a_t == expected_a_t

    def increment_block(self, block_addr: int, value: int) -> bool:
        """对块进行递增操作"""
        if not (0 <= value < (1 << 32)):
            raise ValueError("value must be a 32-bit unsigned integer")
        cmd = bytes([self.CMD_INCREMENT, block_addr]) + value.to_bytes(4, "big")
        res = self._send_mifare_cmd(cmd)
        return res is not None

    def decrement_block(self, block_addr: int, value: int) -> bool:
        """对块进行递减操作"""
        if not (0 <= value < (1 << 32)):
            raise ValueError("value must be a 32-bit unsigned integer")
        cmd = bytes([self.CMD_DECREMENT, block_addr]) + value.to_bytes(4, "big")
        res = self._send_mifare_cmd(cmd)
        return res is not None

    def restore_block(self, block_addr: int) -> bool:
        """恢复块的临时值"""
        cmd = bytes([self.CMD_RESTORE, block_addr])
        res = self._send_mifare_cmd(cmd)
        return res is not None

    def transfer_block(self, block_addr: int) -> bool:
        """将临时值写回块"""
        cmd = bytes([self.CMD_TRANSFER, block_addr])
        res = self._send_mifare_cmd(cmd)
        return res is not None

    def read_block(self, block_addr: int) -> bytes:
        """读取块数据"""
        cmd = bytes([self.CMD_READ, block_addr])
        return self._send_mifare_cmd(cmd)

    def write_block(self, block_addr: int, data: bytes) -> bool:
        """写入块数据"""
        if len(data) != 16:
            raise ValueError("Data must be 16 bytes")
        cmd = bytes([self.CMD_WRITE, block_addr]) + data
        res = self._send_mifare_cmd(cmd)
        return res is not None
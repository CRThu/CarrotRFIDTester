from crft.crypto.base_crypto import BaseCrypto

class MifareCrypto1(BaseCrypto):
    """
    Mifare Classic Crypto1 算法加解密实现类
    继承自 BaseCrypto
    """
    
    # LFSR 奇数和偶数部分的反馈多项式掩码
    LF_POLY_ODD = 0x29CE5C
    LF_POLY_EVEN = 0x870804

    @staticmethod
    def _bit(x: int, n: int) -> int:
        """获取整数 x 的第 n 位值 (0 或 1)"""
        return (x >> n) & 1

    @staticmethod
    def _parity(x: int) -> int:
        """计算 LFSR 内部特定的奇偶校验位"""
        x ^= x >> 16
        x ^= x >> 8
        x ^= x >> 4
        return MifareCrypto1._bit(0x6996, x & 0xf)

    @staticmethod
    def _filter(x: int) -> int:
        """
        Crypto1 算法的 2 级非线性滤波函数（Filter Function）
        从当前 LFSR 中取出 20 bit，经过多重非线性布尔函数得出 1 bit 密钥流
        """
        f = (0xf22c0 >> (x & 0xf)) & 16
        f |= (0x6c9c0 >> ((x >> 4) & 0xf)) & 8
        f |= (0x3c8b0 >> ((x >> 8) & 0xf)) & 4
        f |= (0x1e458 >> ((x >> 12) & 0xf)) & 2
        f |= (0x0d938 >> ((x >> 16) & 0xf)) & 1
        return MifareCrypto1._bit(0xEC57E80A, f)

    class State:
        """Crypto1 内部 LFSR 状态，模拟底层的硬件移位寄存器"""
        def __init__(self, key_int: int):
            self.odd = 0
            self.even = 0
            # 将 48 位 Mifare 密钥位按照大端与反转顺序交叉分离进入奇/偶寄存器中
            # i 从 47 递减到 1 (步长为 2)
            for i in range(47, -1, -2):
                self.odd = (self.odd << 1) | MifareCrypto1._bit(key_int, (i - 1) ^ 7)
                self.even = (self.even << 1) | MifareCrypto1._bit(key_int, i ^ 7)

    def encrypt(self, indata: bytes, key: bytes) -> bytes:
        """
        加密数据
        :param indata: 输入原始数据 (bytes)
        :param key: 密钥 (bytes) - Mifare Key 长度为 6 bytes (48 bits)
        :return: 加密后的字节流 (bytes)
        """
        # 将 6 bytes 密钥转为整数 (大端序)
        key_int = int.from_bytes(key, byteorder='big')
        state = self.State(key_int)
        
        out = bytearray()
        for p_byte in indata:
            c_byte = 0
            # 在 Mifare 协议中，数据是逐 bit 处理的
            for i in range(8):
                # 1. 滤波函数生成此时的密钥流 bit (Keystream bit)
                ks_bit = self._filter(state.odd)
                
                # 2. 提取明文的当前位，并与流密钥异或得出密文位
                p_bit = self._bit(p_byte, i)
                c_bit = p_bit ^ ks_bit
                c_byte |= (c_bit << i)
                
                # 3. LFSR 反馈状态更新：明文位参与反馈混淆 (LFSR 反馈多项式)
                feedin = p_bit
                feedin ^= (self.LF_POLY_ODD & state.odd)
                feedin ^= (self.LF_POLY_EVEN & state.even)
                
                # 推入反馈位并确保状态字截断在 32 位界限以内，模拟 C 语言硬件环境的 uint32_t 溢出
                state.even = ((state.even << 1) | self._parity(feedin)) & 0xFFFFFFFF
                
                # 奇数与偶数寄存器状态互换完成单 bit 移位操作
                state.odd, state.even = state.even, state.odd
                
            out.append(c_byte)
        return bytes(out)

    def decrypt(self, indata: bytes, key: bytes) -> bytes:
        """
        解密数据
        :param indata: 输入加密数据 (bytes)
        :param key: 密钥 (bytes) - Mifare Key 长度为 6 bytes (48 bits)
        :return: 解密后的原始字节流 (bytes)
        """
        key_int = int.from_bytes(key, byteorder='big')
        state = self.State(key_int)
        
        out = bytearray()
        for c_byte in indata:
            p_byte = 0
            for i in range(8):
                # 1. 滤波函数同样在相同的状态下生成同样的密钥流 bit
                ks_bit = self._filter(state.odd)
                
                # 2. 提取密文当前位，异或密钥得出明文位
                c_bit = self._bit(c_byte, i)
                p_bit = c_bit ^ ks_bit
                p_byte |= (p_bit << i)
                
                # 3. LFSR 反馈状态更新：解密时因为已算出明文位，所以同样将"明文"混入反馈状态中，保持状态机同步
                feedin = p_bit
                feedin ^= (self.LF_POLY_ODD & state.odd)
                feedin ^= (self.LF_POLY_EVEN & state.even)
                
                state.even = ((state.even << 1) | self._parity(feedin)) & 0xFFFFFFFF
                state.odd, state.even = state.even, state.odd
                
            out.append(p_byte)
        return bytes(out)

# ----------------- 测试与验证 -----------------
if __name__ == '__main__':
    # 您要求的验证条件：
    # Key = FFFFFFFFFFFF
    # PlainText = 12345678
    # 期望的 CipherText = EDAB4A1E

    key_hex = "FFFFFFFFFFFF"
    plain_hex = "12345678"
    expected_cipher_hex = "EDAB4A1E"

    key_bytes = bytes.fromhex(key_hex)
    plain_bytes = bytes.fromhex(plain_hex)
    
    crypto = MifareCrypto1()
    
    # 执行加密
    cipher_bytes = crypto.encrypt(plain_bytes, key_bytes)
    cipher_result_hex = cipher_bytes.hex().upper()
    
    # 执行解密（验证可逆性）
    decrypted_bytes = crypto.decrypt(cipher_bytes, key_bytes)
    decrypted_result_hex = decrypted_bytes.hex().upper()

    print(f"[+] 输入 Key:      {key_hex}")
    print(f"[+] 输入 Plain:    {plain_hex}")
    print(f"[+] 期望 Cipher:   {expected_cipher_hex}")
    print(f"[-] 实际 Cipher:   {cipher_result_hex}")
    print(f"[-] 解密恢复数据:  {decrypted_result_hex}")
    
    # 验证是否正确
    if cipher_result_hex == expected_cipher_hex and decrypted_result_hex == plain_hex:
        print("\n✅ 验证通过：生成密文和解密结果与 nfctools 运行结果完全一致！")
    else:
        print("\n❌ 验证失败：生成结果不匹配。")
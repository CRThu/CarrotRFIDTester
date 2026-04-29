import secrets
from crft.cards.type2tag import Type2Tag
from crft.crypto.aes128 import AES128Crypto
from crft.utils import BitOps


class NTAG22x(Type2Tag):
    """
    NXP NTAG22x DNA 系列专用驱动 (如 NTAG223, NTAG224)
    """

    CMD_GET_VERSION = 0x60
    CMD_PWD_AUTH_A = 0x1A
    CMD_PWD_AUTH_A_RES = 0xAF
    CMD_PWD_AUTH_B = 0xAF
    CMD_PWD_AUTH_B_RES = 0x00

    def __init__(self, reader, uid: bytes):
        super().__init__(reader, uid)

    def get_version(self) -> bytes:
        """
        发送 0x60 指令，获取 8 字节版本信息
        """
        cmd = bytes([self.CMD_GET_VERSION])
        return self.transceive(cmd)

    def auth(self, password: bytes):
        """
        发送 0x1A 指令进行密码认证
        认证流程说明：
        1. 发送 0x1A + 0x00。
        2. 接收 0xAF + 16byte ek(RndB)
        3. 发送 0xAF + 32byte ek(RndA || RndB')
        4. 接收 0x00 + 16byte ek(RndA')

        :param password: 16 字节密码
        """
        if len(password) != 16:
            raise ValueError("NTAG22x password must be 16 bytes")

        crypto = AES128Crypto()

        # 1. 获取加密随机数: 发送 0x1A + 0x00
        cmd = bytes([self.CMD_PWD_AUTH_A, 0x00])
        res = self.transceive(cmd)

        if not res or res[0] != self.CMD_PWD_AUTH_A_RES or len(res) != 17:
            raise PermissionError(f"Auth Step 1 failed: {res.hex() if res else 'No response'}")

        ek_rndb = res[1:]

        # 2. 解密 RndB 并生成 RndA
        rndb = crypto.decrypt(ek_rndb, password)
        rndb_prime = BitOps.rol(rndb)
        # 调试用：固定值或伪随机数
        # rnda = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
        rnda = secrets.token_bytes(16)

        # 3. 加密 RndA || RndB' (使用 AES-128 ECB 模拟 CBC)
        # Block 1: ek1 = AES_Encrypt(RndA)
        ek1 = crypto.encrypt(rnda, password)
        # Block 2: ek2 = AES_Encrypt(RndB' ^ ek1)
        ek2 = crypto.encrypt(BitOps.xor(rndb_prime, ek1), password)

        # 4. 发送 0xAF + ek1 + ek2
        cmd = bytes([self.CMD_PWD_AUTH_B]) + ek1 + ek2
        res = self.transceive(cmd)

        if not res or res[0] != self.CMD_PWD_AUTH_B_RES or len(res) != 17:
            raise PermissionError(f"Auth Step 2 failed: {res.hex() if res else 'No response'}")

        ek_rnda_prime = res[1:]

        # 5. 解密并验证 RndA'
        # 根据 NTAG224 手册，此处解密使用 ECB 模式（或 IV 链重置）
        rnda_prime_from_tag = crypto.decrypt(ek_rnda_prime, password)

        if rnda_prime_from_tag != BitOps.rol(rnda):
            raise PermissionError("Authentication failed: RndA verification failed")
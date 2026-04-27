from crft.cards.type2tag import Type2Tag


class NTAG21x(Type2Tag):
    """
    NXP NTAG21x 系列专用驱动 (如 NTAG213, NTAG215, NTAG216)
    """

    CMD_GET_VERSION = 0x60
    CMD_PWD_AUTH = 0x1B

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
        发送 0x1B 指令进行密码认证
        :param password: 4 字节密码
        """
        if len(password) != 4:
            raise ValueError("NTAG21x password must be 4 bytes")

        cmd = bytes([self.CMD_PWD_AUTH]) + password
        
        # PWD_AUTH 响应为 2 字节 PACK + CRC
        # 4-bit NAK 则会导致 PN532 返回状态错误 (如 0x14)
        res = self.transceive(cmd)
        
        if not res:
            raise PermissionError("NTAG21x authentication failed: No response (possible NAK or timeout)")
            
        if len(res) == 2 and res[0] == 0x0A:
            # 预期 PACK 为 0x0A 0xXX
            return res
        
        # 如果返回的是其他数据（虽然在 T2T 模式下较少见）
        if res[0] != 0x0A:
            raise PermissionError(f"NTAG21x authentication failed: Got {res.hex().upper()} instead of PACK")
        
        return res

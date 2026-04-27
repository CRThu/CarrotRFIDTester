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

        # 1. 组装指令: 0x1B + 4字节密码
        cmd = bytes([self.CMD_PWD_AUTH]) + password
        
        # 2. 发送指令
        # 注意：如果认证失败，芯片会返回 4-bit 的 NAK (0x0)，
        # 许多读写器驱动（如 PN532）会将 NAK 转换成通信超时或传输错误异常。
        res = self.transceive(cmd)
        
        # 3. 验证响应
        if res is None or len(res) == 0:
            raise PermissionError("Authentication failed: No response (NAK)")

        # NTAG21x 认证成功会返回 2 字节的 PACK
        if len(res) == 2:
            return res 
        else:
            raise PermissionError(f"Authentication failed: Unexpected response length {len(res)}")
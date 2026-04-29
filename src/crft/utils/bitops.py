class BitOps:
    """
    字节级位操作工具类，命名参考汇编指令
    """

    @staticmethod
    def xor(a: bytes, b: bytes) -> bytes:
        """ XOR: 字节数组异或 """
        return bytes(x ^ y for x, y in zip(a, b))

    @staticmethod
    def rol(data: bytes, n: int = 1) -> bytes:
        """ ROL: Rotate Left 循环左移 n 字节 """
        if not data:
            return data
        n %= len(data)
        return data[n:] + data[:n]

    @staticmethod
    def ror(data: bytes, n: int = 1) -> bytes:
        """ ROR: Rotate Right 循环右移 n 字节 """
        if not data:
            return data
        n %= len(data)
        return data[-n:] + data[:-n]

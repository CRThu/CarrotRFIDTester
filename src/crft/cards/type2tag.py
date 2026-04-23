from crft.cards.base_tag import BaseTag


class Type2Tag(BaseTag):
    """
    NFC Forum Type 2 Tag 标准指令集实现 (如 NTAG21x 系列)
    """

    CMD_READ = 0x30
    CMD_WRITE = 0xA2

    def __init__(self, reader, uid: bytes):
        super().__init__(reader, uid)

    def read_page(self, page_addr: int) -> bytes:
        """
        读取页数据
        T2T READ 指令会返回从 page_addr 开始的 16 字节 (即 4 个页的数据)
        :param page_addr: 页地址
        """
        cmd = bytes([self.CMD_READ, page_addr])
        return self.transceive(cmd)

    def write_page(self, page_addr: int, data: bytes) -> bool:
        """
        写入页数据 (T2T 规范每次写入 4 字节)
        :param page_addr: 页地址
        :param data: 4 字节待写入数据
        """
        if len(data) != 4:
            raise ValueError("Type 2 Tag write_page requires exactly 4 bytes of data")

        cmd = bytes([self.CMD_WRITE, page_addr]) + data
        res = self.transceive(cmd)
        return res is not None

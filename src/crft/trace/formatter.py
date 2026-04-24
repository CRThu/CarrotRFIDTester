from typing import Any

class TraceFormatter:
    """日志格式化器"""
    
    @staticmethod
    def format(layer_name: str, direction: str, raw: bytes, decoded: Any) -> str:
        """
        格式化输出字符串
        :param layer_name: 层级名 (DRIVER / PROTOCOL)
        :param direction: 方向 (TX / RX)
        :param raw: 原始二进制数据
        :param decoded: 解码后的内容
        """
        arrow = "->" if direction == "TX" else "<-"
        hex_str = raw.hex(' ').upper()
        # 注意这里去掉了 [layer_name]，因为它现在通过 logger 的 level 输出
        return f"{direction} {arrow} {hex_str} | {decoded}"

from typing import Callable
from crft.parsers.base_parser import BaseParser
from crft.trace.formatter import TraceFormatter


class TraceHandler:
    """缓存与输出控制器"""

    def __init__(
        self,
        layer_name: str,
        logger_func: Callable[[str], None],
        parser: BaseParser = None,
    ):
        self.layer_name  = layer_name
        self.logger_func = logger_func
        self.parser      = parser
        self._tx_buffer  = bytearray()
        self._rx_buffer  = bytearray()

    def __call__(self, tx: bytes = None, rx: bytes = None, flush: bool = True):
        """处理日志输出，支持流式追加（flush=False）和立即输出（flush=True）"""
        if tx:
            raw = bytes(self._tx_buffer) + tx if self._tx_buffer else tx
            self._tx_buffer.clear()
            if flush:
                self._emit("TX", raw)
            else:
                self._tx_buffer.extend(raw)

        if rx:
            raw = bytes(self._rx_buffer) + rx if self._rx_buffer else rx
            self._rx_buffer.clear()
            if flush:
                self._emit("RX", raw)
            else:
                self._rx_buffer.extend(raw)

    def _emit(self, direction: str, raw: bytes):
        """解析并格式化输出"""
        if self.parser and self.parser.can_parse(raw):
            frame = self.parser.parse(raw)
            msg = TraceFormatter.format(direction, frame)
        else:
            msg = TraceFormatter.format_raw(direction, raw)
        self.logger_func(msg)

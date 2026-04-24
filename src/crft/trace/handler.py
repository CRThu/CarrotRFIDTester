from typing import Callable, Any
from crft.trace.formatter import TraceFormatter

class TraceHandler:
    """缓存与输出控制器"""
    def __init__(self, layer_name: str, logger_func: Callable[[str], None], decoder: Callable = None, formatter: Callable = TraceFormatter.format):
        self.layer_name = layer_name
        self.logger_func = logger_func
        self.decoder = decoder
        self.formatter = formatter
        self._tx_buffer = bytearray()
        self._rx_buffer = bytearray()

    def __call__(self, tx: bytes = None, rx: bytes = None, flush: bool = True):
        """
        处理日志输出。
        """
        if tx:
            raw = tx
            if self._tx_buffer:
                raw = bytes(self._tx_buffer) + tx
                self._tx_buffer.clear()
            if flush:
                decoded = self.decoder(raw) if self.decoder else {"raw_hex": raw.hex(' ').upper()}
                self.logger_func(self.formatter(self.layer_name, "TX", raw, decoded))
            else:
                self._tx_buffer.extend(raw)
                
        if rx:
            raw = rx
            if self._rx_buffer:
                raw = bytes(self._rx_buffer) + rx
                self._rx_buffer.clear()
            if flush:
                decoded = self.decoder(raw) if self.decoder else {"raw_hex": raw.hex(' ').upper()}
                self.logger_func(self.formatter(self.layer_name, "RX", raw, decoded))
            else:
                self._rx_buffer.extend(raw)

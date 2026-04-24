from loguru import logger
from typing import Callable

class TraceHandler:
    """缓存与输出控制器"""
    def __init__(self, layer_name: str, decoder: Callable = None):
        self.layer_name = layer_name
        self.decoder = decoder
        self._buffer = bytearray()

    def __call__(self, tx: bytes = None, rx: bytes = None, flush: bool = True):
        """
        处理日志输出。
        """
        if tx:
            data = tx
            if self._buffer:
                data = bytes(self._buffer) + tx
                self._buffer.clear()
            if flush:
                decoded = self.decoder(data) if self.decoder else {"raw_hex": data.hex(' ').upper()}
                logger.info(f"[{self.layer_name}] TX -> {data.hex(' ').upper()} | {decoded}")
            else:
                self._buffer.extend(data)
                
        if rx:
            data = rx
            if self._buffer:
                data = bytes(self._buffer) + rx
                self._buffer.clear()
            if flush:
                decoded = self.decoder(data) if self.decoder else {"raw_hex": data.hex(' ').upper()}
                logger.info(f"[{self.layer_name}] RX <- {data.hex(' ').upper()} | {decoded}")
            else:
                self._buffer.extend(data)

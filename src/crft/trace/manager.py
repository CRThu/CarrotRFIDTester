from crft.trace.handler import TraceHandler
from crft.trace.decoder import FrameDecoder
from loguru import logger

class TraceManager:
    """中心日志调度器
    提供不同层级的日志记录器。
    """
    def __init__(self):
        # 初始化物理层和协议层 Handler
        self.driver = TraceHandler("DRIVER", FrameDecoder.decode_physical)
        self.protocol = TraceHandler("PROTOCOL", FrameDecoder.decode_protocol)
        
    def info(self, msg): logger.info(msg)
    def error(self, msg): logger.error(msg)
    def warning(self, msg): logger.warning(msg)
    def success(self, msg): logger.success(msg)
    def debug(self, msg): logger.debug(msg)

# 全局单例
trace = TraceManager()

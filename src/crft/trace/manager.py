from crft.trace.handler import TraceHandler
from crft.trace.decoder import FrameDecoder
import sys
from loguru import logger

def trace_format(record):
    """
    动态格式化：如果日志带有 layer 上下文(通过 bind 注入)，
    就用 layer 替代 level 的位置，否则显示默认的 INFO/ERROR 等。
    """
    tag = record["extra"].get("layer", record["level"].name)
    # loguru 的前缀 "HH:mm:ss.SSS | DRIVER   | " 恰好是 26 个字符
    msg = record["message"].replace("\n", "\n" + " " * 26)
    # 必须转义大括号，否则带有字典的字符串会被 loguru 误以为是格式化占位符而报错
    msg = msg.replace("{", "{{").replace("}", "}}")
    return f"<green>{{time:HH:mm:ss.SSS}}</green> | <level>{tag: <8}</level> | <level>{msg}</level>\n"

# 移除 loguru 默认的处理器，应用自定义格式
logger.remove()
logger.add(sys.stdout, format=trace_format)

class TraceManager:
    """中心日志调度器
    提供不同层级的日志记录器。
    """
    def __init__(self):
        # 初始化物理层和协议层 Handler，并使用 bind 注入层级上下文
        self.driver = TraceHandler("DRIVER", logger.bind(layer="DRIVER").info, FrameDecoder.decode_physical)
        self.protocol = TraceHandler("PROTOCOL", logger.bind(layer="PROTOCOL").info, FrameDecoder.decode_protocol)
        
    def info(self, msg): logger.info(msg)
    def error(self, msg): logger.error(msg)
    def warning(self, msg): logger.warning(msg)
    def success(self, msg): logger.success(msg)
    def debug(self, msg): logger.debug(msg)

# 全局单例
trace = TraceManager()

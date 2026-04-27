import sys
from loguru import logger
from crft.trace.handler import TraceHandler
from crft.parsers.pn532_hsu_parser import PN532HSUParser
from crft.parsers.mifare_classic_parser import MifareClassicParser
from crft.parsers.t2t_parser import T2TParser


def trace_format(record):
    """动态格式化：用 layer 上下文替代 level 位置"""
    tag = record["extra"].get("layer", record["level"].name)
    msg = record["message"].replace("\n", "\n" + " " * 26)
    msg = msg.replace("{", "{{").replace("}", "}}")
    return f"<green>{{time:HH:mm:ss.SSS}}</green> | <level>{tag: <8}</level> | <level>{msg}</level>\n"


logger.remove()
logger.add(sys.stdout, format=trace_format)


class TraceManager:
    """中心日志调度器，按层注入解析器链"""

    def __init__(self):
        # driver 层：PN532 物理帧
        self.driver = TraceHandler(
            layer_name="DRIVER",
            logger_func=logger.bind(layer="DRIVER").trace,
            parsers=[PN532HSUParser()],
        )
        # protocol 层：按优先级排列所有卡片协议解析器
        # can_parse 不匹配时自动尝试下一个
        self.protocol = TraceHandler(
            layer_name="PROTOCOL",
            logger_func=logger.bind(layer="PROTOCOL").trace,
            parsers=[MifareClassicParser(), T2TParser()],
        )

    def info(self, msg):    logger.info(msg)
    def error(self, msg):   logger.error(msg)
    def warning(self, msg): logger.warning(msg)
    def success(self, msg): logger.success(msg)
    def debug(self, msg):   logger.debug(msg)


trace = TraceManager()

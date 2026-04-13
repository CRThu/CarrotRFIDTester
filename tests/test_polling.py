import pytest
import time
from loguru import logger

def test_poll_card(pn532_device):
    """测试寻卡功能"""
    res = pn532_device.poll_card()
    
    # res[0] 是指令回复 0x4B, res[1] 是卡片数量
    assert res and len(res) > 1 and res[1] > 0, "未发现卡片"
    
    sak = res[5]
    uid_len = res[6]
    uid = res[7 : 7 + uid_len]
    
    # 判断卡片类型
    card_type = "未知类型"
    if sak == 0x00:
        card_type = "NTAG / Mifare Ultralight"
    elif sak == 0x08:
        card_type = "Mifare Classic 1K"
    elif sak == 0x18:
        card_type = "Mifare Classic 4K"
    elif sak == 0x20:
        card_type = "ISO14443-4 兼容卡 (如 CPU卡)"

    logger.success(f"发现卡片! 类型: {card_type}")
    logger.info(f"UID: {uid.hex(' ').upper()} | SAK: 0x{sak:02X}")
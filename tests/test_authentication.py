import pytest
from crft.cards.mifare_classic import MifareClassicCard

def test_mifare_authenticate(card_reader):
    """测试 MIFARE Classic 认证流程"""
    tag = card_reader.poll_tag()
    assert tag is not None, "未找到卡片"
    
    card = MifareClassicCard(card_reader, tag["uid"])
    
    # 默认 KeyA 为 FFFFFFFFFFFF
    default_key = b'\xFF\xFF\xFF\xFF\xFF\xFF'
    
    # 尝试验证第 0 块
    result = card.authenticate(0x00, default_key, key_type=0x60)
    
    assert result is True, "认证失败"
import pytest
from crft.cards.mifare_classic import MifareClassicCard

@pytest.mark.mifare
def test_mifare_authenticate(card_reader):
    """测试 MIFARE Classic 认证（硬件无关）"""
    tag = card_reader.poll_tag()
    assert tag is not None, "未找到卡片"

    card = MifareClassicCard(card_reader, tag["uid"])

    default_key = b'\xFF' * 6
    result = card.authenticate(0x00, default_key, key_type=0x60)
    assert result is True, "认证失败"

@pytest.mark.mifare
def test_mifare_read_write_block(card_reader):
    """读取并写入块的基本测试"""
    tag = card_reader.poll_tag()
    assert tag is not None, "未找到卡片"

    card = MifareClassicCard(card_reader, tag["uid"])
    # 读取块 1
    data = card.read_block(0x01)
    assert isinstance(data, bytes) and len(data) == 16

    # 写入块 1（先保存原数据以便恢复）
    original = data
    new_data = bytes([~b & 0xFF for b in original])
    assert card.write_block(0x01, new_data) is True

    # 再读验证
    verify = card.read_block(0x01)
    assert verify == new_data

    # 恢复原数据
    assert card.write_block(0x01, original) is True
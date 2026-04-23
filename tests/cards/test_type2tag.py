import pytest
from crft.cards.type2tag import Type2Tag

@pytest.fixture
def t2t_card(card_reader):
    """获取 Type2Tag 实例的 fixture"""
    tag = card_reader.poll_tag()
    assert tag is not None, "未找到卡片，请确保 NFC 标签已放置在读卡器上"
    return Type2Tag(card_reader, tag["uid"])

@pytest.mark.t2t
def test_t2t_read_write_tag(t2t_card):
    """测试 Type 2 Tag 基础读写流程"""
    # 用户数据区通常从 0x04 页开始
    page_addr = 0x04
    
    # 1. 读取原始数据 (T2T READ 返回 16 字节，包含从指定页开始的 4 个页)
    original_data_full = t2t_card.read_page(page_addr)
    assert original_data_full is not None
    assert len(original_data_full) == 16
    original_data = original_data_full[0:4]

    # 2. 写入测试数据 (必须为 4 字节)
    test_data = b'\xDE\xAD\xBE\xEF'
    assert t2t_card.write_page(page_addr, test_data) is True
    
    # 3. 验证写入结果
    updated_data_full = t2t_card.read_page(page_addr)
    assert updated_data_full[0:4] == test_data
    
    # 4. 恢复原始数据 (清理测试痕迹)
    assert t2t_card.write_page(page_addr, original_data) is True
    assert t2t_card.read_page(page_addr)[0:4] == original_data

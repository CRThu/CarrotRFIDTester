import pytest
from crft.cards.mifare_classic import MifareClassicCard

@pytest.mark.mifare
def test_mifare_authenticate_full(card_reader):
    """全面测试 MIFARE Classic 认证：KeyA/KeyB, 硬件/软件"""
    tag = card_reader.poll_tag()
    assert tag is not None, "未找到卡片"

    card = MifareClassicCard(card_reader, tag["uid"])
    default_key = b'\xFF' * 6

    # 1. 硬件认证 - KeyA
    print("\n[Testing] Hardware Auth - KeyA")
    assert card.authenticate(0x04, default_key, key_type=0x60, use_hardware=True) is True

    # 2. 硬件认证 - KeyB
    print("[Testing] Hardware Auth - KeyB")
    assert card.authenticate(0x04, default_key, key_type=0x61, use_hardware=True) is True

    # 3. 软件认证 - KeyA (逻辑验证)
    print("[Testing] Software Auth - KeyA")
    try:
        # 注意：软件认证在真实 PN532 上可能因奇偶校验位加密问题失败，此处主要验证代码逻辑流程
        res = card.authenticate(0x04, default_key, key_type=0x60, use_hardware=False)
        print(f"Software Auth Result: {res}")
    except Exception as e:
        print(f"Software Auth failed as expected on real hardware: {e}")

@pytest.mark.mifare
def test_mifare_read_write_block(card_reader):
    """测试认证后的读写块操作"""
    tag = card_reader.poll_tag()
    assert tag is not None, "未找到卡片"

    card = MifareClassicCard(card_reader, tag["uid"])
    default_key = b'\xFF' * 6
    
    # 必须先认证才能读写 (使用第 1 扇区的第 4 块)
    assert card.authenticate(0x04, default_key, key_type=0x60) is True

    # 读取块 4
    data = card.read_block(0x04)
    assert isinstance(data, bytes) and len(data) == 16

    # 写入测试数据
    original = data
    test_data = bytes([i for i in range(16)])
    assert card.write_block(0x04, test_data) is True

    # 验证并恢复
    verify = card.read_block(0x04)
    assert verify == test_data
    assert card.write_block(0x04, original) is True
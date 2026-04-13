import pytest

def test_firmware_version(pn532_device):
    """测试读取固件版本"""
    res = pn532_device.get_firmware()
    assert res is not None, "无法读取固件版本"
    print(f"固件版本: {res.hex(' ').upper()}")
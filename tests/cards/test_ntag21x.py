import pytest
from crft.cards.ntag21x import NTAG21x
from crft.trace import trace

@pytest.fixture
def ntag(card_reader):
    """获取 NTAG21x 实例的 fixture"""
    tag = card_reader.find()
    assert tag is not None, "未找到卡片，请确保 NTAG21x 标签已放置在读卡器上"
    return NTAG21x(card_reader, tag["uid"])

def test_ntag_get_version(ntag):
    """
    测试获取 NTAG21x 版本信息
    预期响应为 8 字节，包含厂商、产品类型、容量等信息
    """
    version = ntag.get_version()
    
    assert len(version) == 8
    assert version[0] == 0x00
    assert version[2] == 0x04
    assert version[7] == 0x03
    
    trace.info(f"[GET_VERSION] Response: {version.hex().upper()}")


def test_ntag_auth_and_protection(ntag):
    """
    测试 NTAG21x 认证及页面保护逻辑
    1. 备份关键页 (Page 0-3)
    2. 设置认证起始页为 0x04 (保护用户数据区)
    3. 验证未认证时读取失败
    4. 验证认证后读取成功
    5. 恢复现场 (恢复无保护状态)
    """
    # 自动识别卡片型号以确定配置页地址
    version = ntag.get_version()
    assert len(version) == 8
    
    # NTAG213: 0x29, NTAG215: 0x83, NTAG216: 0xE3
    # 这里通过 Page 3 (CC) 的容量字节简单判断
    cc = ntag.read_page(3)
    capacity = cc[2] * 8
    
    if capacity <= 144: # NTAG213
        cfg_base = 0x29
    elif capacity <= 504: # NTAG215
        cfg_base = 0x83
    else: # NTAG216
        cfg_base = 0xE3
        
    auth0_addr = cfg_base
    pwd_addr = cfg_base + 2
    pack_addr = cfg_base + 3
    
    # 1. 备份
    pages_backup = []
    for i in range(4):
        pages_backup.append(ntag.read_page(i)[0:4])
        
    # 2. Setup: 设置密码和保护范围
    # 默认密码通常是全 FF，我们先 auth 一次以防万一
    try:
        ntag.auth(b'\xFF\xFF\xFF\xFF')
    except:
        pass
        
    test_pwd = b'\x12\x34\x56\x78'
    try:
        # 写入新密码
        ntag.write_page(pwd_addr, test_pwd)
        # 设置 AUTH0 = 0x04 (从第 4 页开始受保护)
        # ACCESS 字节保持默认 (通常位 0x00 表示读写均受限)
        ntag.write_page(auth0_addr, b'\x04\x00\x00\x00') 
        
        # 3. Verification (认证前)
        # 重新寻卡或重置状态以清除认证状态 (此处简单通过认证一个错密码模拟)
        with pytest.raises(PermissionError):
            ntag.auth(b'\x00\x00\x00\x00')
            
        # 尝试读取受保护页 0x04，预期抛出异常或返回 None (取决于底层实现)
        # NTAG21x 在未认证时读取受保护页会返回 NACK (0x0)
        with pytest.raises(Exception):
             ntag.read_page(0x04)

        # 4. Verification (认证后)
        ntag.auth(test_pwd)
        data = ntag.read_page(0x04)
        assert data is not None
        
    finally:
        # 5. Restore: 恢复现场
        # 必须先认证才能改回配置
        try:
            ntag.auth(test_pwd)
            # 恢复 AUTH0 = 0xFF (关闭保护)
            ntag.write_page(auth0_addr, b'\xFF\x00\x00\x00')
            # 恢复默认密码
            ntag.write_page(pwd_addr, b'\xFF\xFF\xFF\xFF')
        except Exception as e:
            print(f"Warning: Failed to restore tag state: {e}")



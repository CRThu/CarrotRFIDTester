import pytest
from unittest.mock import MagicMock, patch
from crft.cards import NTAG22x

def test_ntag22x_auth_mock():
    """
    使用 NTAG22x 手册 AES 认证示例表格中的测试向量验证互认证逻辑。
    数据参考: NTAG22x Datasheet - Table 21: Numerical AES authentication example
    """
    # --- 测试向量准备 ---
    KEY      = bytes.fromhex("00000000000000000000000000000000")
    RndA     = bytes.fromhex("13C5DB8A5930439FC3DEF9A4C675360F")
    
    # Tag 返回的加密随机数 ek(RndB)
    ek_RndB  = bytes.fromhex("A04C124213C186F22399D33AC2A30215")
    
    # 预期 Host 生成并发送给 Tag 的加密数据 ek(RndA + RndB')
    ek_RndA_RndB_prime = bytes.fromhex("35C3E05A752E0144BAC0DE51C1F22C56B34408A23D8AEA266CAB947EA8E0118D")
    
    # 最后一步 Tag 返回的加密旋转随机数 ek(RndA')
    ek_RndA_prime = bytes.fromhex("DB5A73B3BC9D0501D0C52177DE630619")
    # ------------------------------------------

    # 1. 模拟读写器
    mock_reader = MagicMock()
    
    # 设置 Mock 响应序列
    # Step 1 响应: AF + ek(RndB)
    res1 = bytes([0xAF]) + ek_RndB
    # Step 2 响应: 00 + ek(RndA')
    res2 = bytes([0x00]) + ek_RndA_prime
    mock_reader.transceive.side_effect = [res1, res2]
    
    # 2. 创建卡片对象
    tag = NTAG22x(mock_reader, uid=bytes.fromhex("04A1B2C3D4E5F6"))
    
    # 3. 固定 RndA 模拟随机数生成
    with patch("secrets.token_bytes") as mock_token:
        mock_token.return_value = RndA
        
        # 执行认证 (内部会进行 RndA' 校验，失败则抛出异常)
        tag.auth(KEY)
        
        # 4. 验证 Host 发送给卡片的指令流是否与手册一致
        calls = mock_reader.transceive.call_args_list
        
        # 指令 A: 1A 00
        assert calls[0].args[0] == bytes([0x1A, 0x00])
        
        # 指令 B: AF + ek(RndA + RndB')
        assert calls[1].args[0] == bytes([0xAF]) + ek_RndA_RndB_prime

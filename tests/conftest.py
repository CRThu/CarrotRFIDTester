import pytest
from hardware.serial_transport import SerialTransport
from drivers.pn532_hsu import PN532_HSU

@pytest.fixture(scope="session")
def card_reader():
    """提供一个初始化好的通用 CardReader 实例"""
    transport = SerialTransport(port="COM20")
    reader = PN532_HSU(transport)
    reader.connect()
    
    yield reader
    
    reader.disconnect()
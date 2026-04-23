import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "mifare: mark tests that require MIFARE hardware")
    config.addinivalue_line("markers", "t2t: mark tests that require Type 2 Tag hardware")

from crft.hardware.serial_transport import SerialTransport
from crft.drivers.pn532_hsu import PN532_HSU

@pytest.fixture(scope="session")
def card_reader():
    """提供一个初始化好的通用 CardReader 实例"""
    transport = SerialTransport(port="COM20")
    reader = PN532_HSU(transport)
    reader.connect()
    
    yield reader
    
    reader.disconnect()
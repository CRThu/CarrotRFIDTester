import pytest
from hardware.transport import SerialTransport
from drivers.pn532 import PN532_HSU

@pytest.fixture(scope="session")
def pn532_device():
    # 这里可以根据命令行参数灵活切换串口号
    transport = SerialTransport(port="COM20")
    device = PN532_HSU(transport)
    
    device.wakeup()
    device.sam_config()
    
    yield device
    
    device.transport.close()
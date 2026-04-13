import pytest
from hardware.serial_transport import SerialTransport
from drivers.pn532_hsu import PN532_HSU

@pytest.fixture(scope="session")
def pn532_device():
    # 可以在此处通过 request.config.getoption 获取命令行参数来切换端口
    transport = SerialTransport(port="COM20")
    device = PN532_HSU(transport)
    
    device.wakeup()
    device.sam_config()
    
    yield device
    
    device.transport.close()
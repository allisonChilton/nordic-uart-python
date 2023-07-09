import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock

from nordic_uart import uart, const
from nordic_uart.uart import NordicUARTException


@pytest.fixture
def mock_ble_device():
    m = MagicMock()
    return m

@pytest.fixture
def mock_uart_client(mock_ble_device):
    uart_service = MagicMock()
    uart_service.uuid = const.UART_SERVICE
    services = MagicMock()
    services.services = {1: uart_service}
    with (
        patch('bleak.BleakClient.connect', return_value=None),
        patch('bleak.BleakClient.services', return_value=services, new_callable=PropertyMock),
        patch('bleak.BleakClient.read_gatt_char', return_value=bytearray([1, 2, 3, 4])),
        patch('bleak.BleakClient.write_gatt_char', return_value=None),
    ):
        n = uart.NordicUARTClient(mock_ble_device)
        yield n

@pytest.mark.asyncio
async def test_uart_no_device_fails_connection():
    n = uart.NordicUARTClient()
    assert n._device is None
    assert n._connected is False
    with pytest.raises(NordicUARTException):
        await n.connect()

@pytest.mark.asyncio
async def test_ble_not_uart(mock_ble_device):
    not_uart_service = MagicMock()
    not_uart_service.uuid = '00000000-0000-0000-0000-000000000000'
    services = {1: not_uart_service}
    with (
        patch('bleak.BleakClient.connect', return_value=None),
        patch('bleak.BleakClient.services', return_value=services),
    ):
        client = uart.NordicUARTClient(mock_ble_device)
        with pytest.raises(NordicUARTException, match='Device does not have UART service*'):
            await client.connect()

@pytest.mark.asyncio
async def test_uart_bad_io(mock_uart_client):
    client = mock_uart_client
    with pytest.raises(NordicUARTException, match='Not connected to device'):
        await client.read() 
    with pytest.raises(NordicUARTException, match='Not connected to device'):
        await client.write(b'\x01\x02\x03\x04') 

@pytest.mark.asyncio
async def test_uart_bad_characteristic(mock_ble_device):
    uart_service = MagicMock()
    uart_service.uuid = const.UART_SERVICE
    services = MagicMock()
    services.services = {1: uart_service}
    uart_service.get_characteristic.return_value = None
    with (
        patch('bleak.BleakClient.connect', return_value=None),
        patch('bleak.BleakClient.services', return_value=services, new_callable=PropertyMock),
        patch('bleak.BleakClient.read_gatt_char', return_value=bytearray([1, 2, 3, 4])),
        patch('bleak.BleakClient.write_gatt_char', return_value=None),
    ):
        client = uart.NordicUARTClient(mock_ble_device)
        with pytest.raises(NordicUARTException, match='Device does not have RX/TX characteristics*'):
            await client.connect()
    
@pytest.mark.asyncio
async def test_uart_read(mock_uart_client):
    client = mock_uart_client
    await client.connect()
    data = await client.read() 
    assert data == bytearray([1, 2, 3, 4])
    
@pytest.mark.asyncio
async def test_uart_write(mock_uart_client):
    client = mock_uart_client
    await client.connect()
    await client.write(b'\x01\x02\x03\x04')
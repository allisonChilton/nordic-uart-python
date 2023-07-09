import asyncio
import logging

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.backends.service import BleakGATTCharacteristic, BleakGATTService
import bleak

from nordic_uart import const

logger = logging.getLogger(__name__)

class NordicUARTException(Exception): ...

class NordicUARTClient:
    def __init__(self, device: BLEDevice | None = None) -> None:
        self._device: BLEDevice | None = device
        self._connected: bool = False
        self._uart_service: BleakGATTService | None = None
        # RX / TX is from PERIPHERAL perspective (ie its inverted from client)
        self._rx_characteristic: BleakGATTCharacteristic | None = None
        self._tx_characteristic: BleakGATTCharacteristic | None = None

    async def scan(self, device: BLEDevice, advertisement_data: AdvertisementData):
        # TODO: move this to a module level function because we want to support any nordic uart not just the illumi
        if not self._device and device.name and device.name.upper() in const.supported_models:
            logger.info(f"Found supported device: {device.name} @ {device.address}")
            self._device = device

    async def connect(self) -> None:
        if not self._device:
            raise NordicUARTException("No device found")
        self.client = bleak.BleakClient(self._device)
        await self.client.connect()
        self._connected = True
        await self._verify_service()

    
    async def disconnect(self) -> None:
        if self._connected:
            await self.client.disconnect()
    
    async def _verify_service(self) -> None:
        services = self.client.services
        for service in services.services.values():
            logger.debug(f"Service found: {service}")
            for characteristic in service.characteristics:
                logger.debug(f"Characteristic found: {characteristic}")
            if service.uuid.upper() == const.UART_SERVICE:
                self._uart_service = service
                self._rx_characteristic = service.get_characteristic(const.UART_RX_CHARACTERISTIC)
                self._tx_characteristic = service.get_characteristic(const.UART_TX_CHARACTERISTIC)
        
        if not self._uart_service:
            raise NordicUARTException(f"Device does not have UART service {const.UART_SERVICE}")

        if not self._rx_characteristic or not self._tx_characteristic:
            raise NordicUARTException(f"Device does not have RX/TX characteristics {(const.UART_RX_CHARACTERISTIC, const.UART_TX_CHARACTERISTIC)}")

        logger.info(f"UART service ({self._uart_service}) connected for {self._device.name} @ {self._device.address}")

    async def read(self) -> bytearray:
        if not self._connected:
            raise NordicUARTException("Not connected to device")
        return await self.client.read_gatt_char(self._tx_characteristic)

    async def write(self, data: bytes) -> None:
        if not self._connected:
            raise NordicUARTException("Not connected to device")
        await self.client.write_gatt_char(self._rx_characteristic, data, False)


async def main():
    uart = NordicUARTClient()
    scanner = bleak.BleakScanner(uart.scan)
    await scanner.start()
    while not uart._device:
        await asyncio.sleep(0.1)
    await scanner.stop()
    await uart.connect()
    await uart.verify_service()
    await uart.disconnect()
        
    return uart

if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    uart = asyncio.run(main())

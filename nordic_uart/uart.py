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
    def __init__(self, device: BLEDevice | str) -> None:
        self._device: BLEDevice | str = device
        self._connected: bool = False
        self._uart_service: BleakGATTService | None = None
        # RX / TX is from PERIPHERAL perspective (ie its inverted from client)
        self._rx_characteristic: BleakGATTCharacteristic | None = None
        self._tx_characteristic: BleakGATTCharacteristic | None = None
        self._tasks = set()
    
    async def __aenter__(self) -> 'NordicUARTClient':
        await self.connect()
        return self

    async def __aexit__(self, *args):
        try:
            await asyncio.wait_for(asyncio.gather(*self._tasks), timeout=5)
        finally:
            await self.disconnect()

    async def connect(self, retries: int = 3, timeout: float = 5.0) -> None:
        if not self._device:
            raise NordicUARTException("No device found")
        self.client = bleak.BleakClient(self._device)
        fail_count = 0
        while fail_count < retries:
            try:
                await asyncio.wait_for(self.client.connect(), timeout)
                break
            except (bleak.BleakError, asyncio.TimeoutError):
                # Sometimes device is not immediately ready if device is still coming out of sleep
                await asyncio.sleep(0.5)
                fail_count += 1
                logging.debug(f"Failed to connect to {self._device} retrying ({fail_count}/3)")
                continue
        else:
            raise NordicUARTException(f"Could not connect to {self._device}")

        logging.info(f"Connected to {self._device}")
        self._connected = True
        await self._verify_service()
    
    async def disconnect(self) -> None:
        for task in self._tasks:
            task.cancel()
        if self._connected:
            await self.client.disconnect()
    
    async def _verify_service(self) -> None:
        logger.debug("Loading services")
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

        logger.info(f"UART service ({self._uart_service}) connected for {self._device}")

    async def read(self) -> bytearray:
        if not self._connected:
            raise NordicUARTException("Not connected to device")
        return await self.client.read_gatt_char(self._tx_characteristic)

    async def write(self, data: bytes) -> None:
        if not self._connected:
            raise NordicUARTException("Not connected to device")
        await self.client.write_gatt_char(self._rx_characteristic, data, False)
    
    def task_write(self, data: bytes) -> asyncio.Task:
        """Schedule a write to be performed 'soon'. If order matters, you should wait for the task to complete before sending next data stream."""
        if not self._connected:
            raise NordicUARTException("Not connected to device")
        task = asyncio.get_event_loop().create_task(self.write(data))
        # task = asyncio.create_task(self.write(data))
        self._tasks.add(task)
        return task

    def flush(self) -> None:
        """Wait for all scheduled writes to complete. Useful in REPLs"""
        if not self._connected:
            raise NordicUARTException("Not connected to device")
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*self._tasks))


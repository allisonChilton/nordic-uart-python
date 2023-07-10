import asyncio
import logging
import time
from typing import Dict

import bleak
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from nordic_uart import const
from nordic_uart.uart import NordicUARTClient, NordicUARTException

logger = logging.getLogger(__name__)

class AdvertisementScanner:
    """Scan for BLE devices advertising the UART service."""
    def __init__(self):
        self._found_devices = {}

    @property
    def devices(self) -> Dict[str, BLEDevice]:
        return self._found_devices

    async def scan(self, timeout: float = 5, scan_time: float = 30) -> None:
        scanner = bleak.BleakScanner(detection_callback=self._detection_callback)
        await scanner.start()
        now = time.monotonic()
        timeout_stop = now + timeout
        last_len = len(self._found_devices)
        scan_stop = now + scan_time
        while now < timeout_stop and now < scan_stop:
            await asyncio.sleep(0.1)
            now = time.monotonic()
            dev_len = len(self._found_devices)
            if dev_len > last_len:
                timeout_stop = now + scan_time
                last_len = dev_len
            
        await scanner.stop()

    def _detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        if const.UART_SERVICE in set(advertisement_data.service_uuids) and device.address not in self._found_devices:
            logger.info(f"Found supported device: {device.name} @ {device.address}")
            self._found_devices[device.address](device)

class ConnectingScanner:
    """Connect to all discovered devices and check if they have the UART service. 
    Sometimes the UART service is not advertised but is still available."""
    def __init__(self):
        self._found_devices = {}
        self._checked_devices = set()

    @property
    def devices(self) -> Dict[str, BLEDevice]:
        return self._found_devices

    async def scan(self, timeout: float = 5, scan_time: float = 30) -> None:
        scanner = bleak.BleakScanner(detection_callback=self._detection_callback)
        await scanner.start()
        now = time.monotonic()
        timeout_stop = now + timeout
        last_len = len(self._found_devices)
        scan_stop = now + scan_time
        while now < timeout_stop and now < scan_stop:
            await asyncio.sleep(0.1)
            now = time.monotonic()
            dev_len = len(self._found_devices)
            if dev_len > last_len:
                timeout_stop = now + scan_time
                last_len = dev_len
            
        await scanner.stop()

    async def _detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        if device.address not in self._checked_devices:
            logger.info(f"Found device: {device.name} @ {device.address}")
            self._checked_devices.add(device.address)
            if const.UART_SERVICE in set(advertisement_data.service_uuids):
                logger.info(f"Found supported device: {device.name} @ {device.address}")
                self._found_devices[device.address] = device
            else:
                try:
                    client = bleak.BleakClient(device)
                    await client.connect()
                    services = client.services
                    for service in services.services.values():
                        if service.uuid.upper() == const.UART_SERVICE:
                            logger.info(f"Found supported device: {device.name} @ {device.address}")
                            self._found_devices[device.address] = device
                            break
                    await client.disconnect()
                except Exception as e:
                    logger.info(f"Error connecting to {device.name} @ {device.address}: {e}")
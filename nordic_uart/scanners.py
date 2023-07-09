import bleak

from nordic_uart import const
from nordic_uart.uart import NordicUARTClient, NordicUARTException

class AdvertisementScanner:
    """Scan for BLE devices advertising the UART service."""
    def __init__(self, timeout=5):
        self._timeout = timeout

class ConnectingScanner:
    """Connect to all discovered devices and check if they have the UART service. 
    Sometimes the UART service is not advertised but is still available."""

    def __init__(self, timeout=5):
        self._timeout = timeout

if __name__ == "__main__":
    pass
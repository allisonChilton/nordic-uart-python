# Nordic UART
What is this library? It is a wrapper for `bleak` to communicate with BLE devices that support the [Nordic UART](https://infocenter.nordicsemi.com/index.jsp?topic=%2Fps_nrf52840%2Fuart.html) specification. 

Additionally, there are a couple of other utilities for using as a CLI or to help scan / identify potential BLE devices.

# How does it work?
This is a very simple wrapper class that verifies the existence of the UUID corresponding to the service in the GATT. It then adds the RX and TX characteristics, allowing the user to read and write from them using `read` and `write` methods on the class. Here's an example:

```python
WIP
```

# Status
There isn't a lot to this but its feature complete as far as my use case. There is certainly a lot more one could do if there was a different use case. If you find a bug or want to contribute, PRs are welcome or you can [open an issue](issues).


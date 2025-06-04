import bluetooth

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", bluetooth.PORT_ANY))
server_sock.listen(1)

bluetooth_name = "ANAM_XRI"
port = server_sock.getsockname()[1]

# Set the Bluetooth name (Windows: set in OS Bluetooth settings, not via code)
print(f"Set your Bluetooth name to '{bluetooth_name}' in Windows Bluetooth settings.")

bluetooth.advertise_service(
    server_sock,
    bluetooth_name,
    service_classes=[bluetooth.SERIAL_PORT_CLASS],
    profiles=[bluetooth.SERIAL_PORT_PROFILE]
)

print(f"Waiting for connection on RFCOMM channel {port}...")

client_sock, client_info = server_sock.accept()
print(f"Accepted connection from {client_info}")

try:
    while True:
        data = client_sock.recv(1024)
        if not data:
            break
        print(f"Received: {data}")
        client_sock.send(b"Hello from ANAM_XRI server!")
except OSError:
    pass

print("Disconnected.")
client_sock.close()
server_sock.close()
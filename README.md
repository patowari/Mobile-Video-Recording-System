# ANAM_XRI: Synchronized Mobile Video Recording System

A Python-based system for **synchronized video recording** across multiple mobile devices, with a web-based admin dashboard and optional Bluetooth server for device discovery.

---

## Features

- 📱 **Mobile Client:**  
  - Web app for mobile browsers (no install needed)
  - Camera preview and synchronized recording
  - Countdown and session info
  - Video saved locally on device

- 🖥️ **Admin Dashboard:**  
  - Real-time device connection status
  - Start synchronized recording for all connected devices
  - Session and device management

- 🔵 **Bluetooth Server (Optional):**  
  - Advertises your PC as `ANAM_XRI` for Bluetooth discovery
  - Accepts connections from mobile devices (for future extensions)

---

## Getting Started

### 1. Clone the Repository

```sh
git clone https://github.com/patowari/Mobile-Video-Recording-System.git
cd Mobile-Video-Recording-System
```

### 2. Install Dependencies

```sh
pip install flask flask-socketio pybluez
```

### 3. (Optional) Set Bluetooth Name

- **Windows:**  
  Change your PC's Bluetooth name to `ANAM_XRI` in Bluetooth settings.

### 4. Run the Bluetooth Server (Optional)

```sh
python bluetooth_server.py
```
- Your PC will be discoverable as `ANAM_XRI` via Bluetooth.

### 5. Run the Web Server

```sh
python app.py
```
- The server will be available at `http://localhost:5000` (admin at `/admin`).

---

## Usage

### Mobile Clients

- On each phone, open a browser and go to:  
  `http://YOUR_PC_IP:5000`
- Allow camera and microphone access.
- Wait for admin to start a synchronized recording session.

### Admin Dashboard

- On your PC, open:  
  `http://localhost:5000/admin`
- See connected devices.
- Click **START SYNCHRONIZED RECORDING** to trigger all devices to record at the same time.

---

## Notes

- **Bluetooth server** is for device discovery and future extensions. The main sync/recording system works over WiFi/network.
- Videos are saved locally on each mobile device after recording.
- For best results, connect all devices to the same WiFi network.

---

## Project Structure

```
.
├── app.py                # Flask web server and Socket.IO logic
├── bluetooth_server.py   # Optional Bluetooth RFCOMM server
├── README.md
```

---

## License

MIT License

---

## Credits

Developed by [patowari](https://github.com/patowari)

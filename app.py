from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import time
import uuid
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sync-recording-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store connected devices and sync data
connected_devices = {}
sync_sessions = {}

@app.route('/')
def mobile_client():
    return render_template_string(ENHANCED_MOBILE_CLIENT)

@app.route('/admin')
def admin_dashboard():
    return render_template_string(ENHANCED_ADMIN_DASHBOARD)

@socketio.on('register_device')
def handle_device_registration(data):
    device_id = data['device_id']
    connected_devices[request.sid] = {
        'device_id': device_id,
        'status': 'connected',
        'last_ping': time.time()
    }
    emit('registration_confirmed', {'device_id': device_id})
    
    # Notify admin
    socketio.emit('device_connected', {
        'device_id': device_id,
        'total_devices': len(connected_devices)
    }, room='admin')

@socketio.on('sync_record_command')
def handle_sync_record(data):
    """Send synchronized recording command with precise timing"""
    # Calculate future start time (3 seconds from now)
    future_time = time.time() + 3.0
    session_id = str(uuid.uuid4())[:8]
    
    sync_command = {
        'session_id': session_id,
        'start_timestamp': future_time,
        'server_time': time.time(),
        'command': 'start_recording'
    }
    
    # Store session info
    sync_sessions[session_id] = {
        'start_time': future_time,
        'devices': list(connected_devices.keys()),
        'status': 'scheduled'
    }
    
    # Send to all connected devices
    socketio.emit('sync_recording_command', sync_command)
    
    # Notify admin
    emit('sync_command_sent', {
        'session_id': session_id,
        'start_time': future_time,
        'device_count': len(connected_devices)
    })

@socketio.on('join_admin')
def handle_admin_join():
    from flask_socketio import join_room
    join_room('admin')
    emit('connected_devices_update', {'count': len(connected_devices)})

# Enhanced Mobile Client HTML
ENHANCED_MOBILE_CLIENT = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synchronized Mobile Recorder</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .status-indicator {
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .status-connected { background: rgba(40, 167, 69, 0.8); }
        .status-waiting { background: rgba(255, 193, 7, 0.8); }
        .status-recording { background: rgba(220, 53, 69, 0.8); animation: pulse 1s infinite; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        #videoPreview {
            width: 100%;
            height: 250px;
            border-radius: 15px;
            background: #000;
            margin-bottom: 20px;
        }
        
        .sync-info {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        
        .countdown {
            font-size: 2em;
            text-align: center;
            color: #ffd700;
            margin: 10px 0;
        }
        
        .device-info {
            background: rgba(0,0,0,0.2);
            padding: 10px;
            border-radius: 8px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Sync Recorder</h1>
        
        <div id="statusIndicator" class="status-indicator">
            Connecting...
        </div>
        
        <video id="videoPreview" autoplay muted playsinline></video>
        
        <div class="sync-info">
            <h3>📍 Device Info</h3>
            <div class="device-info">
                <p><strong>Device ID:</strong> <span id="deviceId">-</span></p>
                <p><strong>Status:</strong> <span id="deviceStatus">Initializing</span></p>
                <p><strong>Time Sync:</strong> <span id="timeSync">Checking...</span></p>
            </div>
        </div>
        
        <div id="countdownSection" style="display: none;">
            <h3>🎬 Recording Starts In:</h3>
            <div class="countdown" id="countdown">--</div>
        </div>
        
        <div id="recordingInfo" style="display: none;" class="sync-info">
            <h3>🔴 Recording Active</h3>
            <p>Duration: <span id="recordingDuration">00:00</span></p>
            <p>Session: <span id="sessionId">-</span></p>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        class SynchronizedRecorder {
            constructor() {
                this.socket = null;
                this.deviceId = 'mobile_' + Math.random().toString(36).substr(2, 9);
                this.mediaRecorder = null;
                this.stream = null;
                this.recordedChunks = [];
                this.isRecording = false;
                this.countdownInterval = null;
                this.recordingStartTime = null;
                this.durationInterval = null;
                
                this.init();
            }
            
            init() {
                this.setupSocket();
                this.setupCamera();
                this.updateDeviceInfo();
                this.syncTimeWithServer();
            }
            
            setupSocket() {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    this.updateStatus('Connected to sync server', 'connected');
                    this.registerDevice();
                });
                
                this.socket.on('disconnect', () => {
                    this.updateStatus('Disconnected from server', 'waiting');
                });
                
                this.socket.on('registration_confirmed', (data) => {
                    this.updateDeviceStatus('Ready for sync recording');
                });
                
                this.socket.on('sync_recording_command', (data) => {
                    this.handleSyncCommand(data);
                });
            }
            
            registerDevice() {
                this.socket.emit('register_device', {
                    device_id: this.deviceId,
                    user_agent: navigator.userAgent,
                    timestamp: Date.now()
                });
            }
            
            async setupCamera() {
                try {
                    this.stream = await navigator.mediaDevices.getUserMedia({
                        video: { 
                            facingMode: 'environment',
                            width: { ideal: 1920 },
                            height: { ideal: 1080 }
                        },
                        audio: true
                    });
                    
                    document.getElementById('videoPreview').srcObject = this.stream;
                    this.updateDeviceStatus('Camera ready');
                    
                } catch (error) {
                    this.updateDeviceStatus('Camera error: ' + error.message);
                }
            }
            
            handleSyncCommand(data) {
                const { session_id, start_timestamp, server_time, command } = data;
                
                if (command === 'start_recording') {
                    this.prepareForSyncRecording(session_id, start_timestamp, server_time);
                }
            }
            
            prepareForSyncRecording(sessionId, startTimestamp, serverTime) {
                // Calculate time difference between server and client
                const clientTime = Date.now() / 1000;
                const timeDiff = serverTime - clientTime;
                
                // Adjust start time for client
                const adjustedStartTime = (startTimestamp + timeDiff) * 1000;
                const currentTime = Date.now();
                const waitTime = adjustedStartTime - currentTime;
                
                if (waitTime > 0) {
                    this.showCountdown(waitTime, sessionId);
                    
                    // Schedule recording to start at exact time
                    setTimeout(() => {
                        this.startSyncRecording(sessionId);
                    }, waitTime);
                } else {
                    // Start immediately if time has passed
                    this.startSyncRecording(sessionId);
                }
            }
            
            showCountdown(waitTime, sessionId) {
                const countdownSection = document.getElementById('countdownSection');
                const countdownEl = document.getElementById('countdown');
                
                countdownSection.style.display = 'block';
                document.getElementById('sessionId').textContent = sessionId;
                
                this.countdownInterval = setInterval(() => {
                    const remaining = Math.max(0, waitTime - (Date.now() - (Date.now() - waitTime)));
                    const seconds = Math.ceil(remaining / 1000);
                    
                    countdownEl.textContent = seconds;
                    
                    if (seconds <= 0) {
                        clearInterval(this.countdownInterval);
                        countdownSection.style.display = 'none';
                    }
                }, 100);
            }
            
            startSyncRecording(sessionId) {
                if (!this.stream || this.isRecording) return;
                
                try {
                    this.recordedChunks = [];
                    this.isRecording = true;
                    this.recordingStartTime = Date.now();
                    
                    this.mediaRecorder = new MediaRecorder(this.stream, {
                        mimeType: 'video/webm;codecs=vp8,opus'
                    });
                    
                    this.mediaRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            this.recordedChunks.push(event.data);
                        }
                    };
                    
                    this.mediaRecorder.onstop = () => {
                        this.saveRecording(sessionId);
                    };
                    
                    this.mediaRecorder.start();
                    
                    this.updateStatus('Recording synchronized!', 'recording');
                    this.showRecordingInfo(sessionId);
                    this.startDurationTimer();
                    
                    // Auto-stop after 30 seconds (configurable)
                    setTimeout(() => {
                        this.stopRecording();
                    }, 30000);
                    
                } catch (error) {
                    console.error('Recording error:', error);
                    this.updateDeviceStatus('Recording failed: ' + error.message);
                }
            }
            
            stopRecording() {
                if (this.mediaRecorder && this.isRecording) {
                    this.mediaRecorder.stop();
                    this.isRecording = false;
                    this.updateStatus('Recording completed', 'connected');
                    this.hideRecordingInfo();
                    
                    if (this.durationInterval) {
                        clearInterval(this.durationInterval);
                    }
                }
            }
            
            saveRecording(sessionId) {
                if (this.recordedChunks.length === 0) return;
                
                const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                
                // Create download link
                const a = document.createElement('a');
                a.href = url;
                a.download = `${sessionId}_${this.deviceId}_${new Date().toISOString()}.webm`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                this.updateDeviceStatus('Video saved locally');
            }
            
            showRecordingInfo(sessionId) {
                const recordingInfo = document.getElementById('recordingInfo');
                recordingInfo.style.display = 'block';
                document.getElementById('sessionId').textContent = sessionId;
            }
            
            hideRecordingInfo() {
                document.getElementById('recordingInfo').style.display = 'none';
            }
            
            startDurationTimer() {
                this.durationInterval = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
                    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
                    const seconds = (elapsed % 60).toString().padStart(2, '0');
                    document.getElementById('recordingDuration').textContent = `${minutes}:${seconds}`;
                }, 1000);
            }
            
            syncTimeWithServer() {
                // Simple time sync check
                const start = Date.now();
                fetch('/admin')
                    .then(() => {
                        const rtt = Date.now() - start;
                        document.getElementById('timeSync').textContent = `RTT: ${rtt}ms`;
                    })
                    .catch(() => {
                        document.getElementById('timeSync').textContent = 'Sync failed';
                    });
            }
            
            updateDeviceInfo() {
                document.getElementById('deviceId').textContent = this.deviceId;
            }
            
            updateStatus(message, type) {
                const indicator = document.getElementById('statusIndicator');
                indicator.textContent = message;
                indicator.className = `status-indicator status-${type}`;
            }
            
            updateDeviceStatus(status) {
                document.getElementById('deviceStatus').textContent = status;
            }
        }
        
        // Initialize when page loads
        window.addEventListener('DOMContentLoaded', () => {
            new SynchronizedRecorder();
        });
    </script>
</body>
</html>
'''

# Enhanced Admin Dashboard
ENHANCED_ADMIN_DASHBOARD = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sync Recording Control Center</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        
        .control-panel {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .sync-button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 20px 40px;
            border-radius: 50px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            margin: 10px;
        }
        
        .sync-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(0,0,0,0.4);
        }
        
        .sync-button:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
        }
        
        .devices-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .device-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }
        
        .device-status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .status-connected { background: #28a745; }
        .status-recording { background: #dc3545; animation: pulse 1s infinite; }
        .status-waiting { background: #ffc107; color: #000; }
        
        .countdown-display {
            font-size: 3em;
            color: #ffd700;
            margin: 20px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .session-info {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 Synchronized Recording Control Center</h1>
            <p>Connected Devices: <span id="deviceCount">0</span>/4</p>
        </div>
        
        <div class="control-panel">
            <h2>📡 Sync Control</h2>
            <button id="syncRecordBtn" class="sync-button">
                🎯 START SYNCHRONIZED RECORDING
            </button>
            <div id="countdownDisplay" class="countdown-display" style="display: none;">
                3
            </div>
            <div class="session-info" id="sessionInfo" style="display: none;">
                <h3>📊 Active Session</h3>
                <p>Session ID: <span id="activeSessionId">-</span></p>
                <p>Devices Recording: <span id="recordingDevices">0</span></p>
            </div>
        </div>
        
        <div class="devices-grid" id="devicesGrid">
            <div class="device-card">
                <h3>📱 Waiting for devices...</h3>
                <p>Open the mobile client on each phone</p>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        class SyncController {
            constructor() {
                this.socket = null;
                this.connectedDevices = new Map();
                this.activeSession = null;
                
                this.init();
            }
            
            init() {
                this.setupSocket();
                this.setupEventListeners();
            }
            
            setupSocket() {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    console.log('Admin connected');
                    this.socket.emit('join_admin');
                });
                
                this.socket.on('device_connected', (data) => {
                    this.addDevice(data);
                });
                
                this.socket.on('connected_devices_update', (data) => {
                    this.updateDeviceCount(data.count);
                });
                
                this.socket.on('sync_command_sent', (data) => {
                    this.handleSyncCommandSent(data);
                });
            }
            
            setupEventListeners() {
                document.getElementById('syncRecordBtn').addEventListener('click', () => {
                    this.triggerSyncRecording();
                });
            }
            
            addDevice(data) {
                this.connectedDevices.set(data.device_id, {
                    id: data.device_id,
                    status: 'connected'
                });
                this.updateDevicesDisplay();
                this.updateDeviceCount(data.total_devices);
            }
            
            updateDevicesDisplay() {
                const grid = document.getElementById('devicesGrid');
                
                if (this.connectedDevices.size === 0) {
                    grid.innerHTML = `
                        <div class="device-card">
                            <h3>📱 Waiting for devices...</h3>
                            <p>Open the mobile client on each phone</p>
                        </div>
                    `;
                    return;
                }
                
                let html = '';
                this.connectedDevices.forEach((device) => {
                    html += `
                        <div class="device-card">
                            <h3>📱 ${device.id}</h3>
                            <div class="device-status status-${device.status}">
                                ${device.status.toUpperCase()}
                            </div>
                        </div>
                    `;
                });
                
                grid.innerHTML = html;
            }
            
            updateDeviceCount(count) {
                document.getElementById('deviceCount').textContent = count;
                
                const syncBtn = document.getElementById('syncRecordBtn');
                if (count === 0) {
                    syncBtn.disabled = true;
                    syncBtn.textContent = '⏳ WAITING FOR DEVICES';
                } else {
                    syncBtn.disabled = false;
                    syncBtn.textContent = `🎯 START SYNCHRONIZED RECORDING (${count} devices)`;
                }
            }
            
            triggerSyncRecording() {
                if (this.connectedDevices.size === 0) return;
                
                this.socket.emit('sync_record_command', {
                    timestamp: Date.now()
                });
            }
            
            handleSyncCommandSent(data) {
                console.log('Sync command sent:', data);
                
                // Show countdown
                this.showCountdown();
                
                // Update session info
                this.activeSession = data;
                this.updateSessionInfo(data);
                
                // Update device status
                this.connectedDevices.forEach((device, id) => {
                    device.status = 'recording';
                });
                this.updateDevicesDisplay();
            }
            
            showCountdown() {
                const countdownEl = document.getElementById('countdownDisplay');
                countdownEl.style.display = 'block';
                
                let count = 3;
                countdownEl.textContent = count;
                
                const interval = setInterval(() => {
                    count--;
                    if (count > 0) {
                        countdownEl.textContent = count;
                    } else {
                        countdownEl.textContent = 'RECORDING!';
                        setTimeout(() => {
                            countdownEl.style.display = 'none';
                        }, 1000);
                        clearInterval(interval);
                    }
                }, 1000);
            }
            
            updateSessionInfo(sessionData) {
                const sessionInfo = document.getElementById('sessionInfo');
                sessionInfo.style.display = 'block';
                
                document.getElementById('activeSessionId').textContent = sessionData.session_id;
                document.getElementById('recordingDevices').textContent = sessionData.device_count;
            }
        }
        
        // Initialize when page loads
        window.addEventListener('DOMContentLoaded', () => {
            new SyncController();
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🎬 Synchronized Video Recording System")
    print("=" * 50)
    print("📱 Mobile clients: http://YOUR_IP:5000")
    print("🖥️  Admin dashboard: http://localhost:5000/admin") 
    print("📁 Recordings saved locally on each device")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
import os
import time
import serial
import requests
import datetime
import re

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
FLASK_URL = "http://127.0.0.1:5000/upload_data"

DEVICE_ID_FILE = os.path.join(os.path.dirname(__file__), "device_id.txt")

def read_device_id():
    """Try to read the device_id from file; return int or None."""
    try:
        with open(DEVICE_ID_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None

device_id = read_device_id()
while device_id is None:
    print("⏳ Waiting for device_id.txt (create a sensor in the UI)...")
    time.sleep(3)
    device_id = read_device_id()

print(f"✅ Using device_id = {device_id}")

# open serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    print(f"✅ Connected to {SERIAL_PORT}")
except Exception as e:
    print(f"❌ Could not connect to {SERIAL_PORT}: {e}")
    raise

time.sleep(2)

last_mtime = os.path.getmtime(DEVICE_ID_FILE)

while True:
    try:
        try:
            mtime = os.path.getmtime(DEVICE_ID_FILE)
            if mtime != last_mtime:
                new_id = read_device_id()
                if new_id:
                    device_id = new_id
                    last_mtime = mtime
                    print(f"🔁 device_id changed → now {device_id}")
        except Exception:
            pass

        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue
        print("📥 Received:", line)

        # CSV preferred: "temp,hum,volt,ON"
        if ',' in line:
            parts = line.split(',')
            if len(parts) >= 4:
                temperature = float(parts[0])
                humidity    = float(parts[1])
                voltage     = float(parts[2])
                lights      = parts[3].strip().upper()
            else:
                print("⚠️ Invalid CSV format")
                continue
        else:
            # fallback parse
            match = re.search(r"Temperature:\s*([\d.]+).*Humidity:\s*([\d.]+).*Voltage:\s*([\d.]+).*Lights:\s*(ON|OFF)", line, re.I)
            if not match:
                print("⚠️ Invalid format")
                continue
            temperature = float(match.group(1))
            humidity    = float(match.group(2))
            voltage     = float(match.group(3))
            lights      = match.group(4).upper()

        hour = datetime.datetime.now().hour
        period = "Morning" if hour < 12 else "Afternoon" if hour < 18 else "Evening"

        payload = {
            "device_id": device_id,  
            "period": period,
            "temperature": temperature,
            "humidity": humidity,
            "voltage": voltage,
            "lights": lights
        }

        try:
            resp = requests.post(FLASK_URL, json=payload, timeout=5)
            print(f"➡️ Sent → {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Post failed: {e}. Retrying in 5s...")
            time.sleep(5)

    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(2)

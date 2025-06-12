# scanner.py
import asyncio
import time
import socket
import json
import paho.mqtt.client as mqtt
from bleak import BleakScanner

MQTT_BROKER = "192.168.0.101"
MQTT_PORT = 1883
MQTT_TOPIC = "neighbors/update"
HOSTNAME = socket.gethostname()

async def scan_ble():
    devices = await BleakScanner.discover()
    nearby = []
    for d in devices:
        nearby.append({
            "mac": d.address,
            "name": d.name or "Unknown",
            "rssi": d.rssi
        })
    return nearby

def choose_neighbors(devices):
    sorted_devs = sorted(devices, key=lambda x: x["rssi"], reverse=True)
    left = sorted_devs[0] if len(sorted_devs) > 0 else None
    right = sorted_devs[1] if len(sorted_devs) > 1 else None
    return left, right

def send_to_mqtt(left, right):
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    payload = {
        "station": HOSTNAME,
        "left_neighbor": left["mac"] if left else None,
        "right_neighbor": right["mac"] if right else None,
        "timestamp": time.time()
    }

    client.publish(MQTT_TOPIC, json.dumps(payload))
    client.disconnect()
    print(f"Enviado via MQTT: {json.dumps(payload, indent=2)}")

async def main_loop():
    while True:
        try:
            devices = await scan_ble()
            left, right = choose_neighbors(devices)
            send_to_mqtt(left, right)
        except Exception as e:
            print("Erro:", e)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main_loop())

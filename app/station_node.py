import asyncio
import json
import time
from typing import List
from bleak import BleakScanner, BLEDevice
import paho.mqtt.client as mqtt
from mqtt_config import BROKER_ADDRESS, BROKER_PORT

VERSION = "1.0.0"

class StationNode:
    def __init__(self, station_id: str, is_master: bool = False):
        self.station_id = station_id
        self.is_master = is_master
        self.known_master = station_id if is_master else None
        self.has_propagated_master = is_master
        self.neighbors: List[BLEDevice] = []
        self.client = mqtt.Client()
        self.client.on_message = self.on_message

    def start(self):
        self.client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
        self.client.subscribe("network/master")
        self.client.loop_start()

        if self.is_master:
            self.propagate_master_info()

        while True:
            self.scan_ble()
            self.advertise_ble_name()
            self.publish_neighbors()
            time.sleep(30)

    def scan_ble(self):
        print(f"[{self.station_id}] Scanning BLE devices...")
        self.neighbors = asyncio.run(BleakScanner.discover(timeout=10))
        if not self.known_master:
            for device in self.neighbors:
                if device.name and device.name.startswith("MASTER_"):
                    master_id = device.name.replace("MASTER_", "")
                    print(f"[{self.station_id}] Detected master: {master_id}")
                    self.known_master = master_id
                    break

    def advertise_ble_name(self):
        if self.is_master:
            advertise_name = f"MASTER_{self.station_id}"
        elif self.known_master:
            advertise_name = f"MASTER_{self.known_master}"
        else:
            advertise_name = f"NODE_{self.station_id}"
        print(f"[{self.station_id}] Simulating BLE advertising as: {advertise_name}")

    def publish_neighbors(self):
        if self.is_master or not self.known_master:
            return

        data = []
        for device in self.neighbors:
            if device.name:
                dist = self.estimate_distance(device.rssi)
                data.append({
                    "id": device.name,
                    "dist": dist,
                    "var": 0.05
                })

        payload = json.dumps({
            "from": self.station_id,
            "data": data
        })
        topic = f"station/{self.known_master}/neighbors"
        self.client.publish(topic, payload)
        print(f"[{self.station_id}] Sent neighbors to master {self.known_master}: {data}")

    def estimate_distance(self, rssi: float, tx_power: float = -59, n: float = 2.0) -> float:
        return round(10 ** ((tx_power - rssi) / (10 * n)), 2)

    def propagate_master_info(self):
        if not self.known_master:
            return
        payload = json.dumps({"master_id": self.known_master})
        self.client.publish("network/master", payload)
        print(f"[{self.station_id}] Propagated master info via MQTT: {self.known_master}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        if topic == "network/master":
            data = json.loads(payload)
            master_id = data.get("master_id")
            if not self.known_master:
                print(f"[{self.station_id}] Learned master via MQTT: {master_id}")
                self.known_master = master_id
                if not self.has_propagated_master:
                    self.propagate_master_info()
                    self.has_propagated_master = True

# Simulation block (not run automatically)
if __name__ == "__main__":
    # Replace station_id and is_master depending on the test
    node = StationNode(station_id="N1", is_master=True)  # example: master node
    node.start()

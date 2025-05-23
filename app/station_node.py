import asyncio
import json
import time
from typing import List
from bleak import BleakScanner, BLEDevice
import paho.mqtt.client as mqtt
from mqtt_config import BROKER_ADDRESS, BROKER_PORT, TOPICS

VERSION = "1.0.0"  # Versão do software da estação

class StationNode:
    def __init__(self, station_id: str, ip: str, is_master: bool = False):
        self.station_id = station_id
        self.ip = ip
        self.is_master = is_master
        self.neighbors: List[BLEDevice] = []
        self.client = mqtt.Client()
        self.client.on_message = self.on_message

    def start(self):
        self.client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

        # Subscrições relevantes
        self.client.subscribe("topology/positions")
        self.client.subscribe("topology/graph")
        self.client.subscribe(f"station/{self.station_id}/update")

        self.client.loop_start()

        while True:
            self.scan_ble()
            self.publish_identity()
            self.publish_version()
            self.publish_neighbors()
            time.sleep(30)

    def scan_ble(self):
        print(f"[{self.station_id}] Scanning BLE devices...")
        self.neighbors = asyncio.run(BleakScanner.discover(timeout=10))

    def publish_identity(self):
        payload = json.dumps({"id": self.station_id, "is_master": self.is_master})
        topic = TOPICS["IS_MASTER"].format(id=self.station_id)
        self.client.publish(topic, payload)

    def publish_version(self):
        payload = json.dumps({"id": self.station_id, "version": VERSION})
        topic = TOPICS["VERSION"].format(id=self.station_id)
        self.client.publish(topic, payload)

    def estimate_distance(self, rssi: float, tx_power: float = -59, n: float = 2.0) -> float:
        return round(10 ** ((tx_power - rssi) / (10 * n)), 2)

    def publish_neighbors(self):
        data = []
        for device in self.neighbors:
            if device.name:
                dist = self.estimate_distance(device.rssi)
                data.append({
                    "id": device.name,
                    "dist": dist,
                    "var": 0.05  # valor fixo para agora
                })

        payload = json.dumps(data)
        topic = TOPICS["NEIGHBORS"].format(id=self.station_id)
        self.client.publish(topic, payload)
        print(f"[{self.station_id}] Published neighbors: {data}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"[{self.station_id}] Received on {topic}: {payload}")

        if topic == f"station/{self.station_id}/update":
            self.handle_update(payload)

        elif topic == "topology/positions":
            self.handle_topology_positions(payload)

        elif topic == "topology/graph":
            self.handle_topology_graph(payload)

    def handle_update(self, payload):
        print(f"[{self.station_id}]  UPDATE NEEDED: {payload}")
        # update script todo

    def handle_topology_positions(self, payload):
        try:
            pos_data = json.loads(payload)
            print(f"[{self.station_id}]  New positions: {pos_data.get(self.station_id, 'not found')}")
        except Exception as e:
            print(f"[{self.station_id}] Error decoding topology positions: {e}")

    def handle_topology_graph(self, payload):
        try:
            graph_data = json.loads(payload)
            print(f"[{self.station_id}]  Neighbors in graph: {graph_data.get(self.station_id, [])}")
        except Exception as e:
            print(f"[{self.station_id}] Error decoding graph: {e}")


if __name__ == "__main__":
    # Troque os parâmetros conforme cada estação
    node = StationNode(station_id="N1", ip="192.168.1.10", is_master=False)
    node.start()

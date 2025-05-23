import json
import time
import threading
import paho.mqtt.client as mqtt
from mqtt_config import BROKER_ADDRESS, BROKER_PORT, TOPICS
from things import solve_point_positions_and_graph

class MasterNode:
    def __init__(self):
        self.measurements_raw = {}  # id -> list of {id, dist, var}
        self.versions = {}          # id -> version
        self.detected_masters = set()

        self.client = mqtt.Client()
        self.client.on_message = self.on_message

        self.lock = threading.Lock()

    def start(self):
        self.client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

        self.client.subscribe("station/+/neighbors")
        self.client.subscribe("station/+/version")
        self.client.subscribe("station/+/is_master")

        self.client.loop_start()

        # Loop de verificação e reconstrução
        while True:
            time.sleep(60)
            self.verify_masters()
            self.verify_versions()
            self.reconstruct_topology()

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        try:
            if topic.endswith("/neighbors"):
                station_id = topic.split("/")[1]
                self.handle_neighbors(station_id, payload)
            elif topic.endswith("/version"):
                self.handle_version(payload)
            elif topic.endswith("/is_master"):
                self.handle_is_master(payload)
        except Exception as e:
            print(f"[MASTER] Erro ao processar mensagem: {e}")

    def handle_neighbors(self, station_id, payload):
        data = json.loads(payload)
        with self.lock:
            self.measurements_raw[station_id] = data
        print(f"[MASTER] Vizinhos de {station_id}: {data}")

    def handle_version(self, payload):
        data = json.loads(payload)
        node_id = data["id"]
        version = data["version"]
        with self.lock:
            self.versions[node_id] = version
        print(f"[MASTER] Versão de {node_id}: {version}")

    def handle_is_master(self, payload):
        data = json.loads(payload)
        if data["is_master"]:
            self.detected_masters.add(data["id"])

    def verify_masters(self):
        print(f"[MASTER] Mestres detectados: {self.detected_masters}")
        if len(self.detected_masters) > 1:
            print("[MASTER]  Mais de um mestre detectado! Conflito.")

    def verify_versions(self):
        latest_version = max(self.versions.values(), default=None)
        for node_id, version in self.versions.items():
            if version != latest_version:
                update_payload = json.dumps({
                    "required_version": latest_version,
                    "your_version": version
                })
                topic = TOPICS["UPDATE_CMD"].format(id=node_id)
                self.client.publish(topic, update_payload)
                print(f"[MASTER]  Pedido de atualização enviado para {node_id}")

    def reconstruct_topology(self):
        with self.lock:
            # Montar input no formato de things.py
            input_structure = []
            for src_id, neighbor_list in self.measurements_raw.items():
                edges = []
                for entry in neighbor_list:
                    edges.append((entry["id"], entry["dist"], entry["var"]))
                input_structure.append((src_id, edges))

        if not input_structure:
            print("[MASTER] Nenhuma medição para reconstruir topologia.")
            return

        print("[MASTER] Recalculando topologia...")
        positions, graph = solve_point_positions_and_graph(input_structure, visualize=False)

        self.client.publish(TOPICS["TOPOLOGY_POS"], json.dumps(positions))
        self.client.publish(TOPICS["TOPOLOGY_GRAPH"], json.dumps(graph))
        print(f"[MASTER]  Topologia publicada com {len(positions)} posições.")


if __name__ == "__main__":
    master = MasterNode()
    master.start()

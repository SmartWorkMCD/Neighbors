# listener.py
import json
import paho.mqtt.client as mqtt

MQTT_BROKER = "192.168.0.101"
MQTT_PORT = 1883
MQTT_TOPIC = "neighbors/update"
CACHE_FILE = "neighbors_cache.json"
neighbors = {}

def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker MQTT")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global neighbors
    try:
        payload = json.loads(msg.payload.decode())
        station = payload.get("station")
        neighbors[station] = {
            "left": payload.get("left_neighbor"),
            "right": payload.get("right_neighbor")
        }
        print(f"Atualizado {station}:", neighbors[station])

        with open(CACHE_FILE, "w") as f:
            json.dump(neighbors, f, indent=2)

    except Exception as e:
        print("Erro ao processar mensagem:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()

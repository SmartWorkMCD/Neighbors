# mqtt_config.py
import dotenv
import os
dotenv.load_dotenv()

BROKER_ADDRESS = os.getenv("BROKER_IP", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", 1883))
IM_MASTER = os.getenv("IM_MASTER", "False").lower() == "true"

TOPICS = {
    "IS_MASTER": "station/{id}/is_master",  
    "NEIGHBORS": "station/{id}/neighbors",
    "VERSION": "station/{id}/version",
    "TOPOLOGY_POS": "topology/positions",
    "TOPOLOGY_GRAPH": "topology/graph",
    "UPDATE_CMD": "station/{id}/update"
}

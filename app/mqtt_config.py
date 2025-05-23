# mqtt_config.py

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883

TOPICS = {
    "IS_MASTER": "station/{id}/is_master",  
    "NEIGHBORS": "station/{id}/neighbors",
    "VERSION": "station/{id}/version",
    "TOPOLOGY_POS": "topology/positions",
    "TOPOLOGY_GRAPH": "topology/graph",
    "UPDATE_CMD": "station/{id}/update"
}

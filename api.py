# api.py
from flask import Flask, jsonify
import json
import os

app = Flask(__name__)
CACHE_FILE = "neighbors_cache.json"

def load_neighbors():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

@app.route("/neighbors/<station>", methods=["GET"])
def get_neighbors(station):
    data = load_neighbors()
    if station in data:
        return jsonify({
            "station": station,
            "left": data[station].get("left"),
            "right": data[station].get("right")
        })
    else:
        return jsonify({"error": "Estação não encontrada"}), 404

@app.route("/neighbors", methods=["GET"])
def get_all():
    return jsonify(load_neighbors())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

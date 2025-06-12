
# pip install streamlit paho-mqtt networkx matplotlib

import json
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import threading
import time

# --- Configurações
BROKER = "localhost"  # altere para o IP do broker se estiver em outro dispositivo
PORT = 1883

TOPIC_POS = "topology/positions"
TOPIC_GRAPH = "topology/graph"

positions = {}
edges = {}

# --- Funções MQTT
def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(TOPIC_POS)
    client.subscribe(TOPIC_GRAPH)

def on_message(client, userdata, msg):
    global positions, edges
    if msg.topic == TOPIC_POS:
        try:
            positions.update(json.loads(msg.payload.decode()))
        except:
            pass
    elif msg.topic == TOPIC_GRAPH:
        try:
            edges.update(json.loads(msg.payload.decode()))
        except:
            pass

def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

# --- Inicializa o cliente MQTT em thread separada
threading.Thread(target=mqtt_thread, daemon=True).start()

# --- Interface Streamlit
st.title("BLE Network Topology")
st.markdown("Este painel mostra a topologia atual estimada a partir das distâncias BLE.")

with st.spinner("Aguardando dados MQTT..."):
    time.sleep(1)

# --- Atualização dinâmica
while True:
    st.subheader("Posições dos Nós")
    st.json(positions)

    st.subheader("Ligações (grafo)")
    st.json(edges)

    if positions and edges:
        G = nx.Graph()
        for node, pos in positions.items():
            G.add_node(node, pos=tuple(pos))

        for node, neighbors in edges.items():
            for neighbor in neighbors:
                if G.has_edge(node, neighbor) or node == neighbor:
                    continue
                G.add_edge(node, neighbor)

        pos_dict = nx.get_node_attributes(G, 'pos')

        fig, ax = plt.subplots(figsize=(6, 6))
        nx.draw(G, pos=pos_dict, with_labels=True, node_color='skyblue',
                node_size=1000, font_weight='bold', ax=ax)
        st.pyplot(fig)

    st.info("Este painel atualiza automaticamente a cada 10 segundos.")
    time.sleep(10)
    st.experimental_rerun()

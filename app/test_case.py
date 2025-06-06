
from things import solve_point_positions_and_graph

print("==== Simulação Completa ====")

# Simulação: N1 é o mestre
master_id = "N1"
print(f" N1 inicia como mestre: {master_id}")

# Etapa 1: nós descobrem o mestre via BLE
nodes = {
    "N2": {"known_master": None},
    "N3": {"known_master": None},
    "N4": {"known_master": None},
}

print("\n--- Etapa 1: Descoberta do mestre via BLE ---")
for node_id in nodes:
    print(f"{node_id} escaneou e encontrou advertising MASTER_{master_id}")
    nodes[node_id]["known_master"] = master_id

# Etapa 2: cada nó envia sua tabela de vizinhos via MQTT para o mestre
print("\n--- Etapa 2: Envio das tabelas via MQTT para o mestre ---")
ble_tables = {
    "N2": [('N1', 10.2, 0.1), ('N3', 10.0, 0.1)],
    "N3": [('N2', 10.0, 0.1), ('N4', 7.1, 0.05)],
    "N4": [('N3', 7.1, 0.05)],
}

simulated_input = []
for sender, table in ble_tables.items():
    print(f"{sender} envia para {master_id}: {table}")
    simulated_input.append((sender, table))

# Etapa 3: mestre reconstrói topologia
print("\n--- Etapa 3: Mestre calcula topologia ---")
positions, graph = solve_point_positions_and_graph(simulated_input, visualize=True)

print("\nPosições calculadas:")
for k, v in positions.items():
    print(f"{k}: {v}")

print("\nGrafo de conectividade:")
for k, v in graph.items():
    print(f"{k} <--> {v}")

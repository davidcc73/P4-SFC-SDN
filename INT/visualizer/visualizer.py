import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from influxdb import InfluxDBClient
import sys
from datetime import datetime, timedelta
import random

# Configurações do InfluxDB
host = 'localhost'
database = "int"

# Conexão ao InfluxDB
influx_client = InfluxDBClient(host=host, database=database)
if influx_client.ping():  # Verificar se a conexão é bem-sucedida
    print("Connected to InfluxDB successfully.") 
else:
    print("Failed to connect to InfluxDB")
    sys.exit(1)

# Lista de cores para serem usadas
colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']

# Dicionário para armazenar cores para cada fluxo
path_colors = {}

# Dicionário para armazenar índices das arestas para cada fluxo
edge_flow_indices = {}

# Dicionário para armazenar IDs para cada fluxo
flow_ids = {}

# Variável para rastrear o próximo ID disponível
next_flow_id = 1

# Função para atribuir uma cor a um fluxo
def assign_color(flow_identifier):
    if flow_identifier not in path_colors:
        if len(colors) > 0:
            path_colors[flow_identifier] = colors.pop(0)
        else:
            # Se as cores predefinidas acabarem, gerar uma cor aleatória
            path_colors[flow_identifier] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    return path_colors[flow_identifier]

# Função para atribuir um ID a um fluxo
def assign_flow_id(flow_identifier):
    global next_flow_id
    if flow_identifier not in flow_ids:
        flow_ids[flow_identifier] = next_flow_id
        next_flow_id += 1
    return flow_ids[flow_identifier]

# Função para atualizar o gráfico
def update_graph(G, new_data, edge_update_time):
    unique_flows = set()
    
    for point in new_data:
        flow_label = point['flow_label']
        src_ip = point['src_ip']
        dst_ip = point['dst_ip']
        
        flow_identifier = f"{flow_label}_{src_ip}_{dst_ip}"  # Create a unique identifier for each flow
        unique_flows.add(flow_identifier)
    
    for flow_identifier in unique_flows:
        flow_label, src_ip, dst_ip = flow_identifier.split('_')
        
        flow_color = assign_color(flow_identifier)  # Assign a color to the flow
        flow_id = assign_flow_id(flow_identifier)   # Assign an ID to the flow
        
        print("\nFlow ID:", flow_id, "Label:", flow_label, "Source IP:", src_ip, "Destination IP:", dst_ip, "Color:", flow_color)
        
        # Find paths for the specific flow
        paths = [point['path'] for point in new_data if point['flow_label'] == flow_label and point['src_ip'] == src_ip and point['dst_ip'] == dst_ip]
        
        # Reset the edge indices for this flow
        edge_flow_indices[flow_identifier] = {}
        
        for path in paths:
            switches = path.split('-')
            
            for i in range(len(switches) - 1):
                egress_switch_id = int(switches[i])
                ingress_switch_id = int(switches[i + 1])
                edge = (egress_switch_id, ingress_switch_id, flow_identifier)  # Include flow identifier in the edge
                
                if edge not in edge_colors:
                    edge_colors[edge] = flow_color
                if flow_identifier not in edge_flow_indices:
                    edge_flow_indices[flow_identifier] = {}
                if edge not in edge_flow_indices[flow_identifier]:
                    edge_flow_indices[flow_identifier][edge] = len(edge_flow_indices[flow_identifier]) + 1  # Assign a unique index per flow
                # print('Edge:', edge, 'Index:', edge_flow_indices[flow_identifier][edge])
                edge_update_time[edge] = datetime.now()  # Update the last update time

# Função para visualizar o gráfico
def visualize_graph(G, edge_colors, edge_flow_indices):
    plt.clf()  # Clear the current figure

    # Draw all nodes
    nx.draw_networkx_nodes(G, pos, node_size=400, edgecolors="black")

    # Draw all edges in light gray
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color="lightgray", style="dashed", connectionstyle="arc3,rad=0.0")

    # Draw edges with assigned colors
    edge_labels = {}
    max_rad = 0.33  # Maximum arc radius for edge labels
    for i, (edge, color) in enumerate(edge_colors.items()):
        egress_switch_id, ingress_switch_id, flow_identifier = edge
        rad = (i % 10) * 0.05 - max_rad  # Adjust arc radius for each edge with a slightly larger range
        
        nx.draw_networkx_edges(
            G, pos, edgelist=[(egress_switch_id, ingress_switch_id)], 
            edge_color=color, arrows=True, 
            connectionstyle=f"arc3,rad={rad}"
        )
        
        if flow_identifier in edge_flow_indices and edge in edge_flow_indices[flow_identifier]:
            flow_index = edge_flow_indices[flow_identifier][edge]  # Get the flow-specific index for the edge
            edge_labels[(egress_switch_id, ingress_switch_id, rad)] = (flow_index, color)  # Store index and color

    # Add labels to nodes
    nx.draw_networkx_labels(G, pos, font_size=13, font_family="sans-serif")

    # Add labels to edges
    for (egress_switch_id, ingress_switch_id, rad), (label, flow_color) in edge_labels.items():
        label_pos = (
            pos[egress_switch_id][0] * 0.75 + pos[ingress_switch_id][0] * 0.25, 
            pos[egress_switch_id][1] * 0.75 + pos[ingress_switch_id][1] * 0.25 + rad * 0.2
        )
        plt.text(label_pos[0], label_pos[1], label, fontsize=10, color=flow_color, ha='center', va='center')

    # Create a legend for flows
    legend_elements = []
    for flow_identifier, color in path_colors.items():
            flow_label, src_ip, dst_ip = flow_identifier.split('_')
            flow_id = flow_ids[flow_identifier]  # Get the assigned ID for this flow
            legend_label = f"Flow {flow_id}:({src_ip} -> {dst_ip}) Label {flow_label}"
            legend_elements.append(Patch(facecolor=color, edgecolor='black', label=legend_label))

    # Adjust figure layout to accommodate the legend on the left
    plt.subplots_adjust(left=0.23, right=0.98)
    # Add the legend to the plot
    plt.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(-0.3, 0.5), fontsize='small')

    # Set the title of the plot
    plt.title("Network Topology Visualizer in Real-Time")
    plt.pause(0.5)  # Pause for 0.5 seconds




# Inicialização do gráfico
G = nx.MultiDiGraph()
G.add_nodes_from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
G.add_edges_from([
    (1, 4), (1, 9), (2, 3), (2, 14), (9, 4), (9, 10), (9, 13), (9, 14), (14, 10), (14, 3), (14, 13), 
    (4, 5), (4, 10), (3, 13), (3, 6), (10, 5), (10, 11), (10, 12), (10, 13), (13, 11), (13, 12), (13, 6),
    (5, 8), (5, 11), (6, 7), (6, 12), (11, 12), (11, 8), (12, 7), (8, 7), (4, 1), (9, 1), (3, 2), (14, 2), 
    (4, 9), (10, 9), (13, 9), (14, 9), (10, 14), (3, 14), (13, 14), (5, 4), (10, 4), (13, 3), (6, 3), (5, 10), 
    (11, 10), (12, 10), (13, 10), (11, 13), (12, 13), (6, 13), (8, 5), (11, 5), (7, 6), (12, 6), (12, 11), 
    (8, 11), (7, 12), (7, 8)
])

edge_colors = {}
edge_update_time = {edge: datetime.min for edge in G.edges()}  # Inicializa o tempo da última atualização com datetime.min

pos = {
    1: (0, 3), 9: (2, 3), 14: (4, 3), 2: (6, 3), 
    4: (0, 2), 10: (2, 2), 13: (4, 2), 3: (6, 2),
    5: (0, 1), 11: (2, 1), 12: (4, 1), 6: (6, 1),
    8: (1, 0), 7: (5, 0)}

# Criar figura para o gráfico sem trazer para frente
plt.figure(figsize=(12, 8))
plt.ion()  # Turn on interactive mode

# Simulação de leitura contínua de dados
while True:
    query = 'SELECT path, flow_label, src_ip, dst_ip from "flow_stats" WHERE time > now() - 1s'
    result = influx_client.query(query)
    points = result.get_points()
    new_data = list(points)

    if new_data:
        update_graph(G, new_data, edge_update_time)
    
    current_time = datetime.now()
    for edge in list(edge_update_time.keys()):
        if (current_time - edge_update_time[edge]) > timedelta(seconds=0.1):
            edge_colors.pop(edge, None)  # Remove the edge color if not updated in the last 2 seconds

    visualize_graph(G, edge_colors, edge_flow_indices)
    print('\n-= Graph updated at:', datetime.now(), '=-')

# Garantir que todos os gráficos sejam exibidos no final
plt.ioff()
plt.show()

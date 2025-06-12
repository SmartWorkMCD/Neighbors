import numpy as np
import collections
import matplotlib.pyplot as plt 


def order_t(id1,id2):
    return (id1,id2) if id1<id2 else (id2,id1)

def parse_input_data(raw_data: list[tuple[str, list[tuple[str, float, float]]]]):
    """
    Parses the raw input data into usable structures.

    Args:
        raw_data: List of tuples, e.g.,
                  [('A', [('B', 1, 0.1), ('C', 2, 0.15)]),
                   ('B', [('A', 0.95, 0.1), ('C', 2, 0.15)])]

    Returns:
        A tuple containing:
        - point_ids_list (list): Sorted list of unique point IDs.
        - id_to_idx (dict): Mapping from point ID to integer index.
        - idx_to_id (dict): Mapping from integer index to point ID.
        - measurements (dict): {(idx1, idx2): (avg_distance, avg_variance)}
                               for unique pairs of point indices.
    """
    all_point_ids = set()
    temp_measurements = collections.defaultdict(list)

    for source_id, connections in raw_data:
        all_point_ids.add(source_id)
        for target_id, dist, var in connections:
            all_point_ids.add(target_id)
            
            pair_key = order_t(source_id, target_id)
            temp_measurements[pair_key].append((dist, var))

    point_ids_list = sorted(list(all_point_ids))
    if len(point_ids_list) == 0:
        return [], {}, {}, {}
        
    id_to_idx = {pid: i for i, pid in enumerate(point_ids_list)}
    idx_to_id = {i: pid for i, pid in enumerate(point_ids_list)}

    measurements = {}
    for (p_id1, p_id2), data_list in temp_measurements.items():
        
        avg_dist = np.mean([d for d, _ in data_list])
        avg_var = np.mean([v for _, v in data_list])
        
        idx1, idx2 = id_to_idx[p_id1], id_to_idx[p_id2]
        measurements[tuple(sorted((idx1, idx2)))] = (avg_dist, avg_var)
        
    return point_ids_list, id_to_idx, idx_to_id, measurements

def weigth(dist_need,distance,variance):
    return dist_need #/ (variance+1) / (distance+1)

def step(points,distances,variances,step_size):
    # new_points = np.zeros(points.shape)
    avg_weight = 0
    nn = 0
    for i in range(2,points.shape[0]):
        point = points[i]
        
        attraction = np.zeros(2)
        for j in range(points.shape[0]):
            if i == j:
                continue
            dist = distances[i,j]
            if dist == 0:
                continue
            other_point = points[j]
            diff_p = other_point - point
            
            cur_dist = np.linalg.norm(diff_p)
            
            dist_need = cur_dist - dist
            
            attraction += (other_point - point) * weigth(dist_need,dist,variances[i,j])
            if weigth(dist_need,dist,variances[i,j]) > 1000:
                print(f"Warning: large weight {weigth(dist_need,dist,variances[i,j])}")
            avg_weight += abs(weigth(dist_need,dist,variances[i,j]))
            nn += 1
        points[i] = point + step_size * attraction
        
    return points , avg_weight / nn if nn > 0 else 0
def calculate_positions(point_ids_list, idx_to_id, measurements):
    num_total_points = len(point_ids_list)
    
    if num_total_points == 0:
        return {}
    
    dist_mat = np.zeros((num_total_points, num_total_points))
    var_mat = np.zeros((num_total_points, num_total_points))
    
    for (idx1, idx2), (dist, var) in measurements.items():
        dist_mat[idx1, idx2] = dist
        dist_mat[idx2, idx1] = dist
        var_mat[idx1, idx2] = var
        var_mat[idx2, idx1] = var
        
    avg_dist = np.mean(dist_mat)
    points = np.random.rand(num_total_points, 2) * avg_dist
    
    points[0] = np.array([0,0])
    if num_total_points > 1:
        d = measurements[(0,1)][0]
        points[1] = np.array([d,0])

    lr = 0.01
    prev_weight = 1e9
    for i in range(500):
        print(f"Iteration {i} , learning rate {lr} , weight {prev_weight}")
        points , avg_weight = step(points,dist_mat,var_mat,lr)
        if avg_weight < 1e-6:
            break
        if avg_weight > prev_weight*1.01:
            lr /= 3
        elif avg_weight < prev_weight:
            lr *= 1.1
        prev_weight = avg_weight
        
    
    results = {}
    for i in range(num_total_points):
        results[idx_to_id[i]] = points[i]
    
    return results

def build_graph(positions_dict):
    point_ids = list(positions_dict.keys())
    num_points = len(point_ids)

    if num_points < 2:
        return {pid: [] for pid in point_ids}

    coords_list = [np.array(positions_dict[pid]) for pid in point_ids]
    
    unique_edges = set()

    for i in range(num_points):
        p1_id = point_ids[i]
        p1_coord = coords_list[i]
        
        distances_to_others = []
        for j in range(num_points):
            if i == j:
                continue
            p2_id = point_ids[j]
            p2_coord = coords_list[j]
            dist = np.linalg.norm(p1_coord - p2_coord)
            distances_to_others.append((dist, p2_id))
        
        distances_to_others.sort() 

        for k in range(min(2, len(distances_to_others))):
            neighbor_id = distances_to_others[k][1]
            edge = frozenset({p1_id, neighbor_id})
            unique_edges.add(edge)

    adj_list = collections.defaultdict(list)
    for edge in unique_edges:
        u, v = list(edge) 
        adj_list[u].append(v)
        adj_list[v].append(u)
        
    for pid in point_ids: # Ensure all points are keys
        if pid not in adj_list:
            adj_list[pid] = []
            
    return dict(adj_list)


def visualize_graph(positions_dict, graph_adj_list, title="Point Configuration and Graph"):
    """
    Visualizes the points and their connections.
    """
    if not positions_dict:
        print("No positions to visualize.")
        return

    plt.figure(figsize=(8, 8))
    
    # Plot points
    point_ids = list(positions_dict.keys())
    x_coords = [positions_dict[pid][0] for pid in point_ids]
    y_coords = [positions_dict[pid][1] for pid in point_ids]
    
    plt.scatter(x_coords, y_coords, s=100, zorder=5) # s is size, zorder to draw points on top of lines
    
    # Annotate points
    for pid, (x, y) in positions_dict.items():
        plt.text(x + 0.05, y + 0.05, str(pid), fontsize=9)
        
    # Plot edges
    plotted_edges = set()
    for point_id, neighbors in graph_adj_list.items():
        p1_coord = positions_dict[point_id]
        for neighbor_id in neighbors:
            edge = frozenset({point_id, neighbor_id})
            if edge not in plotted_edges:
                p2_coord = positions_dict[neighbor_id]
                plt.plot([p1_coord[0], p2_coord[0]], 
                         [p1_coord[1], p2_coord[1]], 
                         'b-', alpha=0.6, zorder=1) # blue line with some transparency
                plotted_edges.add(edge)
                
    plt.title(title)
    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.axis('equal') # Ensure X and Y axes have the same scale
    plt.show()

# --- Main program flow ---
def solve_point_positions_and_graph(input_structure, visualize=False): # Added visualize flag
    """
    Main function to calculate positions, build the graph, and optionally visualize.
    """
    point_ids_list, id_to_idx, idx_to_id, measurements = parse_input_data(input_structure)
    
    if not point_ids_list:
        print("No points found in input.")
        return {}, {}

    # print(f"Point IDs: {point_ids_list}")
    # print(f"ID to Index mapping: {id_to_idx}") # Can be verbose
    # print(f"Measurements (by index): {measurements}") # Can be verbose

    absolute_positions = calculate_positions(point_ids_list, idx_to_id, measurements)
    
    print(f"\nCalculated Positions: {absolute_positions}")
    
    connectivity_graph = build_graph(absolute_positions)
    
    print(f"\nConnectivity Graph (2 closest neighbors): {connectivity_graph}")
    
    if visualize:
        try:
            visualize_graph(absolute_positions, connectivity_graph)
        except ImportError:
            print("\nMatplotlib not installed. Skipping visualization.")
        except Exception as e:
            print(f"\nError during visualization: {e}")

    return absolute_positions, connectivity_graph

# --- Example Usage ---
if __name__ == '__main__':
    example_input = [
        ('A', [('B', 1.0, 0.01), ('C', 2.0, 0.05), ('D', 1.5, 0.02)]),
        ('B', [('A', 1.05, 0.015), ('C', 1.2, 0.03), ('E', 2.5, 0.1)]),
        ('C', [('A', 1.95, 0.04), ('B', 1.15, 0.025)]),
        ('D', [('A', 1.55, 0.025), ('E', 1.0, 0.01)]),
        ('E', [('B', 2.4, 0.09), ('D', 0.95, 0.015)])
    ]
    
    example_input_2 = [
        ('N1', [('N2', 10.0, 0.1), ('N3', 14.14, 0.2)]),
        ('N2', [('N1', 10.2, 0.1), ('N3', 10.0, 0.1)]),
        ('N3', [('N1', 13.9, 0.15), ('N2', 9.8, 0.12), ('N4', 7.07, 0.1)]),
        ('N4', [('N3', 7.0, 0.1)])
    ]
    example_input_minimal = [('P1', [('P2', 5.0, 0.01)])]
    example_input_single = [('S1', [])]
    example_input_three_collinear = [
        ('X', [('Y', 1.0, 0.01)]),
        ('Y', [('X', 1.0, 0.01), ('Z', 1.0, 0.01)]),
        ('Z', [('Y', 1.0, 0.01), ('X', 1.0, 0.01)])
    ]

    print("--- Running Example 1 ---")
    solve_point_positions_and_graph(example_input, visualize=True)
    
    print("\n--- Running Example 2 (more complex) ---")
    solve_point_positions_and_graph(example_input_2, visualize=True)

    print("\n--- Running Minimal Example (2 points) ---")
    solve_point_positions_and_graph(example_input_minimal, visualize=True)
    
    print("\n--- Running Single Point Example ---")
    solve_point_positions_and_graph(example_input_single, visualize=True) # Will show one point

    print("\n--- Running Three Collinear Points Example ---")
    solve_point_positions_and_graph(example_input_three_collinear, visualize=True)
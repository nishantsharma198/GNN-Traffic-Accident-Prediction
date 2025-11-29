import networkx as nx
import osmnx as ox
import random
import time
import json

# --- GLOBAL CACHE AND CONFIGURATION ---
G_DELHI = None
PLACE_NAME = "New Delhi, India"
random.seed(42) 

def get_and_prepare_graph():
    """
    Downloads the graph once and assigns a simulated 'predicted_accident_risk' score.
    """
    global G_DELHI
    if G_DELHI is not None:
        return G_DELHI

    print(f"Server: Downloading and preparing graph for {PLACE_NAME} (5km radius)...")
    try:
        center_lat, center_lon = 28.61, 77.21 
        G = ox.graph_from_point((center_lat, center_lon), dist=5000, network_type="drive", simplify=True)
    except Exception as e:
        print(f"Server Error: OSMnx failed to download graph: {e}")
        return None

    # --- SIMULATE GNN PREDICTION: Assign 'predicted_accident_risk' ---
    for u, v, k, data in G.edges(keys=True, data=True):
        base_risk = random.uniform(0.1, 1.5) 
        highway_type = data.get('highway', 'unclassified')
        if isinstance(highway_type, list): highway_type = highway_type[0]

        if 'motorway' in highway_type or 'trunk' in highway_type:
            risk_multiplier = 4.0 
        elif 'residential' in highway_type or 'service' in highway_type:
            risk_multiplier = 1.5
        else:
            risk_multiplier = 2.5
            
        final_risk = round(base_risk * risk_multiplier, 4)
        data['predicted_accident_risk'] = final_risk
        if 'length' not in data: data['length'] = 100.0

    G_DELHI = G
    print("Server: Graph prepared and cached successfully.")
    return G

def get_dynamic_route_prediction(orig_lat, orig_lon, dest_lat, dest_lon):
    """Finds the shortest path minimizing accident risk and returns the score and geometry."""
    G = get_and_prepare_graph()
    if G is None:
        return {"status": "Graph Error", "total_predicted_accidents": 0.0, "node_count": 0, "route_geometry": []}

    try:
        orig_node = ox.nearest_nodes(G, orig_lon, orig_lat)
        dest_node = ox.nearest_nodes(G, dest_lon, dest_lat)

        route = nx.shortest_path(G, orig_node, dest_node, weight='predicted_accident_risk')
    except nx.NetworkXNoPath:
        return {"status": "No Path Found", "total_predicted_accidents": 0.0, "node_count": 0, "route_geometry": []}
    except Exception:
        return {"status": "Pathfinding Error", "total_predicted_accidents": 0.0, "node_count": 0, "route_geometry": []}
    
    cumulative_risk = 0.0
    route_coords = []
    
    for u, v in zip(route[:-1], route[1:]):
        edge_data = G.get_edge_data(u, v)
        min_risk = float('inf')
        
        if G.nodes[u]: route_coords.append([G.nodes[u]['y'], G.nodes[u]['x']])
        
        for k in edge_data:
            risk = edge_data[k].get('predicted_accident_risk', float('inf'))
            if risk < min_risk: min_risk = risk
        
        cumulative_risk += min_risk
    
    if route and G.nodes[route[-1]]: route_coords.append([G.nodes[route[-1]]['y'], G.nodes[route[-1]]['x']])

    return {
        "status": "Success", 
        "total_predicted_accidents": round(cumulative_risk, 2), 
        "node_count": len(route),
        "route_geometry": route_coords
    }

# Load the graph once when the server starts up
get_and_prepare_graph()
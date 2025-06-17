import pandas as pd
import networkx as nx
from itertools import combinations
from pyvis.network import Network
from terminal_style import sprint, spinner


"""
This script shows how the D. characters are connected through their affiliations:
In the networ, two characters are joined if they share an affiliation.
For every pair of D. characters, the program find and print the shortest chain of characters linking them.
"""

spinner("Generating network of D....", color="pink", bold=True)

# Load and clean data
df_characters = pd.read_csv("data/dataframes/df_final_onepiece.csv")

# Drop rows with missing names or affiliations
df_characters = df_characters.dropna(subset=["name", "affiliations"]).copy()
df_characters["name"] = df_characters["name"].astype(str)
df_characters["affiliations"] = df_characters["affiliations"].astype(str)


# Split affiliations and explode
df_characters["affiliations"] = df_characters["affiliations"].str.split(";")
df_exploded = df_characters.explode("affiliations")
df_exploded["affiliations"] = df_exploded["affiliations"].str.strip()
df_exploded = df_exploded[df_exploded["affiliations"] != "clanofd."]


# Build graph of characters connected by shared affiliations
G = nx.Graph()
shared_affiliations = {}  # Keep track of shared affiliations between characters

# First add all characters as nodes
for name, group in df_exploded.groupby("name"):
    G.add_node(name, type="character", has_D=group["has_D"].iloc[0])

# Then connect characters who share affiliations
for aff, chars in df_exploded.groupby("affiliations")["name"]:
    # Get all pairs of characters with this affiliation
    chars = chars.unique()
    for c1, c2 in combinations(chars, 2):
        if G.has_edge(c1, c2):
            # If edge exists, append this affiliation to the list
            shared_affiliations[(c1, c2)].append(aff)
        else:
            # Create new edge with this affiliation
            G.add_edge(c1, c2)
            shared_affiliations[(c1, c2)] = [aff]

# Add shared affiliations to edge tooltips
for (c1, c2), affs in shared_affiliations.items():
    G[c1][c2]['title'] = f"Shared affiliations: {', '.join(affs)}"

key_df = df_exploded[df_exploded["has_D"] == 1.0]
key_characters = key_df["name"].unique().tolist()

# Compute shortest paths
shortest_paths = {}
for c1, c2 in combinations(key_characters, 2):
    try:
        path = nx.shortest_path(G, source=c1, target=c2)
        shortest_paths[(c1, c2)] = path
    except nx.NetworkXNoPath:
        pass

# Subgraph with all shortest path nodes
nodes_to_include = set()
for path in shortest_paths.values():
    nodes_to_include.update(path)

subG = G.subgraph(nodes_to_include).copy()


# Visualization

key_nodes = [n for n, d in subG.nodes(data=True) if d.get("has_D") == 1.0]
intermediate_nodes = [n for n, d in subG.nodes(data=True) if not d.get("has_D") == 1.0]

net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white')
net.from_nx(subG)
net.heading = "One Piece Network — D. Characters : shortest path to link each other"

for node in net.nodes:
    node_data = subG.nodes[node['id']]
    if node_data.get('has_D') == 1.0:
        # D. characters
        node['color'] = '#ff9999'  
        node['size'] = 30  # Bigger size for D. characters
        node['title'] = f"D. Character: {node['id']}"
    else:
        # Other characters
        node['color'] = '#99ccff'  
        node['size'] = 15
        node['title'] = f"Character: {node['id']}"

for edge in net.edges:
    source_has_d = subG.nodes[edge['from']].get('has_D') == 1.0
    target_has_d = subG.nodes[edge['to']].get('has_D') == 1.0
    
    if source_has_d and target_has_d:
        edge['color'] = {'color': '#ff6666', 'opacity': 0.8}  #  D.-D. connections
        edge['width'] = 3
    elif source_has_d or target_has_d:
        edge['color'] = {'color': "#66ccff", 'opacity': 0.4}  # D.-normal connections
        edge['width'] = 2
    else:
        edge['color'] = {'color': '#666666', 'opacity': 0.3}  # normal-normal connections
        edge['width'] = 1


net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=150)
net.show("will_of_d/results/network_of_d.html", notebook=False)

sprint("Network generated and saved as network_of_d.html", color="green", bold= True)

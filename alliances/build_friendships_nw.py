import pandas as pd
import networkx as nx
import itertools
import numpy as np
from terminal_style import sprint, spinner
from pyvis.network import Network
from typing import Dict, List
from collections import defaultdict
from networkx.algorithms.community import greedy_modularity_communities

df_matrix = pd.read_csv("data/dataframes/character_appearances_matrix.csv", index_col=0)

spinner("Generating friendships network...", color="pink", bold=True)

co_matrix = df_matrix.dot(df_matrix.T)
character_to_friends: Dict[str, List[str]] = defaultdict(list)  # ex: {'Luffy': ['Zoro', 'Nami']}
friend_to_characters: Dict[str, List[str]] = defaultdict(list)

for index, record in co_matrix.iterrows():
    character = index
    total_appearances = co_matrix.loc[character, character]  # Diagonal value = total appearances of the character
    if total_appearances >= 25:
        threshold = 0.85 * total_appearances  # Set threshold to 80% of total appearances
        friends = record[record >= threshold].index.tolist()  
        for friend in friends:
            if friend != character:  # Avoid self-references
                character_to_friends[character].append(friend)
                friend_to_characters[friend].append(character)
            

# --- Only keep friendships that share members ---
G = nx.Graph()

# Only process characters with multiple friendships
for character, friends in character_to_friends.items():
    if not G.has_node(character):
        G.add_node(character)

EDGE_WEIGHT = 0.25
# --- Add weighted edges between friends ---
for char, friends in character_to_friends.items():
    for u, v in itertools.combinations(friends, 2):
        if G.has_edge(u, v):
            G[u][v]['weight'] += EDGE_WEIGHT
        else:
            G.add_edge(u, v, weight=1)

edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] == EDGE_WEIGHT]
G.remove_edges_from(edges_to_remove)

# Remove nodes with no connections
G.remove_nodes_from(list(nx.isolates(G)))

# Set node sizes based on number of connections 
for node in G.nodes():
    connections = G.degree(node)
    friends_count = len(character_to_friends[node])
    G.nodes[node]['size'] = connections if connections != 1 else connections *1.8   
    G.nodes[node]['title'] = f"{node} ({friends_count} friends : {character_to_friends[node]})"
    
# --- Community detection ---
# Identify communities
communities = list(greedy_modularity_communities(G, resolution=1))

# Build a mapping from node to community index
group_map = {}
for community_id, community in enumerate(communities):
    for node in community:
        group_map[node] = community_id

# Assign the 'group' attribute on each node
for node in G.nodes():
    G.nodes[node]['group'] = group_map.get(node, 0)

# Add transparency to edges
for u, v in G.edges():
    G[u][v]['color'] = {'opacity': 0.4}

# --- PyVis visualization ---
net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white')
net.from_nx(G)
net.heading = "One Piece Friendship network"
net.force_atlas_2based()
net.show("alliances/results/friendship_network.html", notebook=False)

sprint("Network generated and saved as friendship_network.html", color="green", bold= True)




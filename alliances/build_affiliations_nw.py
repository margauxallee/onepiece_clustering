import pandas as pd
import networkx as nx
import itertools
import numpy as np
from terminal_style import sprint, spinner
from pyvis.network import Network
from typing import Dict, List
from collections import defaultdict
from networkx.algorithms.community import greedy_modularity_communities


spinner("Generating affiliations network...", color="pink", bold=True)

df_alliances = pd.read_csv('data/dataframes/df_final_onepiece.csv')
df_alliances = df_alliances[['affiliations', 'name']]
df_alliances = (df_alliances
    .dropna(subset=['name','affiliations'])
    .assign(affiliations=lambda d: d['affiliations'].str.split(';'))
    .explode('affiliations')
)

# --- Collect all affiliations per character ---
# Initialize mappings using defaultdict for automatic list initialization
names_to_affiliations: Dict[str, List[str]] = defaultdict(list)  # ex: {'Luffy': ['Straw Hat Pirates', 'Revolutionary Army']}
temp_affiliations_to_names: Dict[str, List[str]] = defaultdict(list)  # Temporary mapping for affiliations to names
# Loop through each row in the df
for index, record in df_alliances[['name', 'affiliations']].iterrows():
    character = record['name']
    affiliation = record['affiliations']  

    names_to_affiliations[character].append(affiliation)
    temp_affiliations_to_names[affiliation].append(character)


# --- Only keep affiliations that share members ---
G = nx.Graph()
affiliation_to_names = defaultdict(list)

# Only process characters with multiple affiliations
for name, affs in names_to_affiliations.items():
    if len(affs) > 1:  # This character has more than 1 affiliation so it creates connections
        for aff in affs:
            if aff not in affiliation_to_names:
                affiliation_to_names[aff] = temp_affiliations_to_names[aff]
            if not G.has_node(aff):
                G.add_node(aff)


# --- Add weighted edges ---
shared_chars = {}  # Keep track of shared characters between affiliations
for name, affs in names_to_affiliations.items():
    if len(affs) > 1:
        for u, v in itertools.combinations(affs, 2):
            if (u, v) not in shared_chars:
                shared_chars[(u, v)] = set()
            shared_chars[(u, v)].add(name)
            if G.has_edge(u, v):
                G[u][v]['weight'] += 1
            else:
                G.add_edge(u, v, weight=1)

# Add shared characters to edge tooltips
for (u, v), chars in shared_chars.items():
    G[u][v]['title'] = f"{len(chars)} members shared: {', '.join(chars)}"


# --- Node sizes / tooltips based on affiliation_to_names ---
for aff, chars in affiliation_to_names.items():
    node_size = len(chars)/(1.25 if len(chars) > 1 else 1)  # Scale down size for the affiliations with one member only
    G.nodes[aff]['size'] = node_size
    G.nodes[aff]['title'] = f"{aff} ({len(chars)} members)"

# ---- Prune edges of weight 1 (otherwise to many edges) ---
for u, v, d in list(G.edges(data=True)):
    if d['weight'] < 2:
        G.remove_edge(u, v)

# Remove nodes with no connections
G.remove_nodes_from(list(nx.isolates(G)))

# --- Community detection ---

# Identify communities
communities = list(greedy_modularity_communities(G))

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
net.heading = "One Piece Alliances Network"
net.force_atlas_2based()
net.show("alliances/results/alliances_network.html", notebook=False)

sprint("Network generated and saved as alliances_network.html", color="green", bold= True)




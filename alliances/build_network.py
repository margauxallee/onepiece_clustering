import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from netgraph import Graph
import itertools
import numpy as np
from terminal_style import sprint, spinner, style
import matplotlib.colors as mcolors
from pyvis.network import Network
import seaborn as sns


spinner("Generating affiliations network...", color="blue", bold=True)

df = pd.read_csv('data/dataframes/df_final_onepiece.csv')
df = df[['affiliations', 'key']]
df= (df
    .dropna(subset=['key','affiliations'])
    .rename(columns={'key': 'name'})
    .assign(affiliations=lambda d: d['affiliations'].str.split(';'))
    .explode('affiliations')
)

# --- Collect all affiliations per character ---
names_map = {}         # character → [aff1, aff2, …]
temp_affiliation_map = {}   # temporary map to count members

for _, row in df.iterrows():
    name = row['name']
    aff = row['affiliations']
    names_map.setdefault(name, []).append(aff)
    temp_affiliation_map.setdefault(aff, []).append(name)

# --- Only keep affiliations that share members ---
G = nx.Graph()
affiliation_map = {}   # final map with only connected affiliations

# Only process characters with multiple affiliations
for name, affs in names_map.items():
    if len(affs) > 1:  # This character creates connections
        for aff in affs:
            if aff not in affiliation_map:
                affiliation_map[aff] = temp_affiliation_map[aff]
            if not G.has_node(aff):
                G.add_node(aff)


# --- Add weighted edges ---
import itertools
shared_chars = {}  # Keep track of shared characters between affiliations
for name, affs in names_map.items():
    if len(affs) > 1:
        for u, v in itertools.combinations(affs, 2):
            if (u, v) not in shared_chars:
                shared_chars[(u, v)] = set()
            shared_chars[(u, v)].add(name)
            if G.has_edge(u, v):
                G[u][v]['weight'] += 1
            else:
                G.add_edge(u, v, weight=1, title=f"{name} ({len(shared_chars[(u, v)])} members shared)")

# Add shared characters to edge tooltips
for (u, v), chars in shared_chars.items():
    G[u][v]['title'] = f"{len(chars)} members shared: {', '.join(chars)}"


# --- Set node sizes & tooltips based on affiliation_map ---
for aff, chars in affiliation_map.items():
    cnt = len(chars)/(1.25 if len(chars) > 1 else 1)  # Scale down size for single-member affiliations
    G.nodes[aff]['size'] = cnt
    G.nodes[aff]['title'] = f"{aff} ({len(chars)} members)"

# ---- prune edges of weight 1 to declutter ---
for u, v, d in list(G.edges(data=True)):
    if d['weight'] < 2:
        G.remove_edge(u, v)

# --- Community detection ---
from networkx.algorithms.community import greedy_modularity_communities
comms = list(greedy_modularity_communities(G))
group = {n: cid for cid, comm in enumerate(comms) for n in comm}
for n in G.nodes():
    G.nodes[n]['group'] = group.get(n, 0)

# Add transparency to edges
for u, v in G.edges():
    G[u][v]['color'] = {'opacity': 0.5}

# --- PyVis visualization ---
net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white')
net.from_nx(G)

# stabilize then disable physics for instant render
net.force_atlas_2based()
#net.show("alliances/results/alliances_network.html", notebook=False)

sprint("Network generated and saved as alliances_network.html", color="green", bold= True)




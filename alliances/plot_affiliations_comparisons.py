import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict
from typing import Dict, List
import itertools


# === SAME PROCESSING AS IN build_network.py ===
df_alliances = pd.read_csv('data/dataframes/df_final_onepiece.csv')
df_alliances = df_alliances[['affiliations', 'name']]
df_alliances = (df_alliances
    .dropna(subset=['name','affiliations'])
    .assign(affiliations=lambda d: d['affiliations'].str.split(';'))
    .explode('affiliations')
)
# Collect all affiliations per character

names_to_affiliations: Dict[str, List[str]] = defaultdict(list)  
temp_affiliations_to_names: Dict[str, List[str]] = defaultdict(list) 
for index, record in df_alliances[['name', 'affiliations']].iterrows():
    character = record['name']
    affiliation = record['affiliations']  

    names_to_affiliations[character].append(affiliation)
    temp_affiliations_to_names[affiliation].append(character)

#  Only keep affiliations that share members 
G = nx.Graph()
affiliations_to_names = defaultdict(list)

# Only process characters with multiple affiliations
for name, affs in names_to_affiliations.items():
    if len(affs) > 1:  
        for aff in affs:
            if aff not in affiliations_to_names:
                affiliations_to_names[aff] = temp_affiliations_to_names[aff]
            if not G.has_node(aff):
                G.add_node(aff)

for name, affs in names_to_affiliations.items():
    for u, v in itertools.combinations(affs, 2):
        if G.has_edge(u, v):
            G[u][v]['weight'] += 1
        else:
            G.add_edge(u, v, weight=1)


# ========= CREATE THE DFs ============
 # DataFrame for members
df_members = pd.DataFrame([
    {'affiliation': aff, 'members': len(chars)}
    for aff, chars in affiliations_to_names.items()
])

# Dataframe for connections
df_connections = pd.DataFrame()
rows = []
for node in G.nodes():
    rows.append({'affiliation': node, 'connections': G.degree(node)})
df_connections = pd.DataFrame(rows)

# DataFrame for allied members
df_allies = pd.DataFrame()
rows = []
for aff in G.nodes():
    own_count = len(affiliations_to_names.get(aff, []))
    allied_count = sum(
        len(affiliations_to_names.get(neighbor, []))
        for neighbor in G.neighbors(aff)
    )
    rows.append({
        'affiliation': aff,
        'total_allied_members': own_count + allied_count
    })
df_allies = pd.DataFrame(rows)

TOP_AFFILIATIONS = 10

df_members = df_members.sort_values(by='members', ascending=False).head(TOP_AFFILIATIONS).set_index('affiliation')
df_connections = df_connections.sort_values(by='connections', ascending=False).head(TOP_AFFILIATIONS).set_index('affiliation')
df_allies = df_allies.sort_values(by='total_allied_members', ascending=False).head(TOP_AFFILIATIONS).set_index('affiliation')

# Define pastel colors for each plot
pastel_colors = ["#56BDE3", '#FFB347', '#77DD77'] 

datasets = [
    (df_members['members'], '#Members', f'Top {TOP_AFFILIATIONS} by Members'),
    (df_connections['connections'], '#Connections', f'Top {TOP_AFFILIATIONS} by Connections'),
    (df_allies['total_allied_members'], '#Allies', f'Top {TOP_AFFILIATIONS} by Allies')
]

target = 'strawhatpirates'

for (values, xlabel, title), base_color in zip(datasets, pastel_colors):
    labels = values.index.tolist()
    colors = ['darkred' if lbl == target else base_color for lbl in labels]

    plt.figure(figsize=(10, 6))
    bars = plt.barh(labels, values,
                    color=colors, edgecolor=colors,
                    linewidth=10, joinstyle='round', height=0.6)
    plt.bar_label(bars, label_type='edge', padding=-15,
                  fontsize=10, color='white', weight='bold')

    plt.xlabel(xlabel)
    plt.ylabel('Affiliation')
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

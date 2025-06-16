import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from terminal_style import sprint, spinner, style
import matplotlib.colors as mcolors
import seaborn as sns



df = pd.read_csv('data/dataframes/df_final_onepiece.csv')
df = df[['affiliations', 'key']]
df= (df
    .dropna(subset=['key','affiliations'])
    .rename(columns={'key': 'name'})
    .assign(affiliations=lambda d: d['affiliations'].str.split(';'))
    .explode('affiliations')
)

names_map = {}     
temp_affiliation_map = {}  

for _, row in df.iterrows():
    name = row['name']
    aff = row['affiliations']
    names_map.setdefault(name, []).append(aff)
    temp_affiliation_map.setdefault(aff, []).append(name)

# Only keep affiliations that share members
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


# ========= CREATE THE DFs ============

df_members = pd.DataFrame([
    {'affiliation': aff, 'members': len(chars)}
    for aff, chars in affiliation_map.items()
])

df_connections = pd.DataFrame([
    {'affiliation': node, 'connections': G.degree(node)}
    for node in G.nodes()
])

df_allies = pd.DataFrame([{
    'affiliation': aff,
    'total_allied_members': len(affiliation_map[aff]) + sum(
        len(affiliation_map[neighbor]) 
        for neighbor in G.neighbors(aff)
    )
} for aff in G.nodes()])

# PLOT 
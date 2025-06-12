import pandas as pd
import networkx as nx
from itertools import combinations
from pyvis.network import Network

df = pd.read_csv('data_extraction/df_final_onepiece.csv')
df = df.dropna(subset=['name', 'affiliations']).copy()
df['name'] = df['name'].astype(str)
df['affiliations'] = df['affiliations'].str.split(';')

# exploding affiliations to create all the pairs
df_exp = df.explode('affiliations')
df_exp = df_exp.dropna(subset=['affiliations'])

# building the graph
G = nx.Graph()
G.add_nodes_from(df['name'])
for aff, grp in df_exp.groupby('affiliations'):
    names = [str(n) for n in grp['name']]
    for u, v in combinations(names, 2):
        G.add_edge(u, v, affiliation=aff)

# Visualisation 
net = Network(height='750px', width='100%', notebook=False)
for node, deg in G.degree():
    net.add_node(node, label=node, title=f"Degree: {deg}", value=deg)
for u, v, data in G.edges(data=True):
    net.add_edge(u, v, title=data.get('affiliation', ''))

net.show_buttons(filter_=['physics'])
net.show('results/onepiece_network.html', notebook=False)

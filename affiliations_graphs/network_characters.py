import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from pyvis.network import Network
from networkx.drawing.nx_agraph import graphviz_layout
from terminal_style import sprint, spinner


spinner("Generating filtered & community‐colored characters network...", color="blue")


df = pd.read_csv('data_extraction/df_final_onepiece.csv')
df = df.dropna(subset=['name', 'affiliations']).copy()
df_exp = (
    df
    .assign(affiliation = df['affiliations'].str.split(';'))          
    .explode('affiliation')              
)
df_exp['affiliation'] = df_exp['affiliation'].str.strip()
df_exp = df_exp.drop_duplicates(['name', 'affiliation'])
pairs = (
    df_exp
    .merge(df_exp, on='affiliation', suffixes=('_1', '_2'))
)

pairs = pairs[(pairs['name_1'] < pairs['name_2'])]

result = pairs[['name_1', 'name_2', 'affiliation']].rename(
    columns={'name_1': 'name1', 'name_2': 'name2'}
).reset_index(drop=True)


edge_weights = (
    result
    .groupby(['name1','name2'])
    .size()
    .reset_index(name='weight')
)

G = nx.from_pandas_edgelist(
    edge_weights,
    source='name1',
    target='name2',
    edge_attr='weight',
    create_using=nx.Graph()
)
# Remove self-loops
G.remove_edges_from(nx.selfloop_edges(G))



# nécessite pygraphviz ou pydot + graphviz installé
pos = graphviz_layout(G, prog="dot")  # ou 'sfdp', 'neato', etc.

nx.draw(G, pos,
        with_labels=True,
        node_size=50,
        arrowsize=5,
        font_size=6)

net = Network(height="750px", width="100%", directed=True)
net.from_nx(G)
net.show("graph_characters.html", notebook=False)

sprint("Characters network generated !", color="green", bold=True)



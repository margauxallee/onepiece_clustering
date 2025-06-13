

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from pyvis.network import Network
from networkx.drawing.nx_pydot import graphviz_layout
from networkx.drawing.nx_agraph import graphviz_layout
from terminal_style import sprint, spinner

spinner("Generating affiliations network...", color="blue", bold=True)


# Load and preprocess data
df = pd.read_csv('data_extraction/df_final_onepiece.csv')
df = df.dropna(subset=['name', 'affiliations']).copy()
df["affiliations"] = df["affiliations"].str.split(";")
df = df.explode("affiliations")
df["affiliations"] = df["affiliations"].str.strip()
df = df.dropna(subset=["affiliations"])


# Build weighted graph
G = nx.from_pandas_edgelist(
    df,
    source="name",
    target="affiliations",
    create_using=nx.DiGraph()
)
# Remove self-loops
G.remove_edges_from(nx.selfloop_edges(G))

pos = graphviz_layout(G, prog="dot")  

nx.draw(G, pos,
        with_labels=True,
        node_size=50,
        arrowsize=5,
        font_size=6)

net = Network(height="750px", width="100%", directed=True)
net.from_nx(G)
net.show("graph.html", notebook=False)

sprint("Affiliations network generated !", color="green", bold=True)



import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
import seaborn as sns


# Load and clean data
df = pd.read_csv("data_extraction/df_final_onepiece.csv")

# Drop rows with missing names or affiliations
df = df.dropna(subset=["name", "affiliations"]).copy()
df["name"] = df["name"].astype(str)
df["affiliations"] = df["affiliations"].astype(str)


# Split affiliations and explode
df["affiliations"] = df["affiliations"].str.split(";")
df_exploded = df.explode("affiliations")
df_exploded["affiliations"] = df_exploded["affiliations"].str.strip()
df_exploded = df_exploded[df_exploded["affiliations"] != "clanofd."]


# Build graph
G = nx.Graph()

for _, row in df_exploded.iterrows():
    char = row["name"]
    aff = row["affiliations"]
    G.add_node(char, type="character", has_D=row["has_D"])
    G.add_node(aff, type="affiliation")
    G.add_edge(char, aff)


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

sns.set_theme(style="white")
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "white"
plt.rcParams["axes.linewidth"] = 0.1

palette = sns.color_palette("Set2")

color_key = palette[0]       
color_inter = palette[1]     
color_aff = palette[2]      

plt.figure(figsize=(22, 16))
pos = nx.spring_layout(subG, seed=42, k=0.35, iterations=200)

# Categorize nodes
key_nodes = [n for n, d in subG.nodes(data=True) if d.get("has_D") == 1.0]
intermediate_nodes = [n for n, d in subG.nodes(data=True)
                      if d.get("type") == "character" and d.get("has_D") != 1.0]
aff_nodes = [n for n, d in subG.nodes(data=True) if d.get("type") == "affiliation"]

# Draw nodes with soft edges
nx.draw_networkx_nodes(subG, pos, nodelist=key_nodes, node_color=color_key,
                       node_size=1200, edgecolors="gray", linewidths=1.2, label="Key Characters")
nx.draw_networkx_nodes(subG, pos, nodelist=intermediate_nodes, node_color=color_inter,
                       node_size=600, edgecolors="gray", linewidths=1, label="Intermediate Characters")
nx.draw_networkx_nodes(subG, pos, nodelist=aff_nodes, node_color=color_aff,
                       node_size=400, edgecolors="gray", linewidths=1, label="Affiliations")

nx.draw_networkx_edges(subG, pos, alpha=0.25, width=1, edge_color="gray")

char_labels = {n: n for n in key_nodes + intermediate_nodes}
nx.draw_networkx_labels(subG, pos, labels=char_labels, font_size=10, font_weight="medium")

aff_labels = {n: n for n in aff_nodes}
nx.draw_networkx_labels(subG, pos, labels=aff_labels, font_size=6, font_color="dimgray")

plt.title("One Piece Network — D. Characters and their connections", fontsize=20, fontweight="bold", pad=30)
plt.legend(loc="upper right", fontsize=11, frameon=True, fancybox=True, edgecolor="lightgray")
plt.axis("off")
plt.tight_layout()
plt.show()

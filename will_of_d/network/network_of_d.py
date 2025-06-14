import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
import seaborn as sns
import numpy as np


"""
This script shows how the D. characters are connected through their affiliations:
It build a network where any two characters are joined if they share an affiliation.
For every pair of D. characters, the program find and print the shortest chain of characters linking them.
You can see the resulting network just by running the code, with D. characters and intermediates highlighted in different colors.
"""

# Load and clean data
df_characters = pd.read_csv("data_extraction/df_final_onepiece.csv")

# Drop rows with missing names or affiliations
df_characters = df_characters.dropna(subset=["name", "affiliations"]).copy()
df_characters["name"] = df_characters["name"].astype(str)
df_characters["affiliations"] = df_characters["affiliations"].astype(str)


# Split affiliations and explode
df_characters["affiliations"] = df_characters["affiliations"].str.split(";")
df_exploded = df_characters.explode("affiliations")
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

# Use optimized spring layout for best visualization
pos = nx.spring_layout(
    subG,
    k=3,           # Increase spacing between nodes
    iterations=50, # More iterations for better convergence
    seed=42       # For reproducible layout
)

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

# Categorize edges
key_to_key = [(u, v) for (u, v) in subG.edges() if u in key_nodes and v in key_nodes]
key_to_aff = [(u, v) for (u, v) in subG.edges() if 
              (u in key_nodes and v in aff_nodes) or (v in key_nodes and u in aff_nodes)]
other_edges = [(u, v) for (u, v) in subG.edges() if 
               (u, v) not in key_to_key and (u, v) not in key_to_aff]

# Draw edges with different styles based on connection type
nx.draw_networkx_edges(subG, pos, 
                      edgelist=key_to_key,
                      edge_color='darkred',
                      alpha=0.4,
                      width=2,
                      connectionstyle="arc3,rad=0.3")

nx.draw_networkx_edges(subG, pos, 
                      edgelist=key_to_aff,
                      edge_color='darkblue',
                      alpha=0.3,
                      width=1.5,
                      connectionstyle="arc3,rad=0.2")

nx.draw_networkx_edges(subG, pos, 
                      edgelist=other_edges,
                      edge_color='gray',
                      alpha=0.15,
                      width=1,
                      connectionstyle="arc3,rad=0.1")

# Add labels with improved visibility
char_labels = {n: n for n in key_nodes + intermediate_nodes}
nx.draw_networkx_labels(subG, pos, labels=char_labels, 
                       font_size=10, 
                       font_weight="bold",
                       bbox=dict(facecolor='white', 
                               alpha=0.7, 
                               edgecolor='none', 
                               pad=0.5))

aff_labels = {n: n for n in aff_nodes}
nx.draw_networkx_labels(subG, pos, labels=aff_labels, 
                       font_size=6, 
                       font_color="dimgray",
                       bbox=dict(facecolor='white', 
                               alpha=0.5, 
                               edgecolor='none', 
                               pad=0.3))

plt.title("One Piece Network — D. Characters and their connections", 
          fontsize=20, fontweight="bold", pad=30)

# Create legend elements
node_legend_elements = [
    plt.scatter([], [], c=[color_key], s=1200, label='Key Characters', 
               edgecolors='gray', linewidths=1.2),
    plt.scatter([], [], c=[color_inter], s=600, label='Intermediate Characters',
               edgecolors='gray', linewidths=1),
    plt.scatter([], [], c=[color_aff], s=400, label='Affiliations',
               edgecolors='gray', linewidths=1)
]

# Create custom legend for edge types
edge_legend_elements = [
    plt.Line2D([0], [0], color='darkred', linestyle='-', lw=2,
               label='D. Character Connections'),
    plt.Line2D([0], [0], color='darkblue', linestyle='-', lw=1.5,
               label='D. Character-Affiliation'),
    plt.Line2D([0], [0], color='gray', linestyle='-', lw=1,
               label='Other Connections')
]

# Combine all legend elements
plt.legend(handles=node_legend_elements + edge_legend_elements,
          loc="upper right", 
          fontsize=11, 
          frameon=True, 
          fancybox=True, 
          edgecolor="lightgray")

plt.axis("off")
plt.tight_layout()
plt.show()

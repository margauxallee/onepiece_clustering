# One Piece - Characters networks

![alt text](image.png)

## Overview
The One Piece world is amazing. But it's also huge : with over 1500 characters, it can become overwhelming. This project builds networks based on shared crews, organizations, or even alliances to find patterns and make the world easier to understand, helping fans to better visualize the One Piece world.


## Getting Started

### 🛠️ Data extraction and creation

I used the [Crawl4AI](https://docs.crawl4ai.com/) framework to automate the extraction of structured data from the One Piece Fandom Wiki.

1. **Character list extraction**  
   I targeted the [List of Canon Characters](https://onepiece.fandom.com/wiki/List_of_Canon_Characters) page using a custom CSS schema to extract character names and their profile URLs. For each character URL, I navigated to their dedicated wiki page and extracted infobox attributes such as affiliations, occupations, origin, and more.

2. **Data Processing**  
   The raw crawled data is processed using custom cleaning functions in `data_processing.py`:


3. **Character Appearances**  
   Using episode data from Not David (famous Youtube channel), I created a co-occurrence matrix to track which characters appear together in episodes.

## Analysis 

### 🔍 Network Analysis

The project includes three main types of network analysis:

1. **Affiliations Network** (`build_affiliations_nw.py`)
   - Nodes represent organizations/crews
   - Edges connect organizations that share members
   - Community detection to identify related groups

2. **Friendship Network** (`build_friendships_nw.py`)
   - Nodes represent characters
   - Edges connect characters who frequently appear together
   - Uses 80% co-occurrence threshold based on character's total appearances
   - Community detection to identify groups

3. **Comparative Analysis** (`plot_affiliations_comparisons.py`)
   - Analyzes top affiliations by different metrics:
     - Number of members
     - Number of connections to other groups
     - Total allied members (direct + connected)

### 📊 Visualization

All networks are visualized using PyVis, creating interactive HTML files with:
- Node sizing based on importance
- Community-based coloring
- Tooltips showing detailed information

The visualizations can be found in the `alliances/results/` directory:
- `alliances_network.html`: Shows organization connections
- `friendship_network.html`: Shows characters relationships

### 🧬 Will of D Analysis - IN PROGRESS

A special analysis focusing on the will of D. is implemented in the `will_of_d/` directory:
- Network analysis of D. characters and their connections
- Prediction model for potential D. characters based on character attributes

## Requirements

The project dependencies are listed in `requirements.txt`. Main libraries used:
- NetworkX for graph operations
- PyVis for network visualization
- Pandas for data manipulation
- NumPy for numerical operations



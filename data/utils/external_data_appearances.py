import pickle
import pandas as pd
import numpy as np
from pathlib import Path

def process_appearance_data(file_path):
    """
    Process the pickle file containing character appearances and create a matrix.
    Returns a DataFrame where:
    - Rows are characters
    - Columns are episode numbers
    - Values are 1 if character appears in episode, 0 otherwise
    """
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    
    appearances = {}
    max_episode = 0
    
    # Process each character's appearances
    for character, episodes in data.items():
        appearances[character] = episodes
        if episodes:  
            max_episode = max(max_episode, max(episodes))
    
    # Create a DataFrame with all episodes from 1 to max_episode
    episode_range = range(1, max_episode + 1)
    appearance_matrix = pd.DataFrame(0, 
                                   index=appearances.keys(),
                                   columns=[f'episode_{i}' for i in episode_range])
    
    # Fill the matrix with appearances
    for character, episodes in appearances.items():
        for episode in episodes: 
            col = f'episode_{int(episode)}'
            if col in appearance_matrix.columns:
                appearance_matrix.loc[character, col] = 1
    
    return appearance_matrix

if __name__ == "__main__":
    # Path to the pickle file
    FILE_PATH = 'data/dataframes/onepiece_characterapperencedictionary.pkl'
    
    # Create the appearance matrix
    appearance_matrix = process_appearance_data(FILE_PATH)
    
    # Basic information about the matrix
    print("\n=== Appearance Matrix Info ===")
    print(f"Number of characters: {len(appearance_matrix)}")
    print(f"Number of episodes: {len(appearance_matrix.columns)}")
    print("\nFirst few rows of the matrix:")
    print(appearance_matrix.head())
    
    # Save the matrix to CSV for further use
    OUTPUT_PATH =  'data/dataframes/character_appearances_matrix.csv'
    appearance_matrix.to_csv(OUTPUT_PATH)
    print(f"\nMatrix saved to: {OUTPUT_PATH}")


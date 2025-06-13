#!/usr/bin/env python3
"""
onepiece_clustering.py

Pipeline for unsupervised clustering of One Piece characters,
highlighting the “Has_D” holders via distinctive markers.

Features:
 - Top-N one-hot encoded affiliations
 - Top-N one-hot encoded occupations
 - One-hot encoded origin
 - Three haki columns (observation, armament, conqueror)
 - Standardization + PCA (retain 90% variance)
 - KMeans clustering with silhouette-based k selection
 - 2D PCA scatter plot with Has_D holders marked

Usage:
    python onepiece_clustering.py \
      --csv data_extraction/df_final_onepiece.csv \
      --min_occ 10 \
      --variance 0.90 \
      --k_min 2 --k_max 10
"""

import argparse
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt


def load_and_clean(path: str) -> pd.DataFrame:
    """Load CSV and parse list columns."""
    df = pd.read_csv(path)
    df = df.dropna(subset=['name']).copy()
    # parse semicolon-separated lists
    for col in ['affiliations', 'occupations']:
        df[col] = (
            df[col]
              .fillna('')
              .astype(str)
              .str.split(';')
              .apply(lambda lst: [x.strip() for x in lst if x.strip()])
        )
    # ensure haki columns exist
    haki_cols = ['haki.observation', 'haki.armament', 'haki.conqueror']
    for col in haki_cols:
        if col not in df.columns:
            df[col] = 0
    return df


def top_one_hot(df: pd.DataFrame, col: str, min_occ: int = 10) -> pd.DataFrame:
    """
    Return a DataFrame of one-hot columns for values in df[col] that occur >= min_occ.
    df[col] should be lists of strings.
    """
    # flatten list and count
    all_vals = pd.Series([v for lst in df[col] for v in lst])
    top_vals = all_vals.value_counts()[lambda s: s >= min_occ].index.tolist()
    # build one-hot flags
    mat = {
        val: df[col].apply(lambda lst, v=val: int(v in lst))
        for val in top_vals
    }
    return pd.DataFrame(mat, index=df.index)


def build_feature_matrix(df: pd.DataFrame,
                         min_occ_aff: int,
                         min_occ_occ: int) -> pd.DataFrame:
    """Assemble the full feature matrix."""
    # affiliations & occupations
    X_aff = top_one_hot(df, 'affiliations', min_occ_aff)
    X_occ = top_one_hot(df, 'occupations', min_occ_occ)
    # origin one-hot (group rare into 'Other' if desired)
    X_orig = pd.get_dummies(df['origin'].fillna('Unknown'), prefix='origin')
    # haki columns
    haki_cols = ['haki.observation', 'haki.armament', 'haki.conqueror']
    X_haki = df[haki_cols].fillna(0).astype(float)
    # concatenate
    X = pd.concat([X_aff, X_occ, X_orig, X_haki], axis=1).fillna(0)
    return X


def reduce_dimensionality(X: np.ndarray,
                          variance_threshold: float = 0.90) -> (np.ndarray, PCA):
    """
    Standardize and reduce X via PCA to retain given variance_threshold.
    Returns (X_pca, fitted PCA object).
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    pca = PCA(n_components=variance_threshold, svd_solver='full')
    X_pca = pca.fit_transform(X_scaled)
    print(f"[PCA] retained {pca.n_components_} components "
          f"({variance_threshold*100:.0f}% variance)")
    return X_pca, pca


def select_best_k(X: np.ndarray,
                  k_min: int = 2,
                  k_max: int = 10) -> (int, dict):
    """
    Run KMeans for k in [k_min..k_max], compute silhouette scores,
    and return the best k and the score dict.
    """
    best_k = k_min
    best_score = -1.0
    scores = {}
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels)
        scores[k] = score
        print(f"[K={k}] silhouette = {score:.3f}")
        if score > best_score:
            best_k, best_score = k, score
    print(f"=> chosen k = {best_k} (silhouette = {scores[best_k]:.3f})")
    return best_k, scores


def plot_clusters(X_pca: np.ndarray,
                  labels: np.ndarray,
                  has_d: pd.Series,
                  title: str = "PCA + KMeans Clustering"):
    """
    Scatter plot of the first two PCA components, coloring by cluster,
    marking Has_D holders with 'X' and others with 'o'.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    markers = {0: 'o', 1: 'X'}  # 1 = Has_D, 0 = non-D
    for d_flag in [0, 1]:
        idx = (has_d.values == d_flag)
        ax.scatter(
            X_pca[idx, 0],
            X_pca[idx, 1],
            c=labels[idx],
            cmap='tab10',
            marker=markers[d_flag],
            s=100 if d_flag else 50,
            edgecolor='k' if d_flag else 'none',
            label=f"Has_D={d_flag}"
        )
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(title)
    ax.legend(title="Cluster / Has_D")
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Unsupervised clustering of One Piece characters"
    )
    parser.add_argument("--csv", default="data_extraction/df_final_onepiece.csv",
                        help="Path to df_final_onepiece.csv")
    parser.add_argument("--min_occ_aff", type=int, default=10,
                        help="Min occurrences for affiliations")
    parser.add_argument("--min_occ_occ", type=int, default=10,
                        help="Min occurrences for occupations")
    parser.add_argument("--variance", type=float, default=0.90,
                        help="PCA variance to retain (0–1)")
    parser.add_argument("--k_min", type=int, default=2,
                        help="Min number of clusters to try")
    parser.add_argument("--k_max", type=int, default=10,
                        help="Max number of clusters to try")
    args = parser.parse_args()

    # Load & preprocess
    df = load_and_clean(args.csv)
    X = build_feature_matrix(df, args.min_occ_aff, args.min_occ_occ)

    # Dimensionality reduction
    X_pca, pca = reduce_dimensionality(X.values, args.variance)

    # Find best k
    best_k, scores = select_best_k(X_pca, args.k_min, args.k_max)

    # Final clustering
    km = KMeans(n_clusters=best_k, random_state=42)
    labels = km.fit_predict(X_pca)

    # Plot with Has_D highlight
    has_d = df.set_index(df.index)['has_D'].fillna(0).astype(int)
    plot_clusters(X_pca, labels, has_d,
                  title=f"PCA (n={pca.n_components_}) + KMeans (k={best_k})")

    # Optionally save results
    df_out = df[['name']].copy()
    df_out['cluster'] = labels
    df_out['has_D'] = has_d.values
    df_out.to_csv("clustering_results.csv", index=False)
    print("[DONE] clustering_results.csv written")


if __name__ == "__main__":
    main()

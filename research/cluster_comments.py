"""
CLI: unsupervised opinion clustering on cached YouTube comments.
No API calls — everything runs locally with scikit-learn. Wires data_loader
(I/O) -> algorithms (vectorizing/clustering/PCA) -> visualize (plotting)
together — see algorithms.py for the actual clustering logic.

What it does:
1. Loads every comment from backend/cache/comments/*.json into a DataFrame
2. Vectorizes comment text with TF-IDF (algorithms.vectorize_text)
3. Clusters comments with K-means (auto-picks k via silhouette score) and DBSCAN
4. Reduces to 2D with PCA for visualization
5. Compares the unsupervised clusters against the existing GPT sentiment labels
   (Adjusted Rand Index — how much the two groupings agree)
6. Saves plots + a text summary to research/output/

Run: python research/cluster_comments.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

from algorithms import (
    vectorize_text, pick_k_by_silhouette, run_kmeans, run_dbscan,
    reduce_to_2d, cluster_sentiment_agreement,
)
from data_loader import load_all_comments, OUTPUT_DIR
from visualize import plot_clusters


def main():
    df = load_all_comments()
    print(f"Loaded {len(df)} comments from {df['video'].nunique()} videos")

    X, vectorizer = vectorize_text(df["text"])
    print("TF-IDF matrix shape:", X.shape)

    # --- K-means ---
    best_k, scores = pick_k_by_silhouette(X)
    print("Silhouette scores by k:", {k: round(v, 4) for k, v in scores.items()})
    print("Best k:", best_k)

    df["kmeans_cluster"], centers = run_kmeans(X, best_k)

    # top terms per cluster (what each cluster is actually "about")
    terms = np.array(vectorizer.get_feature_names_out())
    print("\nTop terms per K-means cluster:")
    for i in range(best_k):
        top_idx = centers[i].argsort()[::-1][:8]
        print(f"  cluster {i} (n={sum(df['kmeans_cluster'] == i)}):", ", ".join(terms[top_idx]))

    # --- DBSCAN (density-based, flags outliers as -1) ---
    df["dbscan_cluster"] = run_dbscan(X.toarray())
    n_outliers = (df["dbscan_cluster"] == -1).sum()
    print(f"\nDBSCAN found {df['dbscan_cluster'].nunique() - 1} clusters + {n_outliers} outlier comments")

    # --- agreement with existing GPT sentiment labels ---
    ari = cluster_sentiment_agreement(df["sentiment"], df["kmeans_cluster"])
    print(f"\nAdjusted Rand Index (K-means clusters vs GPT sentiment labels): {ari:.4f}")
    print("(0 = no agreement, 1 = perfect agreement — this tells you how much unsupervised")
    print(" text clustering naturally lines up with GPT's sentiment classification)")

    # --- 2D visualization ---
    coords = reduce_to_2d(X.toarray())
    df["pca_x"], df["pca_y"] = coords[:, 0], coords[:, 1]

    out_path = plot_clusters(df, best_k)
    print(f"\nSaved plot: {out_path}")

    csv_path = os.path.join(OUTPUT_DIR, "clustered_comments.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved full data: {csv_path}")


if __name__ == "__main__":
    main()

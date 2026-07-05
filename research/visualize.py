"""
Console/plot presentation for analysis results. Depends on matplotlib and the
DataFrames algorithms.py produces — no statistical logic lives here, so
changing how something is plotted never touches the algorithm, and vice versa.
"""
import os

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"  # Korean-label plots (reaction trend) need this on Windows
plt.rcParams["axes.unicode_minus"] = False

from algorithms import Z_THRESHOLD
from data_loader import OUTPUT_DIR

TOP_N_COMMENTS = 5

# app's own theme palette (frontend/src/assets/style.css, dark theme)
BG = "#121110"
CARD = "#1e1c1a"
BORDER = "#3a3532"
TEXT = "#eeece9"
SUBTEXT = "#a39c92"
POSITIVE = "#22c55e"
NEGATIVE = "#f43f5e"
GOLD = "#C0AB7E"
GOLD_LIGHT = "#D8C690"
TREND_GRAY = "#8a857c"


def show_bucket_comments(df_video: pd.DataFrame, bucket_start, bucket_end):
    """Prints the top-liked comments within a bucket window — what actually drove it."""
    window = df_video[(df_video["publishedAt"] >= bucket_start) & (df_video["publishedAt"] <= bucket_end)]
    top = window.sort_values("likeCount", ascending=False).head(TOP_N_COMMENTS)
    for _, row in top.iterrows():
        text = row["text"].replace("\n", " ")[:150]
        print(f"        [{row['sentiment']:<8} | {row['likeCount']:>4} likes | {row['topic']}] {text}")


def plot_burst_bars(bucketed: pd.DataFrame, video_id: str) -> str:
    """Simple bar plot — net sentiment per bucket, colored by burst status."""
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = bucketed["z_score"].apply(
        lambda z: "crimson" if z <= -Z_THRESHOLD else ("seagreen" if z >= Z_THRESHOLD else "steelblue")
    )
    ax.bar(bucketed.index, bucketed["net_sentiment"], width=0.03, color=colors)
    ax.axhline(bucketed["net_sentiment"].mean(), color="gray", linestyle="--", label="baseline mean")
    ax.set_ylabel("Net sentiment (POSITIVE=+1, NEUTRAL=0, NEGATIVE=-1)")
    ax.set_title(f"Two-sided sentiment burst detection — {video_id}")
    ax.legend()
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "burst_detection.png")
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_reaction_trend(bucketed: pd.DataFrame, video_id: str, bucket_size: int):
    """Diverging bar chart (positive up / negative down) + net-sentiment trend line."""
    pos, neg = bucketed["positive"].values, bucketed["negative"].values
    x = bucketed.index
    bar_width = (x.max() - x.min()) / max(len(x), 1) * 0.7 if len(x) > 1 else pd.Timedelta(hours=6)

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(CARD)

    ax.bar(x, pos, width=bar_width, color=POSITIVE, alpha=0.85, label="긍정", zorder=3)
    ax.bar(x, -neg, width=bar_width, color=NEGATIVE, alpha=0.85, label="부정", zorder=3)

    net_trend = bucketed["net_sentiment"] * bucketed["total"]
    ax.plot(x, net_trend, color=TREND_GRAY, linewidth=2, marker="o", markersize=3,
            markerfacecolor=BG, markeredgecolor=TREND_GRAY, label="순 감정 추세", zorder=4)

    burst_ts = bucketed[bucketed["is_burst"]].index
    for i, ts in enumerate(burst_ts):
        y = net_trend.loc[ts]
        ax.scatter([ts], [y], marker="*", s=550, color=GOLD_LIGHT, edgecolor=GOLD,
                   linewidth=1.2, zorder=6, label="이상치 감지" if i == 0 else None)

    ax.axhline(0, color=BORDER, linewidth=1)
    ax.grid(axis="y", color=BORDER, linewidth=0.7, alpha=0.5)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left", "bottom"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=SUBTEXT, labelsize=9)

    ax.set_ylabel("댓글 수 (부정 ↓ / 긍정 ↑)", color=SUBTEXT, fontsize=10)
    ax.set_title(f"{video_id}  ·  구간당 댓글 {bucket_size}개 (등빈도 구간화)", color=SUBTEXT, fontsize=10, loc="left", pad=12)
    fig.suptitle("감정 반응 트렌드  ·  이상치 감지", color=TEXT, fontsize=15, fontweight="bold", x=0.06, ha="left")
    ax.legend(facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT, loc="upper right", framealpha=0.9)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_path = os.path.join(OUTPUT_DIR, f"reaction_trend_{video_id}.png")
    plt.savefig(out_path, dpi=150, facecolor=BG)
    plt.close(fig)
    return out_path, burst_ts


def plot_clusters(df: pd.DataFrame, best_k: int) -> str:
    """Side-by-side PCA scatter: unsupervised K-means clusters vs. GPT sentiment labels."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for cluster_id in sorted(df["kmeans_cluster"].unique()):
        sub = df[df["kmeans_cluster"] == cluster_id]
        axes[0].scatter(sub["pca_x"], sub["pca_y"], s=8, alpha=0.6, label=f"cluster {cluster_id}")
    axes[0].set_title(f"K-means clusters (k={best_k})")
    axes[0].legend(markerscale=2, fontsize=8)

    colors = {"POSITIVE": "tab:green", "NEUTRAL": "tab:gray", "NEGATIVE": "tab:red"}
    for label, color in colors.items():
        sub = df[df["sentiment"] == label]
        axes[1].scatter(sub["pca_x"], sub["pca_y"], s=8, alpha=0.6, c=color, label=label)
    axes[1].set_title("GPT sentiment labels (for comparison)")
    axes[1].legend(markerscale=2, fontsize=8)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "clusters_vs_sentiment.png")
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path

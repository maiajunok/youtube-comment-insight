"""
Core statistical algorithms.

Pure functions only: DataFrame/array in, DataFrame/array out. No file I/O, no
printing, no plotting. Safe to unit-test, import, or reuse anywhere without
side effects — this is the one file to touch when the actual analysis logic
(bucketing strategy, anomaly threshold, clustering approach) changes.
"""
import pandas as pd

# ── Sentiment scoring ────────────────────────────────────────────────────
SENTIMENT_SCORE = {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1}

# ── Burst / anomaly detection ────────────────────────────────────────────
Z_THRESHOLD = 1.5        # flag buckets with |z| >= this, relative to the video's own baseline
BUCKET_MIN_COMMENTS = 25    # skip videos too sparse to bucket meaningfully
MIN_PER_BUCKET = 15         # ignore individual buckets with fewer comments than this (noisy ratios)


def format_elapsed(delta: pd.Timedelta) -> str:
    """'N일/N주/N개월' style relative label — same phase logic as the app's
    fixed 0-1h/1-24h/1-7d/7-30d/30d+ buckets, just continuous instead of 5 steps."""
    hours = delta.total_seconds() / 3600
    if hours < 1:
        return f"{max(round(delta.total_seconds() / 60), 0)}분"
    if hours < 24:
        return f"{round(hours)}시간"
    days = hours / 24
    if days < 14:
        return f"{round(days)}일"
    if days < 60:
        return f"{round(days / 7)}주"
    if days < 365:
        return f"{round(days / 30)}개월"
    return f"{round(days / 365, 1)}년"


def bucket_by_count(df_video: pd.DataFrame, bucket_size: int = 40) -> pd.DataFrame:
    """
    Equal-frequency (quantile) binning: every bucket holds the same number of
    comments, so bucket *width in time* stretches or shrinks automatically with
    comment density. Dense periods (right after upload) get narrow, high-resolution
    buckets; sparse periods (months/years later) get wide buckets — no manual
    freq tuning needed, and it works the same way for a video from last week or
    four years ago.
    """
    df_sorted = df_video.sort_values("publishedAt").reset_index(drop=True)
    df_sorted["bucket_id"] = df_sorted.index // bucket_size

    bucketed = df_sorted.groupby("bucket_id").agg(
        total=("score", "size"),
        net_sentiment=("score", "mean"),
        positive=("sentiment", lambda s: (s == "POSITIVE").sum()),
        negative=("sentiment", lambda s: (s == "NEGATIVE").sum()),
        bucket_start=("publishedAt", "min"),
        bucket_end=("publishedAt", "max"),
        bucket_mid=("publishedAt", lambda s: s.iloc[len(s) // 2]),
    )
    # drop a trailing partial bucket (fewer than bucket_size comments)
    bucketed = bucketed[bucketed["total"] >= bucket_size * 0.5]
    return bucketed.set_index("bucket_mid")


def detect_bursts(df_video: pd.DataFrame, bucket_size: int = 40):
    """
    Two-sided z-score anomaly detection on net sentiment per bucket, relative
    to the video's own baseline (mean/std across its own buckets). Returns
    (None, None) if there isn't enough dense data to bucket meaningfully.
    """
    if len(df_video) < BUCKET_MIN_COMMENTS:
        return None, None

    bucketed = bucket_by_count(df_video, bucket_size=bucket_size)
    if len(bucketed) < 4:
        return None, None

    mean, std = bucketed["net_sentiment"].mean(), bucketed["net_sentiment"].std()
    if std == 0 or pd.isna(std):
        return None, None

    bucketed["z_score"] = (bucketed["net_sentiment"] - mean) / std
    bucketed["is_burst"] = bucketed["z_score"].abs() >= Z_THRESHOLD
    bucketed["direction"] = bucketed["z_score"].apply(lambda z: "POSITIVE SPIKE" if z > 0 else "NEGATIVE SPIKE")

    return bucketed, bucket_size


# ── Clustering ────────────────────────────────────────────────────────────
def vectorize_text(texts, max_features: int = 3000, min_df: int = 3):
    """
    Character n-gram TF-IDF. Comments are a Korean/English mix — word-level
    TF-IDF assumes whitespace-separated tokens, which works for English but
    shreds Korean (no morphological analyzer here, e.g. KoNLPy/Mecab).
    Character n-grams sidestep that: they pick up recurring sub-word patterns
    in both languages without needing a language-specific tokenizer.
    Returns (X, vectorizer) — the vectorizer is needed later for feature names.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(max_features=max_features, min_df=min_df, analyzer="char_wb", ngram_range=(2, 4))
    X = vectorizer.fit_transform(texts)
    return X, vectorizer


def pick_k_by_silhouette(X, k_range=range(2, 9)):
    """Picks the K-means k that maximizes silhouette score. Returns (best_k, scores)."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    scores = {}
    for k in k_range:
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
        scores[k] = silhouette_score(X, labels)
    best_k = max(scores, key=scores.get)
    return best_k, scores


def run_kmeans(X, k: int):
    """Fits K-means with a chosen k. Returns (labels, cluster_centers)."""
    from sklearn.cluster import KMeans

    model = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = model.fit_predict(X)
    return labels, model.cluster_centers_


def run_dbscan(X, eps: float = 0.8, min_samples: int = 5):
    """Density-based clustering — flags sparse points as outliers (-1), unlike K-means."""
    from sklearn.cluster import DBSCAN

    return DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit_predict(X)


def reduce_to_2d(X):
    """PCA down to 2 components, purely so clusters can be scatter-plotted."""
    from sklearn.decomposition import PCA

    return PCA(n_components=2, random_state=42).fit_transform(X)


def cluster_sentiment_agreement(sentiment_labels, cluster_labels) -> float:
    """Adjusted Rand Index — how much unsupervised clusters agree with GPT sentiment labels.
    0 = no agreement, 1 = perfect agreement."""
    from sklearn.metrics import adjusted_rand_score

    return adjusted_rand_score(sentiment_labels, cluster_labels)

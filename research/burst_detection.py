"""
CLI: statistical burst detection on GPT-labeled sentiment — no additional AI
calls. Wires data_loader (I/O) -> algorithms (bucketing + z-score) ->
visualize (printing/plotting) together.

This is the "early warning" layer a data scientist adds on top of one-time AI
labeling — pure pandas/numpy under the hood, zero extra API cost after the
initial labeling. See algorithms.py for the actual detection logic.

Run: python research/burst_detection.py [video_id]
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from algorithms import detect_bursts
from data_loader import load_video_comments, all_video_ids
from visualize import show_bucket_comments, plot_burst_bars


def analyze_video(video_id: str, plot: bool = False):
    df_video = load_video_comments(video_id)
    bucketed, bucket_size = detect_bursts(df_video)
    if bucketed is None:
        print(f"[{video_id}] not enough dense data to analyze")
        return None

    n_bursts = bucketed["is_burst"].sum()
    print(f"\n[{video_id}] baseline net sentiment {bucketed['net_sentiment'].mean():.2f} "
          f"± {bucketed['net_sentiment'].std():.2f}  ({n_bursts} burst window(s))")

    for ts, row in bucketed[bucketed["is_burst"]].iterrows():
        print(f"    {ts}  {row['direction']}  (z={row['z_score']:.2f}, net_sentiment={row['net_sentiment']:.2f}, n={int(row['total'])})")
        show_bucket_comments(df_video, row["bucket_start"], row["bucket_end"])

    if plot:
        out_path = plot_burst_bars(bucketed, video_id)
        print(f"\nSaved plot: {out_path}")

    return bucketed


def main():
    if len(sys.argv) > 1:
        analyze_video(sys.argv[1], plot=True)
        return

    results = {}
    for video_id in all_video_ids():
        bucketed = analyze_video(video_id)
        if bucketed is not None:
            results[video_id] = bucketed

    # plot whichever video has the most usable buckets (densest, most reliable)
    best_video = max(results, key=lambda v: len(results[v])) if results else None
    if best_video:
        print(f"\n--- plotting densest example: {best_video} ---")
        analyze_video(best_video, plot=True)


if __name__ == "__main__":
    main()

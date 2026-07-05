"""
CLI: reaction trend chart, diverging style — positive comments bar up,
negative comments bar down from a zero baseline, with a net-sentiment trend
line and flagged anomalies starred. Wires data_loader (I/O) -> algorithms
(bucketing + z-score) -> visualize (plotting) together — see algorithms.py
for the actual bucketing/detection logic.

Run: python analysis/reaction_trend.py <video_id> [bucket_size]
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from algorithms import detect_bursts
from data_loader import load_video_comments, all_video_ids
from visualize import show_bucket_comments, plot_reaction_trend


def run(video_id: str, bucket_size: int = 40):
    df_video = load_video_comments(video_id)
    bucketed, bucket_size = detect_bursts(df_video, bucket_size=bucket_size)
    if bucketed is None:
        print(f"[{video_id}] not enough dense data to analyze")
        return

    out_path, burst_ts = plot_reaction_trend(bucketed, video_id, bucket_size)
    print(f"Saved: {out_path}")

    print(f"\n총 {len(df_video)}개 댓글, {len(bucketed)}개 구간 (구간당 ~{bucket_size}개, 등빈도)")
    print(f"이상치 구간: {len(burst_ts)}개\n")
    for ts in burst_ts:
        row = bucketed.loc[ts]
        print(f"  {row['bucket_start']} ~ {row['bucket_end']}  {row['direction']}  (z={row['z_score']:.2f}, n={int(row['total'])})")
        show_bucket_comments(df_video, row["bucket_start"], row["bucket_end"])
        print()


if __name__ == "__main__":
    video_id = sys.argv[1] if len(sys.argv) > 1 else None
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    if video_id:
        run(video_id, bucket_size=size)
    else:
        for vid in all_video_ids():
            run(vid, bucket_size=size)
            print("=" * 80)

"""
rolling_stats.py

Utilities for computing per-frame rolling-window listening statistics.

This module purposely contains **only** data-side logic; it has no Matplotlib
dependencies so it can be unit-tested quickly and reused by both the track and
artist visualisations in future phases.
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, Iterable, List, Tuple

__all__ = ["calculate_rolling_window_stats"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_rolling_window_stats(
    cleaned_df_for_rolling_stats: pd.DataFrame,
    animation_frame_timestamps: Iterable[pd.Timestamp],
    windows: Tuple[int, int] | List[int] = (7, 30),
    *,
    base_freq: str = "D",
    mode: str = "tracks",
) -> Dict[pd.Timestamp, Dict[str, dict | None]]:
    """Return top-track or top-artist statistics for several rolling windows.

    Parameters
    ----------
    cleaned_df_for_rolling_stats
        DataFrame containing one row per play event.  *Must* have a
        timezone-aware ``timestamp`` column.  The function will add an
        entity ID column (``song_id`` or ``artist_id``) if it is missing.
        ``original_artist`` / ``original_track`` columns – while optional – are highly
        recommended so that display names can be propagated downstream.
    animation_frame_timestamps
        Timestamps for which the animation will draw a frame.  We only need to
        compute the rolling values for these specific instants.
    windows
        Iterable of window sizes *in days* – usually ``(7, 30)``.
    base_freq
        The base frequency for aggregation before rolling.
    mode
        Visualization mode: "tracks" for track-based statistics, "artists" for artist-based.

    Returns
    -------
    dict
        ``{frame_ts: {"top_7_day": {...}|None, "top_30_day": {...}|None}}``
        matching the structure expected by *main_animator.py*.
        The inner dict structure varies by mode.
    """

    # Convert *windows* to an ordered list so index is deterministic.
    window_sizes: List[int] = sorted({int(w) for w in windows})

    # ---------------------------------------------------------------------
    # Guard clauses & basic validation
    # ---------------------------------------------------------------------
    if cleaned_df_for_rolling_stats is None or cleaned_df_for_rolling_stats.empty:
        # Return a dict with all-None entries so downstream code works.
        return {
            ts: {f"top_{w}_day": None for w in window_sizes}  # type: ignore[var-annotated]
            for ts in animation_frame_timestamps
        }

    if "timestamp" not in cleaned_df_for_rolling_stats.columns:
        raise ValueError("cleaned_df_for_rolling_stats must contain a 'timestamp' column.")

    # Ensure timestamp column is timezone-aware (UTC).
    cleaned_df = cleaned_df_for_rolling_stats.copy()
    cleaned_df["timestamp"] = pd.to_datetime(cleaned_df["timestamp"], utc=True)

    # ---------------------------------------------------------------------
    # Ensure we have an entity ID column that uniquely identifies each entity
    # (song or artist). We deliberately reproduce the logic used in
    # prepare_data_for_bar_chart_race so that results stay consistent.
    # ---------------------------------------------------------------------
    if mode == "tracks":
        entity_id_col = "song_id"
        if "song_id" not in cleaned_df.columns:
            if {"artist", "track"}.issubset(cleaned_df.columns):
                cleaned_df["song_id"] = (
                    cleaned_df["artist"].astype(str).str.lower().str.strip()
                    + " - "
                    + cleaned_df["track"].astype(str).str.lower().str.strip()
                )
            else:
                raise ValueError(
                    "DataFrame missing 'song_id' and the columns necessary to create it ('artist', 'track')."
                )
    elif mode == "artists":
        entity_id_col = "artist_id"
        if "artist_id" not in cleaned_df.columns:
            if "artist" in cleaned_df.columns:
                cleaned_df["artist_id"] = cleaned_df["artist"].astype(str).str.lower().str.strip()
            else:
                raise ValueError(
                    "DataFrame missing 'artist_id' and the column necessary to create it ('artist')."
                )
    else:
        raise ValueError(f"Unsupported mode: {mode}. Must be 'tracks' or 'artists'.")

    # Cache original-case names for quick lookup later.
    entity_id_to_originals: Dict[str, dict] = {}
    if mode == "tracks" and {"original_artist", "original_track"}.issubset(cleaned_df.columns):
        entity_id_to_originals = (
            cleaned_df.drop_duplicates("song_id")
            .set_index("song_id")[["original_artist", "original_track"]]
            .to_dict("index")
        )
    elif mode == "artists" and "original_artist" in cleaned_df.columns:
        entity_id_to_originals = (
            cleaned_df.drop_duplicates("artist_id")
            .set_index("artist_id")[["original_artist"]]
            .to_dict("index")
        )

    # ---------------------------------------------------------------------
    # 1. Convert play events to *daily* counts per entity – this vastly reduces
    #    the matrix size and makes the rolling operation O(#days * #entities)
    #    instead of O(#events).
    # ---------------------------------------------------------------------
    cleaned_df["bucket_ts"] = cleaned_df["timestamp"].dt.floor(base_freq)
    counts = cleaned_df.groupby(["bucket_ts", entity_id_col]).size().unstack(fill_value=0)

    # Build continuous index so rolling works across gaps.
    idx_start = counts.index.min()
    idx_end = max(pd.to_datetime(animation_frame_timestamps, utc=True))
    full_range = pd.date_range(idx_start, idx_end, freq=base_freq, tz="UTC")
    counts = counts.reindex(full_range, fill_value=0)

    # ---------------------------------------------------------------------
    # 2. Pre-compute rolling sums and, for each day, the *top entity* + its
    #    play count for every requested window.
    # ---------------------------------------------------------------------
    top_entity_by_window: Dict[int, pd.Series] = {}
    top_count_by_window: Dict[int, pd.Series] = {}

    for w in window_sizes:
        # Using a fixed-length window in *days*.
        rolling_sum = counts.rolling(window=f"{w}D", min_periods=1).sum()
        # idxmax gives NaN for rows with all 0. We therefore fillna("") later.
        top_entity_by_window[w] = rolling_sum.idxmax(axis=1)
        top_count_by_window[w] = rolling_sum.max(axis=1).astype(int)

    # ---------------------------------------------------------------------
    # 3. Assemble the per-frame dictionary in exactly the format that
    #    draw_and_save_single_frame expects.
    # ---------------------------------------------------------------------
    results: Dict[pd.Timestamp, Dict[str, dict | None]] = {}

    for ts in animation_frame_timestamps:
        # Convert ts to pandas.Timestamp (tz-aware) and normalise to *date*.
        ts_dt = pd.to_datetime(ts, utc=True)
        date_key = ts_dt.normalize()

        frame_info: Dict[str, dict | None] = {}
        for w in window_sizes:
            entity_id = top_entity_by_window[w].get(date_key)
            plays = int(top_count_by_window[w].get(date_key, 0))

            if entity_id and plays > 0:
                # Retrieve original names (if available) for nicer labels.
                if mode == "tracks":
                    originals = entity_id_to_originals.get(
                        entity_id,
                        {"original_artist": "Unknown Artist", "original_track": "Unknown Track"},
                    )
                    frame_info[f"top_{w}_day"] = {
                        "song_id": entity_id,
                        "plays": plays,
                        "original_artist": originals.get("original_artist", "Unknown Artist"),
                        "original_track": originals.get("original_track", "Unknown Track"),
                    }
                elif mode == "artists":
                    originals = entity_id_to_originals.get(
                        entity_id,
                        {"original_artist": "Unknown Artist"},
                    )
                    frame_info[f"top_{w}_day"] = {
                        "artist_id": entity_id,
                        "plays": plays,
                        "original_artist": originals.get("original_artist", "Unknown Artist"),
                    }
            else:
                frame_info[f"top_{w}_day"] = None

        results[ts_dt] = frame_info

    return results 
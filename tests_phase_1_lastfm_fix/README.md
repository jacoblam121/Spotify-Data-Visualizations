# Phase 1: Last.fm Similarity Fix - Manual Testing

This folder contains tests for verifying that the Last.fm similarity edge creation is working correctly.

## What Was Fixed

The Last.fm API was working, but artist similarity data wasn't being promoted to the top-level field that network generation expected. This has been fixed in `artist_data_fetcher.py`.

## Manual Test

Run the manual test to verify the fix:

```bash
# Basic test with 8 artists
python test_lastfm_edges_manual.py

# Test with 5 artists and lower similarity threshold
python test_lastfm_edges_manual.py 5 0.3

# Test with 10 artists and higher similarity threshold  
python test_lastfm_edges_manual.py 10 0.6
```

## Expected Results

✅ **Before Fix**: 0 edges created  
✅ **After Fix**: Multiple edges showing artist relationships

Example output:
```
🔗 Artist Similarity Relationships:
   1. ヨルシカ ↔ yoasobi
      Similarity: 0.512 (51.2%)
   2. aimer ↔ yoasobi  
      Similarity: 0.463 (46.3%)
   3. aimer ↔ ヨルシカ
      Similarity: 0.460 (46.0%)
```

## Parameters

- **num_artists**: How many top artists to include (3-50)
- **similarity_threshold**: Minimum similarity to create edge (0.0-1.0)
  - 0.3 = More edges, lower quality relationships
  - 0.5 = Fewer edges, higher quality relationships

## Output Files

Test generates JSON files like:
- `manual_test_network_8artists_20250612_234500.json`

These contain the full network data with nodes and edges for visualization.
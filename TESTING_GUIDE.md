# Testing Guide for Phases 1 & 2

This guide provides comprehensive instructions for manually testing all the new functionality implemented in Phases 1 and 2.

## 🚀 Quick Start

### 1. Run the Full Test Suite
```bash
python test_phases_1_2.py
```
This runs all tests automatically and gives you a complete report.

### 2. Interactive Quick Testing
```bash
python quick_test.py
```
This opens an interactive menu for selective testing.

### 3. Command Line Quick Tests
```bash
# Test configuration
python quick_test.py config

# Test data processing
python quick_test.py data

# Test artist photos
python quick_test.py artist "Taylor Swift"
python quick_test.py artist "ヨルシカ"

# View cache files
python quick_test.py cache
```

## 🔄 Mode Switching

### Switch Between Visualization Modes
```bash
# Switch to artists mode
python switch_mode.py artists

# Switch to tracks mode  
python switch_mode.py tracks

# Interactive mode switching
python switch_mode.py
```

## 📋 Phase 1 Testing Checklist

### ✅ Configuration System
- [ ] Configuration loads successfully
- [ ] Mode validation works (tracks/artists/invalid)
- [ ] Current mode is correctly detected

**Test Command:**
```bash
python quick_test.py config
```

### ✅ Data Processing - Both Modes
- [ ] Data loads from your source (Spotify JSON or Last.fm CSV)
- [ ] Tracks mode produces track-based race data
- [ ] Artists mode produces artist-based race data
- [ ] Artist mode includes fallback track info for each artist
- [ ] Both modes show correct entity counts

**Test Command:**
```bash
python quick_test.py data
```

**Expected Results:**
- Tracks mode: Creates `song_id` entities (e.g., "artist - track")
- Artists mode: Creates `artist_id` entities (e.g., "artist")
- Artists mode includes `most_played_track`, `most_played_album`, `most_played_track_uri`

### ✅ Rolling Stats - Both Modes
- [ ] Rolling stats calculate for tracks mode
- [ ] Rolling stats calculate for artists mode
- [ ] 7-day and 30-day windows work correctly
- [ ] Results include proper original artist/track names

**Test Command:**
```bash
python test_phases_1_2.py
```

## 📸 Phase 2 Testing Checklist

### ✅ Artist Profile Photos
- [ ] Major artists retrieve profile photos (Taylor Swift, Paramore)
- [ ] International artists work (ヨルシカ, etc.)
- [ ] Photos are downloaded and cached correctly
- [ ] File naming follows pattern: `artist_{canonical_name}.jpg`

**Test Commands:**
```bash
python quick_test.py artist "Taylor Swift"
python quick_test.py artist "Paramore"
python quick_test.py artist "ヨルシカ"
```

### ✅ Fallback Logic
- [ ] When no artist profile photo exists, falls back to album art
- [ ] Uses most popular track info for fallback
- [ ] Gracefully handles non-existent artists

**Test Commands:**
```bash
# Test with custom artist name that might not have profile photo
python quick_test.py artist "Your Favorite Less Known Artist"
```

### ✅ Caching System
- [ ] `spotify_artist_cache.json` is created
- [ ] Subsequent requests use cache (much faster)
- [ ] Negative caching works for failed searches
- [ ] Cache includes rich artist info (popularity, followers, genres)

**Test Commands:**
```bash
python quick_test.py cache
python quick_test.py artist "Taylor Swift"  # Run twice to test caching
```

### ✅ Integration with Existing System
- [ ] Dominant color calculation works with artist photos
- [ ] Does not break existing album art functionality
- [ ] Cache files are organized properly

## 📁 Expected Cache Files

After testing, you should see these files in `album_art_cache/`:

### JSON Cache Files:
- `spotify_info_cache.json` (track/album info)
- `spotify_artist_cache.json` (NEW - artist info)
- `dominant_color_cache.json` (colors for all images)
- `negative_cache.json` (failed searches)
- `mb_album_info_cache.json` (MusicBrainz album info)

### Image Files:
- `Artist Name_artist_Artist Name.jpg` (NEW - artist profile photos)
- `Artist Name_Album Name.jpg` (existing album art)

## 🔍 Detailed Testing Scenarios

### Scenario 1: Major Artist Profile Photo
```bash
python quick_test.py artist "Taylor Swift"
```
**Expected:** 
- ✅ SUCCESS with profile photo
- File size: ~50-100KB
- Dominant color calculated
- Artist info with popularity 90+

### Scenario 2: International Artist
```bash
python quick_test.py artist "ヨルシカ"
```
**Expected:**
- ✅ SUCCESS (most popular international artists have photos)
- Unicode handling works correctly
- Proper filename generation

### Scenario 3: Fallback Testing
```bash
python quick_test.py artist "Some Obscure Artist Name 12345"
```
**Expected:**
- ❌ No artist profile photo found
- May attempt fallback to album art if you provide fallback info
- Graceful failure handling

### Scenario 4: Mode Switching Data Test
```bash
# Test in tracks mode
python switch_mode.py tracks
python quick_test.py data

# Test in artists mode  
python switch_mode.py artists
python quick_test.py data
```
**Expected:**
- Different entity counts between modes
- Artists mode shows fewer entities than tracks mode
- Both modes process the same source data

## 🐛 Troubleshooting

### Common Issues:

1. **"No data available"**
   - Check your data source configuration in `configurations.txt`
   - Ensure your data files exist (`lastfm_data.csv` or `spotify_data.json`)

2. **"Failed to get Spotify access token"**
   - Check your Spotify API credentials in `configurations.txt`
   - Ensure `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set

3. **"No artist photo retrieved"**
   - Some artists may not have profile photos on Spotify
   - Try with major artists like "Taylor Swift", "Ed Sheeran", "Ariana Grande"

4. **Cache permission errors**
   - Ensure the `album_art_cache/` directory is writable
   - Check file permissions

### Debug Mode:
To see detailed debug output, edit `configurations.txt`:
```ini
[Debugging]
DEBUG_CACHE_ALBUM_ART_UTILS = True
```

## ✅ Success Criteria

Your implementation is working correctly if:

1. **Phase 1:**
   - Both tracks and artists modes process data successfully
   - Rolling stats calculate for both modes
   - Configuration validation works

2. **Phase 2:**  
   - Artist profile photos download for major artists
   - Cache system creates `spotify_artist_cache.json`
   - Dominant colors calculate for artist photos
   - File naming follows expected pattern

3. **Integration:**
   - Mode switching works seamlessly
   - No existing functionality is broken
   - Cache files are properly organized

## 🎯 Next Steps

Once all tests pass, you're ready for **Phase 3: Main Animator Integration**, which will:
- Extend `main_animator.py` to support both modes
- Implement mode-specific bar chart rendering
- Update rolling stats display for artists
- Integrate artist photos into the animation pipeline

Happy Testing! 🧪✨
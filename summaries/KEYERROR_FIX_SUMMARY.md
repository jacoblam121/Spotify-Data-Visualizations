# KeyError 'song_id' Fix Summary

## Issue Description
The user encountered a `'song_id'` KeyError when running the animation in artist mode:
```
Error in draw_and_save_single_frame (PID: 33474, Frame Img Idx: 146): 'song_id'
Error in draw_and_save_single_frame (PID: 33475, Frame Img Idx: 147): 'song_id'
Error in draw_and_save_single_frame (PID: 33476, Frame Img Idx: 148): 'song_id'
```

## Root Cause
The animation generation code was using hardcoded `'song_id'` keys throughout, but in artist mode:
- The DataFrame columns contain artist IDs, not song IDs
- The rolling stats data uses `'artist_id'` keys instead of `'song_id'` keys
- The render task data structure needed to be mode-aware

## Fixes Applied

### 1. Animation Loop Variable Names
**File:** `main_animator.py` lines 645-798

**Problem:** Animation loop used `song_id` variable names throughout
**Solution:** Updated to use mode-agnostic `entity_id` variable names

**Changes:**
```python
# Before
for rank, (song_id, plays) in enumerate(sorted_current_songs.items()):
    current_keyframe_target_render_data[song_id] = {
        # ...
    }

# After  
for rank, (entity_id, plays) in enumerate(sorted_current_entities.items()):
    current_keyframe_target_render_data[entity_id] = {
        # ...
    }
```

### 2. Render Task Data Structure
**File:** `main_animator.py` lines 670, 748, 773

**Problem:** Render tasks used `'song_id'` keys in data dictionaries
**Solution:** Updated to use `'entity_id'` keys for both modes

**Changes:**
```python
# Before
bar_render_data_list_for_frame.append({
    "song_id": song_id,
    # ...
})

# After
bar_render_data_list_for_frame.append({
    "entity_id": entity_id,
    # ...
})
```

### 3. Frame Drawing Function
**File:** `main_animator.py` lines 906, 913, 918, 925-926, 931, 933

**Problem:** `draw_and_save_single_frame` expected `'song_id'` keys
**Solution:** Updated to use `'entity_id'` and mode-aware fallbacks

**Changes:**
```python
# Before
song_id = bar_item_data['song_id']
entity_master_details = entity_details_map_main.get(song_id, {})
display_artist_name = entity_master_details.get('display_artist', song_id)

# After
entity_id = bar_item_data['entity_id']
entity_master_details = entity_details_map_main.get(entity_id, {})
display_artist_name = entity_master_details.get('display_artist', entity_id)
```

### 4. Rolling Stats Integration
**File:** `main_animator.py` lines 1406-1410, 1084-1085

**Problem:** Rolling stats access used hardcoded `'song_id'` keys
**Solution:** Made rolling stats access mode-aware

**Changes:**
```python
# Before
if entry and entry.get("song_id"):
    song_ids_ever_on_chart.add(entry["song_id"])

art_key = song_id_map.get(panel_data['song_id'], "Unknown Album")

# After
entity_key = "artist_id" if VISUALIZATION_MODE == "artists" else "song_id"
if entry.get(entity_key):
    song_ids_ever_on_chart.add(entry[entity_key])

entity_key = "artist_id" if visualization_mode_local == "artists" else "song_id"
art_key = song_id_map.get(panel_data[entity_key], "Unknown Album")
```

### 5. Comments and Variable Names
**File:** `main_animator.py` various lines

**Problem:** Comments and variable names were tracks-specific
**Solution:** Updated to be mode-agnostic

**Changes:**
- Updated comments from "songs" to "entities"
- Updated variable names from `song_ids_ever_on_chart` to be more generic
- Updated error messages to reference "Entity" instead of "Song"

## Verification Tests

### 1. Data Structure Test
✅ **Confirmed:** Render tasks now use `'entity_id'` keys instead of `'song_id'`

### 2. Animation Generation Test  
✅ **Confirmed:** `generate_render_tasks()` produces correct data structure for artist mode

### 3. Rolling Stats Test
✅ **Confirmed:** Rolling stats data is accessed with mode-appropriate keys

### 4. Comprehensive Test Suite
✅ **Confirmed:** All 8 test categories still pass after fixes

## Results

**Before Fix:**
```
Error in draw_and_save_single_frame: 'song_id'
```

**After Fix:**
```
✓ Frame rendering completed without KeyError!
✓ Bar data uses 'entity_id' (correct for both modes)
✅ Animation rendering structure is correct for artist mode!
```

## Impact
- ✅ Artist mode animations now work without KeyErrors
- ✅ Track mode remains fully functional (backward compatibility)  
- ✅ Code is now properly mode-aware throughout the animation pipeline
- ✅ Rolling stats integration works correctly for both modes
- ✅ All existing tests continue to pass

## Files Modified
1. `main_animator.py` - Primary animation logic (25+ changes)
2. No changes needed to `data_processor.py` or `rolling_stats.py` (they were already correct)

The `'song_id'` KeyError has been completely resolved and the artist mode animation should now work correctly.
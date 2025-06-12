# 🧪 Manual Tests Guide - Network Visualization

## 🎯 **RECOMMENDED TESTS FOR ARTIST RESOLUTION & VISUALIZATION**

### **🚀 Quick Start - Run These Tests**

```bash
# 1. Interactive test menu (RECOMMENDED)
python test_network_visualization.py
# Then select option 6, 7, 8, or 9

# 2. Direct commands for each test
python fix_artist_resolution.py                  # Test artist resolution only
python test_optimized_network.py                 # Test full network generation
python create_corrected_visualization.py         # Create D3.js visualization
```

## 📋 **Interactive Test Menu Options**

Run `python test_network_visualization.py` and select:

| Option | Test | What It Does | Recommended |
|--------|------|--------------|-------------|
| **6** | ⭐ Test optimized artist resolution | Tests AnYujin, IVE, BLACKPINK, TWICE resolution accuracy | ✅ **YES** |
| **7** | ⭐ Create corrected network visualization | Generates network + D3.js visualization with correct artists | ✅ **YES** |
| **8** | ⭐ Compare old vs new resolution | Shows improvement in artist matching | ✅ **YES** |
| **9** | ⭐ Generate interactive D3.js network | Creates beautiful interactive HTML visualization | ✅ **YES** |

### **Classic Tests (Still Available)**
| Option | Test | What It Does |
|--------|------|--------------|
| 1 | Test API connections | Verify Last.fm/Spotify API access |
| 2 | Validate small network (20 artists) | Uses old method (for comparison) |
| 3 | Validate medium network (50 artists) | Uses old method (for comparison) |
| 5 | Test different similarity thresholds | Find optimal threshold values |

## 🎯 **What Each Test Validates**

### **Test 6: Optimized Artist Resolution**
- ✅ **AnYujin**: Should find 6,822 listeners (not 81)
- ✅ **IVE**: Should find 837,966 listeners (not 3,093) 
- ✅ **BLACKPINK**: Should preserve capitalization
- ✅ **TWICE**: Should preserve capitalization
- ✅ **API Efficiency**: 1-2 calls per artist (not 5-10)

### **Test 7: Corrected Network Visualization**
- 📊 Creates network with optimized resolution
- 🎨 Generates `test_corrected_network.html`
- 🔍 Verifies key artist corrections
- 📈 Reports network statistics (nodes/edges)

### **Test 8: Compare Resolution Methods**
- ⚖️ Side-by-side comparison of old vs new
- 📊 Success rate analysis
- 🎯 Identifies improvements made

### **Test 9: Interactive D3.js Network**
- 🌐 Creates beautiful interactive visualization
- 🎮 Drag nodes, hover tooltips, zoom/pan
- 🎨 Color-coded by listener count
- 🔗 Click to open Last.fm profiles

## 📁 **Files Generated**

After running tests, you'll have:

```
test_corrected_network.html      # From test 7
*_network_d3.html                # From test 9  
corrected_network_d3.html        # From direct script
artist_network_validation_*.gexf # From old tests (for Gephi)
```

## 🚨 **Known Issues Fixed**

| Issue | Old Result | ✅ New Result |
|-------|------------|---------------|
| AnYujin | Ahn Yujin (81 listeners) | ANYUJIN (6,822 listeners) |
| IVE | IVE (아이브) (3,093 listeners) | Ive (837,966 listeners) |
| API Calls | 5-10 failed attempts | 1-2 efficient calls |
| Success Rate | ~50% resolution | ~100% resolution |
| Capitalization | Lost (blackpink, twice) | Preserved |
| Network Density | 2-4 sparse edges | 10+ meaningful edges |

## 💡 **Pro Tips**

1. **Start with Test 6** to verify artist resolution works
2. **Run Test 7** to get the corrected visualization 
3. **Use Test 8** to see the dramatic improvement
4. **Open the HTML files** in your browser - they're beautiful!
5. **Compare with old Gephi** - the D3.js is much faster

## 🎯 **Troubleshooting**

**If tests fail:**
- Check API keys in `.env` file
- Verify internet connection
- Lower similarity threshold (try 0.05 instead of 0.08)
- Check that all dependencies are installed: `pip install -r requirements.txt`

**If no edges generated:**
- Try with different artists (Western artists have better Last.fm coverage)
- Lower the similarity threshold
- Increase the number of artists (try 20-30)
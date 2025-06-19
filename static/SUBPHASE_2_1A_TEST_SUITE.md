# Subphase 2.1a Test Suite: Canvas Foundation

## Overview
**Goal**: Validate Canvas renderer with genre colors, renderer abstraction, and D3 integration.

**Expected Behavior**: 
- Canvas and SVG renderers should display identical network layouts
- Genre colors should be vivid on black background  
- Smooth zoom/pan functionality
- Performance monitoring should show FPS

---

## Manual Test Checklist

### 🔧 Setup Tests

#### Test 1: Initial Load
- [ ] **Action**: Open `static/network_enhanced.html` in browser
- [ ] **Expected**: 
  - Black background loads immediately
  - "Canvas" renderer selected by default
  - Loading indicator shows "Loading network data..."
  - Page loads without JavaScript errors (check Console)
- [ ] **Check**: Browser console for any error messages
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 2: Data Loading 
- [ ] **Action**: Wait for data to load (should be automatic)
- [ ] **Expected**:
  - Loading indicator disappears
  - Nodes appear as colored circles
  - Stats show correct node/edge counts (check sidebar)
  - FPS counter shows a number (may be 0 initially)
- [ ] **Note**: Which data file loaded (check console log)
- [ ] **Result**: ✅ Pass / ❌ Fail

---

### 🎨 Visual Quality Tests

#### Test 3: Genre Colors (Critical)
- [ ] **Action**: Examine node colors against black background
- [ ] **Expected Colors**:
  - Asian artists (IU, TWICE, IVE): Hot Pink (#FF69B4)
  - Pop artists (Taylor Swift): Bright Yellow (#FFEB3B) 
  - Rock artists (Paramore): Red (#F44336)
  - J-pop artists (ヨルシカ): Hot Pink (#FF69B4)
- [ ] **Check**: Colors are vivid and clearly visible on black background
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 4: Node Sizing
- [ ] **Action**: Compare node sizes
- [ ] **Expected**: 
  - Taylor Swift should be largest (highest listener count)
  - Node sizes should vary smoothly based on popularity
  - All nodes should be clearly visible (minimum 4px radius)
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 5: Glow Effects
- [ ] **Action**: Look for nodes with glow/shadow effects
- [ ] **Expected**: 
  - High play count artists should have subtle glow
  - Glow should match the node's genre color
  - Effect should be subtle, not overwhelming
- [ ] **Result**: ✅ Pass / ❌ Fail

---

### 🖱️ Interaction Tests

#### Test 6: Zoom Functionality
- [ ] **Action**: Use mouse wheel to zoom in and out
- [ ] **Expected**:
  - Smooth zoom centered on cursor position
  - Nodes scale appropriately 
  - Can zoom from 0.1x to 10x (check extreme ranges)
  - No visual artifacts or blurriness
- [ ] **Test Both**: Try zooming very far in and very far out
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 7: Pan Functionality  
- [ ] **Action**: Click and drag to pan around
- [ ] **Expected**:
  - Smooth panning movement
  - Canvas follows mouse movement accurately
  - No lag or stuttering during pan
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 8: Force Simulation
- [ ] **Action**: Adjust "Force Strength" slider (50-800)
- [ ] **Expected**:
  - Nodes respond to force changes
  - Network layout adjusts dynamically
  - Value display updates (e.g., "300")
  - Animation should be smooth
- [ ] **Result**: ✅ Pass / ❌ Fail

---

### 🔄 Renderer Switching Tests

#### Test 9: Canvas to SVG Switch
- [ ] **Action**: Switch radio button from "Canvas" to "SVG"
- [ ] **Expected**:
  - Immediate renderer switch (< 1 second)
  - Network layout preserved (nodes in same positions)
  - Genre colors identical between renderers
  - No visual flicker or artifacts
- [ ] **Check**: Console for any switch-related errors
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 10: SVG to Canvas Switch
- [ ] **Action**: Switch back from "SVG" to "Canvas"  
- [ ] **Expected**:
  - Fast switch back to Canvas
  - Layout and colors preserved
  - FPS counter reappears and shows values
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 11: Renderer Consistency
- [ ] **Action**: Switch back and forth several times
- [ ] **Expected**:
  - Both renderers show identical visual output
  - Zoom/pan state preserved across switches
  - Performance remains stable
- [ ] **Result**: ✅ Pass / ❌ Fail

---

### ⚡ Performance Tests

#### Test 12: FPS Monitoring
- [ ] **Action**: Monitor FPS counter during different activities
- [ ] **Expected FPS**:
  - Canvas (static): 60 FPS
  - Canvas (during pan): 30-60 FPS  
  - Canvas (during simulation): 15-60 FPS
  - SVG: N/A (should show "--")
- [ ] **Note**: Actual FPS values observed
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 13: Responsiveness Test
- [ ] **Action**: Rapidly zoom, pan, and adjust forces
- [ ] **Expected**:
  - Canvas maintains responsiveness
  - No significant lag or freezing
  - Interactions feel smooth and immediate
- [ ] **Compare**: Canvas vs SVG responsiveness
- [ ] **Result**: ✅ Pass / ❌ Fail

---

### 🖥️ Browser Compatibility Tests

#### Test 14: HiDPI/Retina Display
- [ ] **Action**: Test on high-DPI display if available
- [ ] **Expected**:
  - Nodes appear crisp, not blurry
  - Text remains sharp at all zoom levels
  - No pixelation artifacts
- [ ] **Note**: Display type tested (regular/HiDPI)
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 15: Window Resize
- [ ] **Action**: Resize browser window while visualization is running
- [ ] **Expected**:
  - Canvas resizes smoothly to new dimensions
  - Network layout adapts to new size
  - No visual corruption or errors
- [ ] **Result**: ✅ Pass / ❌ Fail

---

### 🐛 Edge Case Tests

#### Test 16: Error Handling
- [ ] **Action**: Temporarily break network (disconnect internet if loading external data)
- [ ] **Expected**:
  - Graceful fallback to sample data
  - Error message if sample data also fails
  - No white screen or crash
- [ ] **Result**: ✅ Pass / ❌ Fail

#### Test 17: Multiple Rapid Switches
- [ ] **Action**: Rapidly switch renderers 10+ times
- [ ] **Expected**:
  - No memory leaks (check Task Manager)
  - Performance remains stable
  - No accumulating errors in console
- [ ] **Result**: ✅ Pass / ❌ Fail

---

## Test Environment Information

**Please fill out when testing:**

- **Browser**: ________________
- **Version**: ________________  
- **OS**: ____________________
- **Display**: Regular / HiDPI
- **Data Source**: ____________ (which JSON file loaded)
- **Node Count**: _____________ 
- **Edge Count**: _____________

---

## Test Results Summary

**Overall Assessment**: ✅ Ready for next subphase / ⚠️ Minor issues / ❌ Significant problems

**Critical Issues Found**:
1. _________________________________
2. _________________________________
3. _________________________________

**Minor Issues Found**:
1. _________________________________
2. _________________________________
3. _________________________________

**Performance Notes**:
- Canvas FPS: ___________
- SVG Responsiveness: ___________
- Memory Usage: ___________

**Next Steps Recommended**:
- [ ] Proceed to Subphase 2.1b (Edge Rendering)
- [ ] Fix critical issues first
- [ ] Investigate performance problems
- [ ] Other: ________________________
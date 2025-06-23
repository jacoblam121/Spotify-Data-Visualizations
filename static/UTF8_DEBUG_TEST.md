# UTF-8 Debug Test Instructions

## 🔍 Diagnostic Steps

### Step 1: Check Console Logs
1. **Restart server**: `python ../dev_server.py` (with UTF-8 headers)
2. **Refresh browser** and open DevTools → Console
3. **Look for**: "🎌 Yorushika name check:" with Unicode debug info

**Expected Output**:
```
🎌 Yorushika name check:
  Raw name: "ヨルシカ"
  Char codes: [12520, 12523, 12471, 12459]
  Length: 4
```

**If you see wrong char codes** (like [195, 163, 226, ...]), the issue is in the source data.

### Step 2: Test SVG vs Canvas Rendering
1. **Switch to SVG**: Click "SVG - Legacy Fallback" radio button
2. **Check if Yorushika displays correctly** in SVG mode
3. **Switch back to Canvas**: Click "Canvas - High Performance"

**If SVG works but Canvas doesn't**: Font loading issue
**If both are broken**: Data encoding issue

### Step 3: Server Header Check
Open another terminal and run:
```bash
curl -I http://localhost:8000/static/network_enhanced.html
```

**Look for**: `Content-Type: text/html; charset=utf-8`

### Step 4: Font Fallback Test
In browser DevTools Console, run:
```javascript
// Test font detection
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
ctx.font = '12px "Yu Gothic UI", "Meiryo", sans-serif';
ctx.fillText('ヨルシカ', 10, 10);
console.log('Font used:', ctx.font);
```

## 🎯 Expected Results

**Success Criteria**:
- ✅ Console shows correct Unicode char codes: [12520, 12523, 12471, 12459]
- ✅ SVG renderer displays "ヨルシカ" correctly
- ✅ Canvas renderer displays "ヨルシカ" correctly  
- ✅ Server sends proper `charset=utf-8` headers

**Failure Patterns**:
- ❌ Wrong char codes → Data corruption issue
- ❌ SVG works, Canvas broken → Font loading issue
- ❌ Both broken → Server encoding issue

## 🔧 Quick Fixes Applied

1. **Unicode Normalization**: Added `normalize('NFC')` to all text
2. **Enhanced Font Stack**: Added Japanese fonts to Canvas rendering
3. **Server Headers**: Fixed `Content-Type` to include `charset=utf-8`
4. **Debug Logging**: Added detailed Unicode character inspection

This should resolve the UTF-8 encoding issue and prove Canvas can handle international characters properly.
# Phase 1A Test Guide: Flask Development Server

## Overview
This guide walks you through testing the new Flask development server that replaces the old Python SimpleHTTPServer setup.

## What We're Testing
- ✅ **Port Independence**: Server works consistently regardless of which port it runs on
- ✅ **Cache Busting**: Browser always gets fresh files (no stale cache issues)
- ✅ **CORS Support**: External resources load without cross-origin issues
- ✅ **Static File Serving**: All JavaScript, CSS, and HTML files load correctly
- ✅ **Error Handling**: Helpful error messages and debugging info

## Prerequisites
1. Install new dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Testing Steps

### Step 1: Start the New Server
```bash
python dev_server.py
```

**Expected Output:**
```
🚀 Starting Flask Development Server
📁 Serving from: /home/jacob/Spotify-Data-Visualizations
🌐 Server starting on port 8000
📱 Main app: http://localhost:8000/
🧪 Test page: http://localhost:8000/test
💚 Health check: http://localhost:8000/health
📁 Static files: http://localhost:8000/static/
🛑 Press Ctrl+C to stop
```

### Step 2: Run Automated Tests
In a **new terminal** (keep server running):
```bash
python test_phase1a.py
```

**Expected Output:**
```
🧪 Running Phase 1A Test Suite
==================================================
✅ PASS Server Health Check
✅ PASS Health Endpoint JSON
✅ PASS Cache-Control Header
✅ PASS Pragma Header
✅ PASS Expires Header
✅ PASS CORS Access-Control-Allow-Origin
✅ PASS Static file: /static/js/genre_colors.js
✅ PASS Cache headers on /static/js/genre_colors.js
[... more tests ...]
==================================================
📊 Test Summary
✅ Passed: X/X
❌ Failed: 0/X
🎉 All tests passed! Phase 1A is working correctly.
```

### Step 3: Manual Browser Tests

#### Test 3.1: Health Check
1. Open: http://localhost:8000/health
2. **Expected**: JSON response with server status
3. **Check**: Response includes cache headers

#### Test 3.2: Static Files
1. Open: http://localhost:8000/static/js/genre_colors.js
2. **Expected**: JavaScript file content loads
3. **Check**: File loads instantly (no network delay)

#### Test 3.3: Main Application  
1. Open: http://localhost:8000/
2. **Expected**: Main network visualization page loads
3. **Check**: All JavaScript files load without 404 errors

#### Test 3.4: Test Page
1. Open: http://localhost:8000/test
2. **Expected**: Phase 2.1 test page loads
3. **Check**: No console errors in browser dev tools

### Step 4: Port Independence Test

#### Test 4.1: Stop and Restart
1. Stop server (Ctrl+C)
2. Set environment variable: `export PORT=8001`
3. Restart: `python dev_server.py`
4. **Expected**: Server starts on port 8001
5. Open: http://localhost:8001/health
6. **Expected**: Same behavior as port 8000

#### Test 4.2: Cache Independence  
1. Open browser dev tools (F12)
2. Go to Network tab
3. Clear cache (right-click → "Empty Cache and Hard Reload")
4. Reload: http://localhost:8001/test
5. **Expected**: All files load fresh (no "(from cache)" labels)

### Step 5: Browser Cache Test

#### Test 5.1: Force Refresh
1. Open: http://localhost:8000/test
2. Press Ctrl+F5 (force refresh)
3. **Expected**: All files reload from server
4. **Check**: Network tab shows all files as fresh requests

#### Test 5.2: Multi-Tab Test
1. Open test page in Tab 1: http://localhost:8000/test
2. Open test page in Tab 2: http://localhost:8000/test  
3. Make a code change to any JS file
4. Refresh both tabs
5. **Expected**: Both tabs get the updated code

## Success Criteria

### ✅ Phase 1A Passes If:
- [ ] Automated test suite shows 0 failures
- [ ] Server starts on any available port automatically
- [ ] Health check endpoint returns valid JSON
- [ ] Static files load with proper cache headers
- [ ] Browser dev tools show "no-cache" on all requests
- [ ] Same behavior on different ports (8000, 8001, 8002)
- [ ] No 404 errors in browser console
- [ ] File changes are immediately visible on refresh

### ❌ Phase 1A Fails If:
- [ ] Automated tests show failures
- [ ] Server fails to start or crashes
- [ ] Browser shows cached versions of files
- [ ] CORS errors in browser console
- [ ] Different behavior on different ports
- [ ] 404 errors for static files

## Troubleshooting

### Issue: "Address already in use"
**Solution**: The old server might still be running
```bash
# Find and kill old servers
ps aux | grep python | grep server
pkill -f "python.*server"
```

### Issue: "Module not found: Flask"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Automated tests fail
**Solution**: Check server is running
```bash
curl http://localhost:8000/health
```

## Next Steps
Once Phase 1A passes all tests, we'll move to Phase 1B (cleanup) and Phase 2A (HTML fixes).

## Files Created/Modified
- ✅ `dev_server.py` - New Flask development server  
- ✅ `requirements.txt` - Added Flask dependencies
- ✅ `test_phase1a.py` - Automated test suite
- ✅ `PHASE1A_TEST_GUIDE.md` - This test guide
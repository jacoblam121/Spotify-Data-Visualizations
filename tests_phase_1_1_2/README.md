# Phase 1.1.2 Testing Infrastructure

## 🎯 Overview
Testing infrastructure for the unified three-mode network visualization.

## 📁 Files
- **`network_visualization.html`** - Main visualization file
- **`js/network-visualization.js`** - Complete JavaScript implementation
- **`server_control.py`** - Advanced server management
- **`start_server.py`** - Quick start script
- **`stop_server.py`** - Quick stop script
- **`server_status.py`** - Check server status
- **`run_tests.py`** - Comprehensive test suite

## 🚀 Quick Start

### Start Server
```bash
cd tests_phase_1_1_2
python start_server.py
```

### Test in Windows Browser
Open: `http://localhost:8080/network_visualization.html`

### Stop Server
```bash
python stop_server.py
```

## 🧪 Running Tests

### Full Test Suite
```bash
python run_tests.py
```

### Manual Server Control
```bash
# Start server with custom settings
python server_control.py start --host localhost --port 9000

# Check status
python server_control.py status

# Restart server
python server_control.py restart

# Stop server
python server_control.py stop
```

## 🎯 Test Checklist

### Mode Testing
- [ ] **Global Mode**: Large nodes = popular artists, glow = your favorites
- [ ] **Personal Mode**: Large nodes = your top plays, glow = popular artists  
- [ ] **Hybrid Mode**: Large nodes = combined metric, glow = both popular & personal

### Interaction Testing
- [ ] Smooth transitions between modes
- [ ] Force controls work (strength, distance)
- [ ] Zoom and pan functionality
- [ ] Node hover shows tooltips
- [ ] Connection highlighting
- [ ] Edge labels toggle
- [ ] Statistics update per mode
- [ ] Clicking nodes opens Last.fm links

### Performance Testing
- [ ] No lag during mode switching
- [ ] Glow effects don't cause stuttering
- [ ] Responsive force simulation
- [ ] Fast initial load

## 🔧 Server Features

### Automatic Port Finding
If port 8080 is busy, automatically finds next available port.

### Process Management
- Proper PID file management
- Clean process termination
- Status checking

### Multi-Host Support
```bash
# Bind to all interfaces (accessible from other machines)
python start_server.py 8080 0.0.0.0
```

## 🎨 Expected Behaviors

### Global Mode
- **Node Size**: Based on Last.fm global listener count
- **Glow Effect**: Your top personal artists (high play count)
- **Description**: "Node size shows global popularity. Your top artists glow."

### Personal Mode  
- **Node Size**: Based on your personal play count
- **Glow Effect**: Globally popular artists (high listener count)
- **Description**: "Node size shows your play count. Popular artists glow."

### Hybrid Mode
- **Node Size**: Weighted combination of global and personal metrics
- **Glow Effect**: Artists that are both popular AND in your top personal list
- **Description**: "Combined view. Artists both popular and personal glow."

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8080

# Or let the server find a free port automatically
python start_server.py
```

### Browser Can't Connect
1. Check server is running: `python server_status.py`
2. Try different port: `python start_server.py 9000`
3. Check firewall settings

### Visualization Not Loading
1. Check browser console for JavaScript errors
2. Verify files exist: `ls -la network_visualization.html js/`
3. Check server logs in terminal

### Data Not Loading
- Check if JSON files exist in directory
- Verify JSON file structure with `python run_tests.py`
- Falls back to embedded sample data if external files missing

## 💡 Tips

- Use **WSL + Windows browser** workflow for best results
- Keep terminal open to see server logs
- Test all three modes to verify full functionality
- Check network statistics panel updates correctly
- Verify smooth animations between modes
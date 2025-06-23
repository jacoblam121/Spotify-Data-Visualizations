# Deprecated Server Scripts

The scripts in this directory are deprecated and scheduled for deletion.
They have been replaced by `dev_server.py` in the project root.

## Migration Guide

**Old Approach:**
```bash
python start_server.py
python static/simple_server.py
python static/bulletproof_server.py
# etc.
```

**New Approach:**
```bash
python dev_server.py
```

The new Flask-based server provides:
- ✅ Professional CORS headers
- ✅ Cache-busting for development  
- ✅ Smart port detection
- ✅ Colored logging and debugging
- ✅ Health check endpoints

## What was moved here:

- `start_server.py` - Original basic HTTP server
- `simple_server.py` - Simplified server attempt
- `bulletproof_server.py` - Attempted stability fix
- `fixed_server.py` - Another attempted fix
- `working_server.py` - Yet another attempt
- `test_server.py` - Development artifact
- `kill_server.py` - Port management utility
- `server_manager.py` - Complex process management

## Removal Timeline

These files will be permanently deleted in a future release after the new server has been validated in production.

Please update any local workflows to use `dev_server.py`.
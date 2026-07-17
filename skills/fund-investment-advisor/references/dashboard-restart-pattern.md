# Dashboard Restart & Deployment Pattern

## Clean Restart (when LaunchAgent is active)

The LaunchAgent has `KeepAlive=true`, which means it auto-restarts the process after any exit.
A simple `kill $(lsof -ti :8787)` triggers launchd to spawn the OLD app.py immediately (old code, old process).

### Correct restart sequence:

**Option A — Kill twice** (fast, safe):
```bash
kill $(lsof -ti :8787)  # launchd re-spawns
sleep 1
kill $(lsof -ti :8787)  # kills launchd's copy
sleep 1
python3 app.py &        # manual start with new code
```

**Option B — Launchctl reload** (clean, recommended):
```bash
launchctl bootout gui/$(id -u)/com.your-org.fund-dashboard 2>/dev/null
sleep 1
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.your-org.fund-dashboard.plist
```

### Verify after restart:
```bash
curl -s localhost:8787/health                     # → {"status":"ok",...}
curl -s localhost:8787/api/data | python3 -c "import sys,json; d=json.load(sys.stdin); print('holdings:', len(d.get('holdings',[])), '| modules:', list(d.keys()))"
curl -s https://invest.your-domain.com/health     # tunnel check
```

## Common Deployment Errors

### 1. CPI = 0.0 on dashboard
**Root cause**: `macro_china_cpi_yearly()` returns data stuck at 2025-08.  
**Fix**: Replace with `macro_china_cpi()` (monthly CPI, current data).

### 2. `undefined%` in pressure test / stress test cards
**Root cause**: JavaScript accesses `d.impact` but backend `/api/data` returns key `impact_pct`.  
**Prevention**: Before deploying any new module, grep both:
```bash
grep "return {" app.py | grep -E "impact|stress|test"    # backend keys
grep "d\.\|data\." app.py | grep -E "impact|stress|test"  # JS consumers
```

### 3. LaunchAgent re-spawns old code
**Root cause**: launchd's `KeepAlive=true` restarts from the original Plist definition immediately after exit.  
**Detection**: After `kill`, run `ps aux | grep app.py`. If a new PID appears within 1 second, launchd re-spawned.  
**Fix**: Use Option B (launchctl bootout/bootstrap) for clean restarts.

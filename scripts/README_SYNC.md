This folder contains helper scripts to keep the local `master` branch synchronized with `origin/master`.

Files:
- `sync_once.ps1` - single-run script: fetches origin and fast-forwards local `master` if the working tree is clean.
- `sync_loop.ps1` - continuous polling loop that fetches origin periodically and fast-forwards when remote is ahead (skips if local changes exist).

Usage (PowerShell):

Single run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_once.ps1
```

Continuous (every 30s):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_loop.ps1 -IntervalSeconds 30
```

Run hidden in background (Windows):

```powershell
Start-Process -NoNewWindow -FilePath 'powershell' -ArgumentList '-ExecutionPolicy Bypass -File .\scripts\sync_loop.ps1 -IntervalSeconds 30' -WindowStyle Hidden
```

Notes:
- The scripts will not reset if there are uncommitted local changes. Commit or stash local changes before running the auto-sync.
- For production-grade continuous sync, consider using a CI/CD runner or a system service (Windows Scheduled Task) instead of a persistent polling process.

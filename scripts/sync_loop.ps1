<#
Continuous sync script.
Usage examples:
  PowerShell (interactive):
    powershell -ExecutionPolicy Bypass -File .\scripts\sync_loop.ps1 -IntervalSeconds 30
  Run hidden in background (Windows):
    Start-Process -NoNewWindow -FilePath 'powershell' -ArgumentList '-ExecutionPolicy Bypass -File .\scripts\sync_loop.ps1 -IntervalSeconds 30' -WindowStyle Hidden
#>
param(
    [int]$IntervalSeconds = 30
)
Write-Output "Starting continuous sync every $IntervalSeconds seconds. Press Ctrl+C to stop."
while ($true) {
    git fetch origin
    $counts = git rev-list --left-right --count origin/master...master 2>$null
    if (-not $counts) {
        Write-Output "Could not determine divergence. Retrying after sleep."
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }
    $parts = $counts -split '\s+' | Where-Object { $_ -ne '' }
    if ($parts.Length -lt 2) {
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }
    $behind = [int]$parts[0]
    $ahead = [int]$parts[1]
    if ($behind -gt 0) {
        $dirty = git status --porcelain
        if ($dirty) {
            Write-Output "$(Get-Date -Format o): Local working tree dirty; skipping auto-reset."
        } else {
            git checkout master
            git reset --hard origin/master
            Write-Output "$(Get-Date -Format o): Synced master (brought $behind commits)."
        }
    } elseif ($ahead -gt 0) {
        Write-Output "$(Get-Date -Format o): Local is ahead by $ahead commits; consider pushing."
    } else {
        Write-Output "$(Get-Date -Format o): Up-to-date."
    }
    Start-Sleep -Seconds $IntervalSeconds
}

# Single-run sync script: fetches origin and fast-forwards local master if clean
param()
Write-Output "Fetching origin..."
git fetch origin
$dirty = git status --porcelain
if ($dirty) {
    Write-Output "Working tree has uncommitted changes. Aborting sync. Commit or stash changes and retry."
    exit 1
}
Write-Output "Checking out master..."
git checkout master
Write-Output "Resetting master to origin/master..."
git reset --hard origin/master
Write-Output "Sync complete."

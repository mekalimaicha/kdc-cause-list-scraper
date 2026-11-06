# Pulls the scraped CSV files from GitHub and copies them into your MEGA folder.
# GitHub cannot push into a PC, so this script (run by Windows Task Scheduler) PULLS instead.
# Existing files are never deleted - new/changed files are copied in.

$RepoUrl = "https://github.com/YOUR-USERNAME/YOUR-REPO.git"      # <-- EDIT
$Branch  = "main"
$Work    = Join-Path $env:USERPROFILE "CauseListRepo"             # hidden working clone (outside MEGA)
$Dest    = "F:\MEGA\Advocate Mr. Pokhrel\Cause List Scarping"      # final folder with the year sub-folders
$Log     = Join-Path $env:USERPROFILE "CauseListSync.log"

function Log($m) { "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))  $m" | Tee-Object -FilePath $Log -Append }

try {
    if (-not (Test-Path (Join-Path $Work ".git"))) {
        Log "First run: cloning $RepoUrl"
        git clone --branch $Branch --depth 1 $RepoUrl $Work 2>&1 | ForEach-Object { Log $_ }
    } else {
        git -C $Work fetch --depth 1 origin $Branch 2>&1 | ForEach-Object { Log $_ }
        git -C $Work reset --hard "origin/$Branch" 2>&1 | ForEach-Object { Log $_ }
    }
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force | Out-Null }
    robocopy (Join-Path $Work "data") $Dest *.csv /E /R:2 /W:5 /NFL /NDL /NP /NJH | ForEach-Object { Log $_ }
    Log "Sync finished."
} catch { Log "ERROR: $_" }

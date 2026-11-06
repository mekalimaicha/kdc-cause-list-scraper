# Run ONCE (right-click -> Run with PowerShell). Creates a Windows task that syncs automatically.
$script = Join-Path $PSScriptRoot "sync_to_laptop.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$t1 = New-ScheduledTaskTrigger -Daily -At 7:30AM      # after the night scrape finishes
$t2 = New-ScheduledTaskTrigger -AtLogOn               # catches up whenever the laptop is switched on
$set = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable
Register-ScheduledTask -TaskName "CauseListSync" -Action $action -Trigger $t1,$t2 -Settings $set -Force | Out-Null
Write-Host "Task 'CauseListSync' created: daily 7:30 AM + at every log-on."

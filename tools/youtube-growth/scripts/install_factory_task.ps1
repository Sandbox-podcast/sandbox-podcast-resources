param(
    [string]$TaskName = 'SANDBOX-Factory-Simulation',
    [string]$PythonPath,
    [string]$ConfigPath,
    [string]$StateDirectory,
    [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$factoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    return
}
if (-not $PythonPath) {
    $PythonPath = Join-Path $factoryRoot '.local/factory-venv/Scripts/pythonw.exe'
}
$factoryPython = (Resolve-Path -LiteralPath $PythonPath).Path
$factoryEntry = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'factory_worker.py')).Path
if (-not $ConfigPath) { $ConfigPath = Join-Path $factoryRoot 'config/factory.json' }
$factoryConfig = (Resolve-Path -LiteralPath $ConfigPath).Path
$factorySettings = Get-Content -LiteralPath $factoryConfig -Raw | ConvertFrom-Json
if ($factorySettings.mode -ne 'simulation' -or $factorySettings.live_enabled -ne $false) {
    throw 'La tâche exige la simulation et aucune activation réelle.'
}
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    throw "La tâche existe déjà : inspecter son état avant toute modification ($TaskName)."
}
$factoryArguments = "`"$factoryEntry`" --config `"$factoryConfig`""
if ($StateDirectory) {
    $factoryState = [System.IO.Path]::GetFullPath($StateDirectory)
    $factoryArguments += " --state-dir `"$factoryState`""
}
$factoryAction = New-ScheduledTaskAction -Execute $factoryPython -Argument $factoryArguments -WorkingDirectory $factoryRoot
$factoryCurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$factoryPrincipal = New-ScheduledTaskPrincipal -UserId $factoryCurrentUser -LogonType Interactive -RunLevel Limited
$factoryTriggers = @(
    (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)),
    (New-ScheduledTaskTrigger -AtLogOn -User $factoryCurrentUser)
)
$factoryTaskSettings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 4) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $TaskName -Action $factoryAction -Trigger $factoryTriggers -Settings $factoryTaskSettings -Principal $factoryPrincipal -Description 'Factory SANDBOX locale, simulation uniquement. Aucun upload ou appel social mutant.' | Out-Null
Start-ScheduledTask -TaskName $TaskName
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State

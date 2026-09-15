$copyStart = New-Object System.Diagnostics.ProcessStartInfo
$copyStart.FileName = Join-Path $PSScriptRoot 'app\ChatGPT.exe'
$copyStart.WorkingDirectory = Join-Path $PSScriptRoot 'app'
$copyStart.UseShellExecute = $false
$profilePath = Join-Path $PSScriptRoot 'test-profile'
$copyStart.Arguments = '--user-data-dir="' + $profilePath + '"'
$copyStart.EnvironmentVariables['CODEX_ELECTRON_USER_DATA_PATH'] = $profilePath
[System.Diagnostics.Process]::Start($copyStart) | Out-Null

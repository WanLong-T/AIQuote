$ErrorActionPreference = 'Stop'
$crawlerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$crawlerScript = Get-ChildItem -LiteralPath $crawlerRoot -Filter 'crawl_history.py' -File -Recurse |
  Select-Object -First 1 -ExpandProperty FullName
$logDirectory = Join-Path $crawlerRoot 'logs'
$logFile = Join-Path $logDirectory 'one-year-crawl-utf8.log'
$since = (Get-Date).AddYears(-1).ToString('yyyy-MM-dd')

New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)
& "$env:SystemRoot\System32\chcp.com" 65001 | Out-Null
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$env:BIDDING_DB_PASSWORD = [Environment]::GetEnvironmentVariable('BIDDING_DB_PASSWORD', 'User')
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'

if (-not $env:BIDDING_DB_PASSWORD) {
  throw 'BIDDING_DB_PASSWORD is not configured for the current Windows user.'
}
if (-not $crawlerScript) {
  throw 'crawl_history.py was not found.'
}

Write-Host "Start date: $since" -ForegroundColor Cyan
Write-Host 'Press Ctrl+C to pause. Run this file again to resume from checkpoint.' -ForegroundColor Yellow
Write-Host "Log file: $logFile" -ForegroundColor DarkGray

& python $crawlerScript --since $since *>&1 | Tee-Object -FilePath $logFile -Append

if ($LASTEXITCODE -ne 0) {
  throw "Crawler stopped with exit code $LASTEXITCODE. Run this file again to resume."
}

Write-Host 'One-year crawl completed. Data has been synchronized to MySQL.' -ForegroundColor Green

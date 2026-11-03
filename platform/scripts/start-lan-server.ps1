$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$existingListener = Get-NetTCPConnection -State Listen -LocalPort 9000 -ErrorAction SilentlyContinue
if ($existingListener) {
  try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:9000/api/projects' -UseBasicParsing -TimeoutSec 5
    $payload = $response.Content | ConvertFrom-Json
    if ($response.Headers['Content-Type'] -like 'application/json*' -and $payload.data.Count -gt 0) {
      exit 0
    }
  }
  catch {}
  throw '9000端口已被其他程序占用，正式数据服务无法启动。开发服务请使用9001端口。'
}

Set-Location $projectRoot
$env:BIDDING_DB_PASSWORD = [Environment]::GetEnvironmentVariable('BIDDING_DB_PASSWORD', 'User')
& node (Join-Path $projectRoot 'scripts\serve-lan.mjs')

$ErrorActionPreference = 'Stop'
$crawlerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $crawlerRoot '江苏\crawl_history.py'
$logDirectory = Join-Path $crawlerRoot '日志'
$logFile = Join-Path $logDirectory '近三年历史采集.log'

New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$env:BIDDING_DB_PASSWORD = [Environment]::GetEnvironmentVariable('BIDDING_DB_PASSWORD', 'User')

$running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'crawl_history\.py' }
if ($running) {
  "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 历史采集任务已运行，本次不重复启动。" |
    Tee-Object -FilePath $logFile -Append
  exit 0
}

if (-not $env:BIDDING_DB_PASSWORD) {
  throw '未配置用户环境变量 BIDDING_DB_PASSWORD，无法同步 MySQL。'
}

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 启动近三年历史采集" | Tee-Object -FilePath $logFile -Append
& python $scriptPath --since ((Get-Date).AddYears(-3).ToString('yyyy-MM-dd')) *>&1 |
  Tee-Object -FilePath $logFile -Append

if ($LASTEXITCODE -ne 0) {
  throw "历史采集异常退出，退出码：$LASTEXITCODE。重新运行本脚本会从断点继续。"
}

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 近三年历史采集完成" | Tee-Object -FilePath $logFile -Append

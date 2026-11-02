$ErrorActionPreference = 'Stop'
$env:BIDDING_DB_PASSWORD = [Environment]::GetEnvironmentVariable('BIDDING_DB_PASSWORD', 'User')
$pages = 1
if ($env:BIDDING_UPDATE_PAGES -match '^\d+$') {
  $pages = [Math]::Min(20, [Math]::Max(1, [int]$env:BIDDING_UPDATE_PAGES))
}
if ($args.Count -gt 0 -and [string]$args[0] -match '^\d+$') {
  $pages = [Math]::Min(20, [Math]::Max(1, [int]$args[0]))
}

$pythonExecutable = 'D:\Python313\python.exe'
$nodeExecutable = 'D:\Node.js\node.exe'
if (-not (Test-Path -LiteralPath $pythonExecutable)) { throw "Python 执行文件不存在：$pythonExecutable" }
if (-not (Test-Path -LiteralPath $nodeExecutable)) { throw "Node.js 执行文件不存在：$nodeExecutable" }

$projectRoot = Split-Path -Parent $PSScriptRoot
$crawlerRoot = 'D:\工程投标智能决策系统\模块1\项目数据爬虫'
$crawlerScript = Join-Path $crawlerRoot '江苏\crawl_remaining.py'
$sourceData = Join-Path $projectRoot 'public\data\projects.json'
$publishedData = Join-Path $projectRoot 'dist\spa\data\projects.json'
$publicStatusFile = Join-Path $projectRoot 'public\data\update-status.json'
$statusFile = Join-Path $projectRoot 'dist\spa\data\update-status.json'
$publicHistoryFile = Join-Path $projectRoot 'public\data\update-history.json'
$historyFile = Join-Path $projectRoot 'dist\spa\data\update-history.json'
$metricsScript = Join-Path $projectRoot 'scripts\get-project-metrics.mjs'
$logDirectory = Join-Path $projectRoot 'logs'
$logFile = Join-Path $logDirectory 'data-update.log'

New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

function Write-UpdateLog([string]$message) {
  $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $message"
  $bytes = [System.Text.Encoding]::UTF8.GetBytes("$line`r`n")
  $written = $false
  # 日志查看器、杀毒软件或另一个刚结束的更新进程可能会短暂占用文件。
  # 日志失败不能中断数据更新，因此使用共享写入并做短暂重试。
  for ($attempt = 1; $attempt -le 5 -and -not $written; $attempt++) {
    try {
      $stream = [System.IO.File]::Open(
        $logFile,
        [System.IO.FileMode]::Append,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::ReadWrite
      )
      try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush()
        $written = $true
      }
      finally {
        $stream.Dispose()
      }
    }
    catch {
      if ($attempt -lt 5) { Start-Sleep -Milliseconds (100 * $attempt) }
    }
  }
  if (-not $written) {
    # 极端情况下写入进程专属备用日志，但继续执行同步主流程。
    $fallbackLog = Join-Path $logDirectory "data-update-$PID.log"
    try { [System.IO.File]::AppendAllText($fallbackLog, "$line`r`n", [System.Text.Encoding]::UTF8) } catch {}
    Write-Warning "主日志暂时不可写，已跳过本次主日志写入：$logFile"
  }
  Write-Output $line
}

function Write-Utf8Json([string]$path, [string]$content) {
  [System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding($false)))
}

function Save-UpdateHistory($record) {
  $existing = @()
  if (Test-Path -LiteralPath $publicHistoryFile) {
    $parsed = Get-Content -LiteralPath $publicHistoryFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $existing = @($parsed)
  }
  # 每次采集都追加一条独立记录；仅清理超过7天的记录，不以固定条数覆盖。
  $retentionStart = (Get-Date).AddDays(-7)
  $history = @($record) + @(
    $existing | Where-Object {
      try { [datetime]$_.updatedAt -ge $retentionStart } catch { $false }
    }
  ) | Sort-Object { [datetime]$_.updatedAt } -Descending
  $historyJson = ConvertTo-Json -InputObject @($history) -Depth 4
  Write-Utf8Json $publicHistoryFile $historyJson
  if (Test-Path -LiteralPath (Split-Path -Parent $historyFile)) {
    Write-Utf8Json $historyFile $historyJson
  }
}

$updateMutex = New-Object System.Threading.Mutex($false, 'Local\BiddingSystemDataUpdate')
$hasUpdateLock = $false
try {
  try {
    $hasUpdateLock = $updateMutex.WaitOne(0)
  }
  catch [System.Threading.AbandonedMutexException] {
    # 上一次更新进程异常退出时，当前进程已经接管互斥锁，可以继续更新。
    $hasUpdateLock = $true
  }

  if (-not $hasUpdateLock) {
    # 另一个更新进程正在持有互斥锁，也可能正在写主日志；此处只输出到
    # 当前进程标准输出，避免“安全跳过”本身反而争抢日志文件并报失败。
    Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 已有数据更新任务正在运行，本次触发已安全跳过。"
    exit 0
  }

try {
  Write-UpdateLog "开始检查最新招标公告（最新 $pages 页）。"

  $previousIds = @()
  if (Test-Path -LiteralPath $publishedData) {
    $previousPayload = Get-Content -LiteralPath $publishedData -Raw -Encoding UTF8 | ConvertFrom-Json
    $previousIds = @($previousPayload.data | ForEach-Object { [string]$_.id })
  }

  & $pythonExecutable $crawlerScript --pages $pages --refresh-list
  if ($LASTEXITCODE -ne 0) { throw "爬虫执行失败，退出码：$LASTEXITCODE" }

  Push-Location $projectRoot
  try {
    & $nodeExecutable (Join-Path $projectRoot 'scripts\sync-crawler-projects.mjs')
    if ($LASTEXITCODE -ne 0) { throw "数据同步失败，退出码：$LASTEXITCODE" }
  }
  finally {
    Pop-Location
  }

  $payload = Get-Content -LiteralPath $sourceData -Raw -Encoding UTF8 | ConvertFrom-Json
  $projects = @($payload.data)
  if ($projects.Count -eq 0) { throw '更新结果为空，已拒绝覆盖线上数据。' }

  $activeProjects = @($projects | Where-Object {
    $closedStatuses = @('已开标', '已中标', '未中标', '废标', '流标', '已终止')
    $deadlineUnknown = [string]::IsNullOrWhiteSpace([string]$_.openDate) -and [string]::IsNullOrWhiteSpace([string]$_.deadline)
    (($_.days -ne $null -and [double]$_.days -ge 0) -or $deadlineUnknown) -and $_.status -notin $closedStatuses
  })
  $newActiveIds = @($activeProjects | ForEach-Object { [string]$_.id })
  $addedCount = @($newActiveIds | Where-Object { $_ -notin $previousIds }).Count

  # 大屏从 MySQL 实时读取，因此更新记录也必须以同一数据库、同一在招口径统计。
  $metricsJson = & $nodeExecutable $metricsScript
  if ($LASTEXITCODE -ne 0) { throw "在招项目统计失败，退出码：$LASTEXITCODE" }
  $metrics = $metricsJson | ConvertFrom-Json

  $publishedDirectory = Split-Path -Parent $publishedData
  if (-not (Test-Path -LiteralPath $publishedDirectory)) {
    throw '尚未生成生产版本，请先运行 npm run build。'
  }

  $temporaryData = "$publishedData.new"
  Copy-Item -LiteralPath $sourceData -Destination $temporaryData -Force
  Move-Item -LiteralPath $temporaryData -Destination $publishedData -Force

  $status = [ordered]@{
    success = $true
    updatedAt = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    opportunityCount = [int]$metrics.opportunityCount
    addedCount = $addedCount
    source = '江苏省建设工程招标网'
  }
  $statusJson = $status | ConvertTo-Json
  Write-Utf8Json $publicStatusFile $statusJson
  Write-Utf8Json $statusFile $statusJson
  Save-UpdateHistory $status
  Write-UpdateLog "更新成功：当前在招 $($metrics.opportunityCount) 条，本次新增在招项目 $addedCount 条。"
  $exitCode = 0
}
catch {
  $failureMessage = $_.Exception.Message
  $failureStatus = [ordered]@{
    success = $false
    updatedAt = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    opportunityCount = 0
    addedCount = 0
    source = '江苏省建设工程招标网'
    message = $failureMessage
  }
  Save-UpdateHistory $failureStatus
  Write-UpdateLog "更新失败：$failureMessage；保留上一版线上数据。"
  $exitCode = 1
}
}
finally {
  if ($hasUpdateLock) {
    $updateMutex.ReleaseMutex()
  }
  $updateMutex.Dispose()
}

exit $exitCode

param([string]$BackupDir = '.\backups')
if (-not $env:DATABASE_URL) { throw 'Set DATABASE_URL first' }
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$file = Join-Path $BackupDir ("campuscart-{0}.dump" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
pg_dump $env:DATABASE_URL --format=custom --file=$file
Write-Output $file

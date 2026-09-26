param([Parameter(Mandatory=$true)][string]$BackupFile)
if (-not $env:DATABASE_URL) { throw 'Set DATABASE_URL first' }
pg_restore --clean --if-exists --no-owner --dbname=$env:DATABASE_URL $BackupFile

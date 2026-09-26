$ErrorActionPreference = "Stop"

Write-Host "[1/4] Python compile"
python -m compileall -q backend/app backend/tests scripts

Write-Host "[2/4] Backend tests"
Push-Location backend
python -m pytest
Pop-Location

Write-Host "[3/4] Frontend production build"
Push-Location frontend
npm run build
Pop-Location

Write-Host "[4/4] API smoke / readiness"
Invoke-WebRequest -UseBasicParsing http://localhost:8100/health | Out-Null
Invoke-WebRequest -UseBasicParsing http://localhost:8100/ready | Out-Null

Write-Host "CampusCart quality checks completed."

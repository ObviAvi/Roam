param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$envFile = Join-Path $Root ".env"
$frontendEnv = Join-Path $Root "frontend\.env.local"

if (-not (Test-Path $envFile)) {
  Write-Error ".env not found at $envFile"
  exit 1
}

Get-Content $envFile | ForEach-Object {
  if ($_ -match "^\s*([^#=]+)=(.+)$") {
    $name = $matches[1].Trim()
    $value = $matches[2].Trim().Trim("'").Trim('"')
    Set-Variable -Name $name -Value $value -Scope Script
  }
}

$mapbox = $MAPBOX_TOKEN
if (-not $mapbox) { $mapbox = "" }

@(
  "NEXT_PUBLIC_API_URL=http://localhost:8000"
  "NEXT_PUBLIC_MAPBOX_TOKEN=$mapbox"
  "BACKEND_URL=http://localhost:8000"
) | Set-Content -Path $frontendEnv -Encoding UTF8

Write-Host "Wrote $frontendEnv"

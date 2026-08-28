$projectRoot = $PSScriptRoot
$activateScript = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
$envFile = Join-Path $projectRoot ".env"

if (-not (Test-Path -LiteralPath $activateScript)) {
    throw "Virtual environment not found. Create it before running this script."
}

. $activateScript

if (Test-Path -LiteralPath $envFile) {
    foreach ($line in Get-Content -LiteralPath $envFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            if ($value) {
                Set-Item -Path "Env:$name" -Value $value
            }
        }
    }
}

# Google ADK reads GOOGLE_API_KEY, while lesson 01 uses GEMINI_API_KEY.
if (-not $env:GOOGLE_API_KEY -and $env:GEMINI_API_KEY) {
    $env:GOOGLE_API_KEY = $env:GEMINI_API_KEY
}

Write-Host "DAY26 environment activated: $projectRoot"
Write-Host "Python: $((Get-Command python).Source)"

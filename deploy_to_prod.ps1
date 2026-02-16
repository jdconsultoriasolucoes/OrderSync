$ErrorActionPreference = "Stop"

$source = "e:\OrderSync - Dev"
$dest = "e:\OrderSync"

# 1. Backend Copy
Write-Host "Copying Backend..."
$excludeBackend = @('scripts', '__pycache__', 'venv', '.env', '.DS_Store', 'test_*.py')
if (!(Test-Path "$dest\backend")) { New-Item -ItemType Directory -Path "$dest\backend" | Out-Null }

Get-ChildItem -Path "$source\backend" -Recurse | ForEach-Object {
    $relPath = $_.FullName.Substring(("$source\backend").Length + 1)
    $targetPath = Join-Path "$dest\backend" $relPath
    
    # Check exclusions
    $skip = $false
    foreach ($ex in $excludeBackend) {
        if ($_.FullName -match [regex]::Escape($ex)) { $skip = $true; break }
    }
    
    if (-not $skip) {
        if ($_.PSIsContainer) {
            if (!(Test-Path $targetPath)) { New-Item -ItemType Directory -Path $targetPath | Out-Null }
        } else {
            Copy-Item -Path $_.FullName -Destination $targetPath -Force
        }
    }
}

# 2. Frontend Copy
Write-Host "Copying Frontend..."
$excludeFrontend = @('node_modules', '.git', 'dist')
if (!(Test-Path "$dest\frontend")) { New-Item -ItemType Directory -Path "$dest\frontend" | Out-Null }

Get-ChildItem -Path "$source\frontend" -Recurse | ForEach-Object {
    $relPath = $_.FullName.Substring(("$source\frontend").Length + 1)
    $targetPath = Join-Path "$dest\frontend" $relPath
    
    $skip = $false
    foreach ($ex in $excludeFrontend) {
        if ($_.FullName -match [regex]::Escape($ex)) { $skip = $true; break }
    }
    
    if (-not $skip) {
        if ($_.PSIsContainer) {
            if (!(Test-Path $targetPath)) { New-Item -ItemType Directory -Path $targetPath | Out-Null }
        } else {
            Copy-Item -Path $_.FullName -Destination $targetPath -Force
        }
    }
}

# 3. Update Config.js
Write-Host "Updating Config..."
$configFile = "$dest\frontend\public\js\config.js"
if (Test-Path $configFile) {
    $content = Get-Content $configFile -Raw
    # Replace old backend URL or ensure new one is used
    # Regex to find the production URL string
    $newContent = $content -replace "https://ordersync-backend-[a-z0-9]+.onrender.com", "https://ordersync-backend-59d2.onrender.com"
    $newContent | Set-Content $configFile -NoNewline
    Write-Host "Config.js updated."
} else {
    Write-Warning "config.js not found at $configFile"
}

# 4. Copy root files (requirements, etc)
Write-Host "Copying Root Files..."
Copy-Item "$source\requirements.txt" "$dest\requirements.txt" -Force
Copy-Item "$source\render.yaml" "$dest\render.yaml" -Force
Copy-Item "$source\runtime.txt" "$dest\runtime.txt" -Force

Write-Host "Deployment Complete."

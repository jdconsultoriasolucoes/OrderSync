$ErrorActionPreference = "Stop"
$devPath = 'e:\OrderSync - Dev'
$prodPath = 'e:\OrderSync'
$exclude = @('.git', '.idea', '.vscode', '__pycache__', 'node_modules', 'venv', 'dist', 'build', '.DS_Store')

function Get-RelativePath($fullPath, $basePath) {
    return $fullPath.Substring($basePath.Length)
}

function Get-Files($path) {
    $files = Get-ChildItem -Path $path -Recurse -File
    $result = @()
    foreach ($f in $files) {
        $skip = $false
        foreach ($ex in $exclude) {
            if ($f.FullName -match [regex]::Escape($ex)) { $skip = $true; break }
        }
        if (-not $skip) {
            $result += $f
        }
    }
    return $result
}

Write-Host "Scanning Dev..."
$devFiles = Get-Files $devPath
Write-Host "Scanning Prod..."
$prodFiles = Get-Files $prodPath

$devMap = @{}
foreach ($f in $devFiles) {
    $rel = Get-RelativePath $f.FullName $devPath
    $devMap[$rel] = $f
}

$prodMap = @{}
foreach ($f in $prodFiles) {
    $rel = Get-RelativePath $f.FullName $prodPath
    $prodMap[$rel] = $f
}

$onlyInDev = @()
$onlyInProd = @()
$different = @()

foreach ($key in $devMap.Keys) {
    if (-not $prodMap.ContainsKey($key)) {
        $onlyInDev += $key
    } else {
        $d = $devMap[$key]
        $p = $prodMap[$key]
        if ($d.Length -ne $p.Length) {
            $different += @{Path=$key; Reason='Size'; DevSize=$d.Length; ProdSize=$p.Length}
        } else {
            # Size matches, check hash
            try {
                $h1 = (Get-FileHash $d.FullName).Hash
                $h2 = (Get-FileHash $p.FullName).Hash
                if ($h1 -ne $h2) {
                    $different += @{Path=$key; Reason='Content'}
                }
            } catch {
                Write-Warning "Could not hash $key`: $_"
            }
        }
    }
}

foreach ($key in $prodMap.Keys) {
    if (-not $devMap.ContainsKey($key)) {
        $onlyInProd += $key
    }
}

$result = @{
    OnlyInDev = $onlyInDev
    OnlyInProd = $onlyInProd
    Different = $different
}

$json = $result | ConvertTo-Json -Depth 4
$json | Out-File -Encoding utf8 "e:\OrderSync - Dev\workspace_diff.json"
Write-Host "Done. Saved to e:\OrderSync - Dev\workspace_diff.json"

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$file = "E:\OrderSync\backend\assets\FICHA RECADASTRO V.2026-2.xls"

if (Test-Path $file) {
    Write-Host "=========================================="
    Write-Host "FILE: $file"
    Write-Host "=========================================="
    $wb = $excel.Workbooks.Open($file)
    foreach ($s in $wb.Sheets) {
        Write-Host ("=== SHEET: " + $s.Name + " ===")
        $ur = $s.UsedRange
        $rc = $ur.Rows.Count
        $cc = $ur.Columns.Count
        Write-Host ("Rows: " + $rc + " Cols: " + $cc)
        for ($r = 1; $r -le $rc; $r++) {
            $line = @()
            for ($c = 1; $c -le $cc; $c++) {
                $val = $ur.Cells.Item($r, $c).Text
                if ($val -and $val.Trim() -ne '') {
                    $line += ("C" + $c + " (" + $ur.Cells.Item($r, $c).Address($false, $false) + "): '" + $val.Trim() + "'")
                }
            }
            if ($line.Count -gt 0) {
                Write-Host ("Row " + $r + " | " + ($line -join " | "))
            }
        }
    }
    $wb.Close($false)
} else {
    Write-Host "File not found"
}

$excel.Quit()

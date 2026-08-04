$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('E:\Projeto Sistema pedidos\arquivos analise\FICHA RECADASTRO V.2026-2.xls')
Write-Host "Total Sheets: " $wb.Sheets.Count
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
                $line += ("C" + $c + ": " + $val.Trim())
            }
        }
        if ($line.Count -gt 0) {
            Write-Host ("Row " + $r + " | " + ($line -join " | "))
        }
    }
}
$wb.Close($false)
$excel.Quit()

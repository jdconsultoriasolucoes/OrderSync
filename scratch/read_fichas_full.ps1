$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false

$files = @(
    "E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\NOVA_FICHA_DE_CADASTRO_ALISUL (1).xlsx",
    "E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\NOVA_FICHA_DE_CADASTRO_DISPET.xlsm",
    "E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Dispet_Formulario_3_Cadastro_de_Produto.xlsx"
)

foreach ($file in $files) {
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
            for ($r = 1; $r -le [Math]::Min(150, $rc); $r++) {
                $line = @()
                for ($c = 1; $c -le [Math]::Min(30, $cc); $c++) {
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
    }
}

$excel.Quit()

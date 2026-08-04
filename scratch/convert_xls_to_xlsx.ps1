$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$src = "E:\OrderSync\backend\assets\FICHA RECADASTRO V.2026-2.xls"
$dst = "E:\OrderSync\backend\assets\FICHA RECADASTRO V.2026-2.xlsx"

$wb = $excel.Workbooks.Open($src)
$wb.SaveAs($dst, 51)
$wb.Close($false)
$excel.Quit()
Write-Host "Converted $src to $dst successfully."

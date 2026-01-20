@echo off
echo ============================================================
echo   Gerador de PDF - Manual do Usuario OrderSync
echo ============================================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale Python de: https://www.python.org/downloads/
    echo Certifique-se de marcar "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Verificar se as bibliotecas estao instaladas
echo Verificando dependencias...
python -c "import reportlab" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [AVISO] Biblioteca 'reportlab' nao encontrada.
    echo Instalando dependencias...
    echo.
    python -m pip install reportlab markdown
    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao instalar dependencias.
        echo Tente executar manualmente: pip install reportlab markdown
        pause
        exit /b 1
    )
)

python -c "import markdown" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [AVISO] Biblioteca 'markdown' nao encontrada.
    echo Instalando...
    python -m pip install markdown
)

echo [OK] Dependencias verificadas
echo.

REM Executar script
echo Gerando PDF...
echo.
python gerar_pdf_manual_alternativo.py

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar PDF.
    echo.
    echo Verifique:
    echo   1. Se o arquivo MANUAL_USUARIO_ORDERSYNC.md existe
    echo   2. Se ha erros no script Python
    echo   3. Se as dependencias estao instaladas corretamente
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   PDF gerado com sucesso!
echo ============================================================
echo.
echo Arquivo: MANUAL_USUARIO_ORDERSYNC.pdf
echo.
pause

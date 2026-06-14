@echo off
REM build.bat - Gera o executavel Windows (.exe) do img2pdf
REM Execute em um ambiente Windows com Python 3 e pip instalados

echo ======================================================
echo   img2pdf - Build do executavel Windows
echo ======================================================

REM verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: Python nao encontrado no PATH.
    echo Instale em https://python.org e marque "Add to PATH".
    pause
    exit /b 1
)

REM instala dependencias
echo.
echo [1/3] Instalando/verificando dependencias...
python -m pip install pillow pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

REM limpa builds anteriores
echo [2/3] Limpando builds anteriores...
if exist build        rmdir /s /q build
if exist dist         rmdir /s /q dist
if exist __pycache__  rmdir /s /q __pycache__

REM compila usando "python -m PyInstaller" para evitar
REM o erro "'pyinstaller' nao e reconhecido como comando interno"
echo [3/3] Compilando com PyInstaller...
python -m PyInstaller img2pdf.spec
if errorlevel 1 (
    echo.
    echo ERRO: Falha na compilacao. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo   Executavel gerado em:  dist\Img2PdfZ.exe
echo ======================================================
pause

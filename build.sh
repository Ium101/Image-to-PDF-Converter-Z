#!/usr/bin/env bash
# build.sh — Gera o executável Linux (ELF 64-bit) do img2pdf
# Para Windows, rode build.bat em um ambiente Windows com Python + PyInstaller

set -e
cd "$(dirname "$0")"

echo "======================================================"
echo "  img2pdf — Build do executável Linux"
echo "======================================================"

# verifica Python
python3 --version || { echo "ERRO: Python 3 não encontrado"; exit 1; }

# instala dependências se necessário
echo ""
echo "[1/3] Instalando/verificando dependências..."
pip install pillow pyinstaller --break-system-packages -q

# limpa builds anteriores
echo "[2/3] Limpando builds anteriores..."
rm -rf build/ dist/ __pycache__/

# compila
echo "[3/3] Compilando com PyInstaller..."
pyinstaller img2pdf.spec

echo ""
echo "======================================================"
echo "  ✔  Executável gerado em:  dist/Img2PdfZ"
echo "======================================================"
echo ""
echo "Para tornar executável e rodar:"
echo "  chmod +x dist/Img2PdfZ && ./dist/Img2PdfZ"

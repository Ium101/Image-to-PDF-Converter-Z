#!/bin/bash

SCRIPT_NAME="img2pdf.py"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_NAME"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")
DESKTOP_FILE_NAME="img2pdf_z.desktop"

echo "======================================================"
echo "  IMG2PDF Z — Instalação no Linux"
echo "======================================================"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Erro: $SCRIPT_NAME não encontrado em $SCRIPT_DIR"
    exit 1
fi

mkdir -p "$APP_DIR" "$DESKTOP_DIR" "$ICON_DIR"

# ── CHECK PYTHON ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "❌ Erro: python3 não encontrado. Instale o Python 3 antes de continuar."
    exit 1
fi

# ── INSTALL DEPENDENCIES ──────────────────────────────────────────────────────
echo "📦 Verificando dependências..."
pip install pillow --break-system-packages -q 2>/dev/null || \
    pip install pillow -q 2>/dev/null || true

# ── MAKE THE SCRIPT DIRECTLY LAUNCHABLE ───────────────────────────────────────
echo "🔧 Tornando o script executável..."
chmod +x "$SCRIPT_PATH"

# ── CLEAN OLD CACHE ───────────────────────────────────────────────────────────
echo "🧹 Limpando cache antigo..."
rm -rf "$SCRIPT_DIR/__pycache__/"

# ── EMBED ICON (SVG) ─────────────────────────────────────────────────────────
echo "🖼️ Instalando ícone..."
cat > "$ICON_DIR/img2pdf_z.svg" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="256" height="256">
  <!-- Document outline: transparent fill, yellow stroke, folded top-right corner -->
  <polyline points="12,5 70,5 88,23 88,95 12,95 12,5"
            fill="none" stroke="#FFC107" stroke-width="5.5"
            stroke-linejoin="round" stroke-linecap="round"/>
  <!-- Fold crease -->
  <polyline points="70,5 70,23 88,23"
            fill="none" stroke="#FFC107" stroke-width="5.5"
            stroke-linejoin="round" stroke-linecap="round"/>
  <!-- Inner image thumbnail rectangle (landscape, above arrow) -->
  <rect x="20" y="12" width="45" height="32"
        fill="none" stroke="#FFC107" stroke-width="4"
        stroke-linejoin="round" stroke-linecap="round"/>
  <!-- Arrow: horizontal tail on RIGHT, smooth J-curve down-left, tip points DOWN -->
  <!-- Tail bar -->
  <line x1="44" y1="57" x2="74" y2="57"
        stroke="#FFC107" stroke-width="7.6" stroke-linecap="round"/>
  <!-- Curved body: from left end of tail, sweeps down then left, arrives above tip -->
  <path d="M 44,57 C 44,81 23,81 23,83"
        fill="none" stroke="#FFC107" stroke-width="7.6"
        stroke-linecap="round" stroke-linejoin="round"/>
  <!-- Arrowhead pointing DOWN -->
  <polygon points="23,87 12,77 34,77" fill="#FFC107"/>
  <!-- PDF label -->
  <text x="70" y="90" font-family="Arial,Helvetica,sans-serif" font-weight="bold"
        font-size="18" fill="#FFC107" text-anchor="middle">PDF</text>
</svg>
SVGEOF

# ── DESKTOP FILE (points straight at the .py script) ──────────────────────────
echo "🖥️ Registrando no menu do sistema..."
cat > "$APP_DIR/$DESKTOP_FILE_NAME" << DESKTOPEOF
[Desktop Entry]
Name=IMG2PDF Z
Comment=Convert images to PDF / Converter imagens para PDF
Exec=python3 "$SCRIPT_PATH"
Icon=$ICON_DIR/img2pdf_z.svg
Terminal=false
Type=Application
Categories=Utility;Graphics;
DESKTOPEOF
chmod +x "$APP_DIR/$DESKTOP_FILE_NAME"

# ── DESKTOP SHORTCUT ─────────────────────────────────────────────────────────
echo "🏠 Criando atalho na Área de Trabalho..."
cp "$APP_DIR/$DESKTOP_FILE_NAME" "$DESKTOP_DIR/$DESKTOP_FILE_NAME"
chmod 755 "$DESKTOP_DIR/$DESKTOP_FILE_NAME"

if command -v gio &>/dev/null; then
    gio set "$DESKTOP_DIR/$DESKTOP_FILE_NAME" metadata::trusted true 2>/dev/null
fi

# ── REFRESH MENUS ────────────────────────────────────────────────────────────
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APP_DIR" &>/dev/null
fi

echo "🔄 Atualizando cache do menu..."
if command -v kbuildsycoca6 &>/dev/null; then
    kbuildsycoca6 &>/dev/null
elif command -v kbuildsycoca5 &>/dev/null; then
    kbuildsycoca5 &>/dev/null
fi

echo ""
echo "======================================================"
echo "  ✅ Concluído!"
echo "     Script:     $SCRIPT_PATH"
echo "     Ícone:      $ICON_DIR/img2pdf_z.svg"
echo "     Menu:       $APP_DIR/$DESKTOP_FILE_NAME"
echo "     Desktop:    $DESKTOP_DIR/$DESKTOP_FILE_NAME"
echo "======================================================"

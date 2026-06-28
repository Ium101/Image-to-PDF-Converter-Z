# Img2Pdf — Conversor de Imagens para PDF

Converta **PNG, JPG, BMP, GIF, TIFF e WEBP** em PDF com uma interface gráfica moderna.
Distribuído como executável único — sem necessidade de instalar Python.

---

## Funcionalidades

- ✅ Suporte a PNG, JPG/JPEG, BMP, GIF, TIFF/TIF, WEBP
- ✅ Reordenação das imagens antes de converter
- ✅ Escolha de tamanho de página: Automático, A4, A3, Letter, Legal
- ✅ Orientação: Retrato ou Paisagem
- ✅ Controle de qualidade JPEG (10–100%)
- ✅ Margem configurável
- ✅ Executável único — sem dependências externas

---

## Como usar (executável)

### Linux
```bash
chmod +x dist/img2pdf
./dist/img2pdf
```

### Windows
Clique duas vezes em `dist/img2pdf.exe`.

---

## Como compilar você mesmo

### Pré-requisitos

- Python 3.8+
- pip

### Linux / macOS
```bash
pip install pillow pyinstaller
bash build.sh
# executável em: dist/img2pdf
```

### Windows
```bat
pip install pillow pyinstaller
build.bat
REM executável em: dist\img2pdf.exe
```

---

## Estrutura do projeto

```
img2pdf_app/
├── img2pdf.py      ← código-fonte principal
├── img2pdf.spec    ← configuração do PyInstaller
├── build.sh        ← script de build Linux/macOS
├── build.bat       ← script de build Windows
└── README.md
```

---

## Licença
MIT — livre para uso pessoal e comercial.

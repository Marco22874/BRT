#!/bin/bash
# Script per compilare l'applicazione BRT per macOS
# Equivalente di compila_windows.bat

echo "==================================="
echo "Compilazione App macOS - BRT"
echo "==================================="
echo ""

# Vai alla directory del progetto
cd /Users/marco/Documents/BRT

# Genera icona .icns da PNG (se non esiste)
if [ ! -f "igea_icon.icns" ]; then
    echo "Creazione icona .icns da PNG..."
    mkdir -p igea_icon.iconset
    sips -z 16 16     igea_logo.png --out igea_icon.iconset/icon_16x16.png
    sips -z 32 32     igea_logo.png --out igea_icon.iconset/icon_16x16@2x.png
    sips -z 32 32     igea_logo.png --out igea_icon.iconset/icon_32x32.png
    sips -z 64 64     igea_logo.png --out igea_icon.iconset/icon_32x32@2x.png
    sips -z 128 128   igea_logo.png --out igea_icon.iconset/icon_128x128.png
    sips -z 256 256   igea_logo.png --out igea_icon.iconset/icon_128x128@2x.png
    sips -z 256 256   igea_logo.png --out igea_icon.iconset/icon_256x256.png
    sips -z 512 512   igea_logo.png --out igea_icon.iconset/icon_256x256@2x.png
    sips -z 512 512   igea_logo.png --out igea_icon.iconset/icon_512x512.png
    cp igea_logo.png igea_icon.iconset/icon_512x512@2x.png
    iconutil -c icns igea_icon.iconset
    rm -rf igea_icon.iconset
    echo "✓ Icona creata"
fi

# Rimuovi build precedente se esiste
if [ -d "dist/Gestione_Spedizioni_BRT.app" ]; then
    echo "Rimozione build precedente..."
    rm -rf dist/Gestione_Spedizioni_BRT.app
fi

# Esegui PyInstaller
echo "Avvio compilazione con PyInstaller..."
/Users/marco/Library/Python/3.9/bin/pyinstaller \
    --onedir \
    --windowed \
    --name "Gestione_Spedizioni_BRT" \
    --icon=igea_icon.icns \
    --add-data "igea_logo.png:." \
    --add-data "Logo_BRT.svg.png:." \
    --exclude-module pytest \
    --exclude-module _pytest \
    brt_app_pyqt5.py \
    --noconfirm

echo ""
if [ -d "dist/Gestione_Spedizioni_BRT.app" ]; then
    echo "==================================="
    echo "✓ Compilazione completata!"
    echo "==================================="
    echo ""
    echo "App creata in: dist/Gestione_Spedizioni_BRT.app"
    echo ""
    echo "Per aprire l'app:"
    echo "  open dist/Gestione_Spedizioni_BRT.app"
else
    echo "==================================="
    echo "✗ Errore durante la compilazione"
    echo "==================================="
fi

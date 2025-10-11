#!/bin/bash
# Script per compilare l'applicazione BRT per macOS
# Equivalente di compila_windows.bat

echo "==================================="
echo "Compilazione App macOS - BRT"
echo "==================================="
echo ""

# Vai alla directory del progetto
cd /Users/marco/Documents/BRT

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

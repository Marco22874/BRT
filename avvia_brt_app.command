#!/bin/bash
# Script di avvio applicazione BRT

# Vai nella directory dell'app
cd "$(dirname "$0")"

# Avvia l'applicazione
python3 brt_app_pyqt5.py

# Mantieni il terminale aperto in caso di errori
if [ $? -ne 0 ]; then
    echo ""
    echo "Si è verificato un errore. Premi un tasto per chiudere..."
    read -n 1
fi
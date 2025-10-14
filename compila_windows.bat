@echo off
REM ====================================================================
REM Script di compilazione per Windows - Applicazione BRT
REM ====================================================================

echo.
echo ====================================================================
echo    Compilazione Applicazione Gestione Spedizioni BRT
echo ====================================================================
echo.

REM Controlla se Python e' installato
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRORE] Python non trovato!
    echo Installa Python da https://www.python.org/downloads/
    echo Assicurati di selezionare "Add Python to PATH" durante l'installazione
    pause
    exit /b 1
)

echo [1/4] Python trovato
python --version
echo.

REM Installa dipendenze necessarie
echo [2/5] Installazione dipendenze...
pip install PyQt5 requests pandas pyinstaller Pillow
if %errorlevel% neq 0 (
    echo [ERRORE] Errore durante l'installazione delle dipendenze
    pause
    exit /b 1
)
echo.

REM Converte PNG in ICO per l'icona Windows (se non esiste già)
echo [3/5] Verifica icona Windows...
if not exist "assets\igea_icon.ico" (
    echo Creazione icona Windows da PNG...
    python -c "from PIL import Image; img = Image.open('assets/igea_logo.png').convert('RGB'); img.save('assets/igea_icon.ico', format='ICO', sizes=[(256,256)])"
    if %errorlevel% neq 0 (
        echo [AVVISO] Impossibile creare l'icona .ico, compilazione senza icona
    )
) else (
    echo Icona Windows già presente in assets\igea_icon.ico
)
echo.

REM Pulisci compilazioni precedenti
echo [4/6] Pulizia compilazioni precedenti...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo NOTA: Mantengo il file .spec configurato (non lo cancello)
echo.

REM Compilazione con PyInstaller usando il file .spec configurato
echo [5/6] Compilazione applicazione in eseguibile Windows...
echo.
echo Uso il file Gestione_Spedizioni_BRT.spec configurato
echo Questo file include automaticamente la cartella assets/ con tutti i file necessari
echo.

pyinstaller --clean Gestione_Spedizioni_BRT.spec

if %errorlevel% neq 0 (
    echo [ERRORE] Errore durante la compilazione
    pause
    exit /b 1
)
echo.

REM Verifica che l'eseguibile sia stato creato
if exist "dist\Gestione_Spedizioni_BRT\Gestione_Spedizioni_BRT.exe" (
    echo [6/6] Compilazione completata con successo!
    echo.
    echo ====================================================================
    echo    COMPILAZIONE COMPLETATA
    echo ====================================================================
    echo.
    echo L'applicazione si trova in: dist\Gestione_Spedizioni_BRT\
    echo.
    echo L'eseguibile principale e': Gestione_Spedizioni_BRT.exe
    echo.
    echo IMPORTANTE: Devi distribuire l'intera cartella "Gestione_Spedizioni_BRT"
    echo (non solo l'exe) perche' contiene tutte le librerie necessarie.
    echo.
    echo Puoi creare un archivio ZIP della cartella per la distribuzione.
    echo.

    REM Apri la cartella dist
    explorer dist
) else (
    echo [ERRORE] Eseguibile non trovato in dist\Gestione_Spedizioni_BRT\
    pause
    exit /b 1
)

echo.
pause
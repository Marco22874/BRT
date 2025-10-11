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

REM Converte PNG in ICO per l'icona Windows
echo [3/5] Creazione icona Windows...
python -c "from PIL import Image; img = Image.open('igea_logo.png'); img.save('igea_logo.ico', format='ICO', sizes=[(256,256)])"
if %errorlevel% neq 0 (
    echo [AVVISO] Impossibile creare l'icona .ico, compilazione senza icona
)
echo.

REM Pulisci compilazioni precedenti
echo [4/6] Pulizia compilazioni precedenti...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "Gestione_Spedizioni_BRT.spec" del /q Gestione_Spedizioni_BRT.spec
echo.

REM Compilazione con PyInstaller
echo [5/6] Compilazione applicazione in eseguibile Windows...
echo.

REM Verifica se l'icona .ico esiste
if exist "igea_logo.ico" (
    echo Compilazione con icona igea_logo.ico
    pyinstaller --clean ^
        --onefile ^
        --windowed ^
        --name "Gestione_Spedizioni_BRT" ^
        --icon=igea_logo.ico ^
        --add-data "igea_logo.png;." ^
        --add-data "Logo_BRT.svg.png;." ^
        --hidden-import=PyQt5.sip ^
        --collect-all PyQt5 ^
        brt_app_pyqt5_win.py
) else (
    echo Compilazione senza icona
    pyinstaller --clean ^
        --onefile ^
        --windowed ^
        --name "Gestione_Spedizioni_BRT" ^
        --add-data "igea_logo.png;." ^
        --add-data "Logo_BRT.svg.png;." ^
        --hidden-import=PyQt5.sip ^
        --collect-all PyQt5 ^
        brt_app_pyqt5_win.py
)

if %errorlevel% neq 0 (
    echo [ERRORE] Errore durante la compilazione
    pause
    exit /b 1
)
echo.

REM Verifica che l'eseguibile sia stato creato
if exist "dist\Gestione_Spedizioni_BRT.exe" (
    echo [6/6] Compilazione completata con successo!
    echo.
    echo ====================================================================
    echo    COMPILAZIONE COMPLETATA
    echo ====================================================================
    echo.
    echo L'eseguibile si trova in: dist\Gestione_Spedizioni_BRT.exe
    echo.
    echo Puoi copiare questo file ovunque e utilizzarlo senza Python.
    echo.

    REM Apri la cartella dist
    explorer dist
) else (
    echo [ERRORE] Eseguibile non trovato in dist\
    pause
    exit /b 1
)

echo.
pause
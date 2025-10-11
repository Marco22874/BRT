================================================================================
    GUIDA COMPILAZIONE APPLICAZIONE BRT PER WINDOWS
================================================================================

PREREQUISITI SU WINDOWS
-----------------------

1. Python 3.8 o superiore
   Scarica da: https://www.python.org/downloads/
   IMPORTANTE: Durante l'installazione, seleziona "Add Python to PATH"

2. File necessari da portare su Windows:
   - brt_app_pyqt5_win.py (versione ottimizzata per Windows)
   - igea_logo.png
   - Logo_BRT.svg.png
   - compila_windows.bat
   - README_COMPILAZIONE.txt (questo file)

   ATTENZIONE: NON copiare le cartelle build/ o dist/ da macOS!
   Porta SOLO i file elencati sopra.

   NOTA: La versione _win.py include fix per la compatibilità con numpy/pandas su Windows.


PROCEDURA DI COMPILAZIONE
-------------------------

METODO AUTOMATICO (Consigliato):

1. Copia l'intera cartella BRT su Windows

2. Fai doppio click su: compila_windows.bat

3. Lo script eseguirà automaticamente:
   - Verifica della presenza di Python
   - Installazione delle dipendenze (PyQt5, pandas, pyinstaller, Pillow)
   - Conversione dell'icona PNG in formato ICO per Windows
   - Compilazione dell'applicazione in .exe con icona
   - Apertura della cartella con l'eseguibile

4. L'eseguibile finale sarà in: dist\Gestione_Spedizioni_BRT.exe


METODO MANUALE:

1. Apri il Prompt dei Comandi (CMD) nella cartella BRT

2. Installa le dipendenze:
   pip install PyQt5 requests pandas pyinstaller Pillow

3. Converti l'icona (opzionale):
   python -c "from PIL import Image; img = Image.open('igea_logo.png'); img.save('igea_logo.ico', format='ICO', sizes=[(256,256)])"

4. Compila l'applicazione:
   pyinstaller --clean --onefile --windowed --name "Gestione_Spedizioni_BRT" --icon=igea_logo.ico --add-data "igea_logo.png;." --add-data "Logo_BRT.svg.png;." --hidden-import=PyQt5.sip --collect-all PyQt5 brt_app_pyqt5_win.py

5. L'eseguibile sarà creato in: dist\Gestione_Spedizioni_BRT.exe


DISTRIBUZIONE
-------------

Una volta creato l'eseguibile:

- Puoi copiare SOLO il file Gestione_Spedizioni_BRT.exe su qualsiasi PC Windows
- NON serve Python installato sul PC di destinazione
- L'applicazione funzionerà autonomamente


RISOLUZIONE PROBLEMI
--------------------

Errore: "Python non trovato"
→ Reinstalla Python e assicurati di selezionare "Add Python to PATH"

Errore: "pip non riconosciuto"
→ Apri CMD come Amministratore e riprova

Errore: "Ordinale non trovato" o "Impossibile trovare l'ordinale 380"
→ Questo errore indica che hai copiato file .spec o cartelle build/dist da macOS
→ SOLUZIONE:
  1. Elimina le cartelle build/ e dist/
  2. Elimina eventuali file .spec
  3. Rilancia compila_windows.bat
→ Lo script batch aggiornato pulisce automaticamente questi file

Errore durante la compilazione:
→ Verifica che tutti i file (immagini logo) siano presenti nella cartella

L'exe non si avvia:
→ Controlla Windows Defender o antivirus (potrebbe bloccare l'eseguibile)
→ Prova a ricompilare senza --windowed per vedere eventuali errori nel terminale

IMPORTANTE:
- La compilazione DEVE essere fatta direttamente su Windows
- NON portare cartelle build/ o dist/ da macOS a Windows
- Porta SOLO i file sorgente (.py, .png, .bat)


SUPPORTO
--------

Per problemi o domande, contatta lo sviluppatore.

Data creazione: 2025-10-10
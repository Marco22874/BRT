# Applicazione Gestione Spedizioni BRT

## 📦 Descrizione

Questa applicazione automatizza la creazione del file CSV per il gestionale BRT partendo dal file esportato dal gestionale interno.

## 🚀 Come Avviare l'Applicazione

### Opzione 1: Da Terminale
```bash
cd /Users/marco/Documents/nwm-local
python3 brt_app_pyqt5.py
```

### Opzione 2: Script di avvio
Doppio click su `avvia_brt_app.command` (se creato)

## 📋 Come Usare l'Applicazione

### STEP 1: Carica File CSV
1. Clicca su **"Carica LISTADDT.csv"**
2. Seleziona il file esportato dal gestionale
3. L'app rimuoverà automaticamente i duplicati e mostrerà quante spedizioni uniche ha trovato

**Esempio risultato:**
```
✓ 48 spedizioni caricate (125 duplicati rimossi)
```

### STEP 2: Compila Dati Spedizione

Per ogni cliente l'applicazione mostra:

**Destinatario (da CSV):**
- Numero spedizione
- Ragione sociale
- Indirizzo completo
- CAP, città, provincia
- Telefono

**Dati da compilare:**
- **N. Colli**: Numero di colli della spedizione
- **Peso tot (kg)**: Peso totale in kilogrammi

#### Template Rapidi
Usa i bottoni per compilare velocemente:
- **1 collo - 5kg**: Inserisce automaticamente 1 collo e 5 kg
- **1 collo - 10kg**: Inserisce automaticamente 1 collo e 10 kg
- **2 colli - 15kg**: Inserisce automaticamente 2 colli e 15 kg

#### Scorciatoie da Tastiera
- **Enter** dopo il campo colli → passa al campo peso
- **Enter** dopo il campo peso → salva e passa al successivo
- **Ctrl+Enter** ovunque → salva e passa al successivo

#### Navigazione
- **◀ Precedente**: Torna alla spedizione precedente
- **Salta**: Salta questa spedizione (non verrà esportata)
- **Salva e Successivo ▶**: Salva i dati e passa alla prossima spedizione

#### Progress Bar
Mostra in tempo reale:
- Cliente corrente / totale
- Percentuale completamento
- Riepilogo: completati, da fare, saltati

**Esempio:**
```
Cliente 23/48 (48%)
COMPLETATI: 23 ✓  |  DA FARE: 22  |  SALTATI: 3
```

### STEP 3: Genera CSV per BRT

Quando hai completato tutte le spedizioni:

1. Clicca su **"💾 Esporta CSV per BRT"**
2. Scegli dove salvare il file (viene proposto un nome automatico: `spedizioni_BRT_YYYYMMDD_HHMMSS.csv`)
3. Il file è pronto per essere caricato sul gestionale BRT

**Il CSV esportato contiene:**
- Solo le spedizioni completate (non quelle saltate)
- Tutti i campi richiesti da BRT nel formato corretto
- Campi fissi già compilati (codice cliente, tariffa, ecc.)

## 💾 Salvataggio Automatico

L'applicazione salva automaticamente i dati compilati in:
```
/Users/marco/brt_spedizioni_data.json
```

**Vantaggi:**
- Puoi chiudere l'applicazione e riprendere dopo
- I dati compilati vengono mantenuti
- Se ricarichi lo stesso CSV, i dati precedenti vengono ripristinati

## 📊 Campi Fissi BRT (già configurati)

Questi valori sono già impostati nell'applicazione:

| Campo | Valore | Descrizione |
|-------|--------|-------------|
| VABATB | vuoto | Italia (blank) |
| VABCCM | 0091808 | Codice cliente BRT |
| VABCTR | 100 | Codice tariffa |
| VABTSP | C | Servizio Express |
| VABNAS | DISPOSITIVI MEDICI | Natura merce |
| VABRMA | IGEA SRL | Riferimento mittente |
| VABNZD | vuoto | Italia (blank) |

## 🔧 Mapping Campi CSV → BRT

Il file del gestionale viene trasformato automaticamente:

| Campo Gestionale | Campo BRT | Descrizione |
|-----------------|-----------|-------------|
| RegisNumero | VABNSP | Numero spedizione |
| RegisNumero | VABRMN | Riferimento numerico |
| SpedRagSoc1 | VABRSD | Ragione sociale destinatario |
| SpedIndirizzo | VABIND | Indirizzo destinatario |
| SpedLocalita | VABLOD | Località destinatario |
| SpedLocalita | VABCEL | Cellulare per SMS alert |
| SpedLocalita2 | VABTRC | Telefono referente |
| SpedCAP | VABCAD | CAP destinatario |
| SpedProvincia | VABPRD | Provincia destinatario |
| AccompCodPorto | VABCBO | Codice bolla (1=Franco, 2=Assegnato) |

## ❓ Risoluzione Problemi

### L'applicazione non si avvia
```bash
# Verifica che le librerie siano installate
pip3 install pandas PyQt5

# Se manca python3
brew install python3
```

### Errore "Colonne mancanti nel CSV"
Verifica che il file esportato dal gestionale contenga tutte le colonne necessarie:
- RegisNumero
- SpedRagSoc1
- SpedIndirizzo
- SpedLocalita
- SpedLocalita2
- SpedCAP
- SpedProvincia
- AccompCodPorto

### Il file esportato non viene accettato da BRT
1. Verifica che il CSV sia separato da `;` (punto e virgola)
2. Verifica che non ci sia l'intestazione (header)
3. Contatta il supporto BRT per verificare il tracciato

## 📞 Note Importanti

1. **Duplicati**: L'app rimuove automaticamente le righe duplicate basandosi sul campo `RegisNumero`
2. **Salvataggio**: I dati vengono salvati automaticamente dopo ogni operazione
3. **Skip**: Le spedizioni saltate non verranno esportate nel CSV finale
4. **Formato peso**: Può usare sia punto che virgola come separatore decimale (es: 5.5 o 5,5)

## 🔄 Workflow Consigliato

1. **Mattina**: Esporta LISTADDT.csv dal gestionale
2. **Durante il giorno**:
   - Prepara fisicamente i pacchi
   - Compila i dati nell'app (peso, colli)
   - Salva automaticamente
3. **Fine giornata**:
   - Verifica che tutte le spedizioni siano completate
   - Esporta CSV per BRT
   - Carica il CSV sul gestionale BRT

## 📈 Stima Tempo di Lavoro

**Prima (manuale):**
- Preparare pacco + compilare form sul sito: ~3-4 minuti/cliente
- 60 clienti = **3-4 ore**

**Con l'app:**
- Preparare pacco + inserire dati: ~1-2 minuti/cliente
- 60 clienti = **1-2 ore**
- **Risparmio: ~2 ore al giorno** ⚡

## 📝 Versione

- **Versione**: 1.0.0
- **Data**: 10 Ottobre 2025
- **Sviluppato per**: Gestione spedizioni BRT
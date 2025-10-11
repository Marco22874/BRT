# 📦 Applicazione Gestione Spedizioni BRT

## 🎯 Obiettivo

Automatizzare la creazione del file CSV per il gestionale BRT del corriere, partendo dal file esportato dal gestionale interno.

## 📁 File del Progetto

### File Principali

| File | Descrizione |
|------|-------------|
| **brt_app_pyqt5.py** | Applicazione principale con interfaccia grafica PyQt5 |
| **avvia_brt_app.command** | Script di avvio rapido (doppio click) |
| **ISTRUZIONI_BRT_APP.md** | Manuale d'uso completo |
| **README_BRT_APP.md** | Questo file |

### File di Supporto

| File | Descrizione |
|------|-------------|
| **test_trasformazione.py** | Script di test per verificare la trasformazione CSV |
| **brt_app_pyqt5.py** | Versione deprecata con tkinter (non funziona su macOS) |

### File Generati dall'Applicazione

| File | Posizione | Descrizione |
|------|-----------|-------------|
| **brt_spedizioni_data.json** | `~/` (Home) | Salvataggio automatico dei dati compilati |
| **spedizioni_BRT_*.csv** | A scelta dell'utente | CSV finale da caricare su BRT |

## 🚀 Avvio Rapido

### Prima volta - Installazione dipendenze
```bash
pip3 install pandas PyQt5
```

### Avvio Applicazione

**Metodo 1 - Doppio click:**
```
Doppio click su: avvia_brt_app.command
```

**Metodo 2 - Terminale:**
```bash
cd /Users/marco/Documents/nwm-local
python3 brt_app_pyqt5.py
```

## 📊 Flusso di Lavoro

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. ESPORTA da Gestionale                                        │
│    └─> LISTADDT.csv (172 righe con duplicati)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CARICA in Applicazione BRT                                   │
│    ├─> Rimozione duplicati automatica                          │
│    ├─> Mapping colonne automatico                              │
│    └─> 48 spedizioni uniche pronte                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. COMPILA Dati Spedizione (per ogni cliente)                  │
│    ├─> N. Colli (es: 1, 2, 3...)                              │
│    ├─> Peso kg (es: 5.5, 10, 15.3...)                         │
│    └─> Template rapidi per velocizzare                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. ESPORTA CSV per BRT                                          │
│    └─> spedizioni_BRT_20251010_153045.csv                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. CARICA su Gestionale BRT                                     │
│    └─> Upload manuale sul sito del corriere                    │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ Configurazione Campi Fissi

I seguenti valori sono già configurati nell'applicazione:

```python
VABCCM = '0091808'           # Codice cliente BRT
VABCTR = '100'               # Codice tariffa
VABTSP = 'C'                 # Servizio Express
VABNAS = 'DISPOSITIVI MEDICI' # Natura merce
VABRMA = 'IGEA SRL'          # Riferimento mittente
VABATB = ''                  # Italia (vuoto)
VABNZD = ''                  # Italia (vuoto)
```

Se questi valori dovessero cambiare, modifica il file `brt_app_pyqt5.py` alla riga 21.

## 📋 Requisiti Sistema

### Software Necessario
- **Python 3.x** (già installato su macOS)
- **pandas** (gestione CSV)
- **PyQt5** (interfaccia grafica)

### Compatibilità
- ✅ macOS (testato)
- ✅ Windows (compatibile, richiede Python installato)
- ✅ Linux (compatibile)

## 🔧 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'pandas'"
**Soluzione:**
```bash
pip3 install pandas
```

### Problema: "ModuleNotFoundError: No module named 'PyQt5'"
**Soluzione:**
```bash
pip3 install PyQt5
```

### Problema: "Permission denied" su avvia_brt_app.command
**Soluzione:**
```bash
chmod +x avvia_brt_app.command
```

### Problema: CSV non accettato da BRT
**Verifica:**
1. Separatore è `;` (punto e virgola)
2. Nessuna riga di intestazione
3. Formato colonne rispetta il tracciato BRT

## 📈 Performance

### Tempo Stimato per 60 Clienti

| Metodo | Tempo | Note |
|--------|-------|------|
| **Manuale** (sito BRT) | 3-4 ore | ~3-4 min/cliente |
| **Con Applicazione** | 1-2 ore | ~1-2 min/cliente |
| **Risparmio** | ~2 ore | 50% più veloce |

### Operazioni Automatizzate
- ✅ Rimozione duplicati
- ✅ Mapping campi gestionale → BRT
- ✅ Inserimento campi fissi
- ✅ Validazione dati
- ✅ Salvataggio automatico progressi
- ✅ Generazione CSV formato BRT

## 🆘 Supporto

Per problemi o domande:
1. Consulta [ISTRUZIONI_BRT_APP.md](ISTRUZIONI_BRT_APP.md)
2. Verifica la sezione Troubleshooting sopra
3. Testa con `test_trasformazione.py` per verificare la trasformazione

## 📝 Changelog

### Versione 1.0.0 (10/10/2025)
- ✅ Prima versione funzionante
- ✅ Interfaccia grafica PyQt5
- ✅ Caricamento CSV gestionale
- ✅ Rimozione duplicati automatica
- ✅ Compilazione assistita dati spedizione
- ✅ Template rapidi
- ✅ Salvataggio automatico progressi
- ✅ Esportazione CSV formato BRT
- ✅ Documentazione completa

## 📄 Licenza

Uso interno aziendale.

---

**Sviluppato per:** Gestione Spedizioni BRT
**Data:** Ottobre 2025
**Versione:** 1.0.0

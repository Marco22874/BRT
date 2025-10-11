#!/usr/bin/env python3
"""
Test trasformazione CSV per BRT
"""

import pandas as pd
from pathlib import Path

# Configurazione campi fissi BRT
CAMPI_FISSI = {
    'VABATB': '',  # vuoto per Italia
    'VABCCM': '0091808',  # Codice cliente
    'VABNAS': 'DISPOSITIVI MEDICI',  # Natura merce
    'VABRMA': 'IGEA SRL',  # Riferimento alfabetico
    'VABCTR': '100',  # Codice tariffa
    'VABNZD': '',  # vuoto per Italia
    'VABTSP': 'C',  # Servizio Express
}

def trasforma_csv(input_file):
    """Trasforma il CSV secondo le specifiche"""

    print(f"Caricamento file: {input_file}")

    # Leggi CSV
    df = pd.read_csv(input_file, sep=';', encoding='utf-8')
    print(f"✓ Lette {len(df)} righe")

    # Verifica colonne necessarie
    required_cols = ['RegisNumero', 'SpedRagSoc1', 'SpedIndirizzo',
                     'SpedLocalita', 'SpedLocalita2', 'SpedCAP',
                     'SpedProvincia', 'AccompCodPorto']

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Colonne mancanti: {', '.join(missing_cols)}")
        return None

    # Seleziona solo le colonne necessarie
    df = df[required_cols].copy()

    # Rimuovi duplicati basati su RegisNumero (prendi solo prima occorrenza)
    df_unique = df.drop_duplicates(subset=['RegisNumero'], keep='first')
    print(f"✓ Trovate {len(df_unique)} spedizioni uniche ({len(df) - len(df_unique)} duplicati rimossi)")

    # Rinomina colonne secondo mapping BRT
    df_unique = df_unique.rename(columns={
        'RegisNumero': 'VABNSP',
        'SpedRagSoc1': 'VABRSD',
        'SpedIndirizzo': 'VABIND',
        'SpedLocalita': 'VABLOD',
        'SpedLocalita2': 'VABTRC',  # Telefono
        'SpedCAP': 'VABCAD',
        'SpedProvincia': 'VABPRD',
        'AccompCodPorto': 'VABCBO'
    })

    # Duplica VABNSP per VABRMN
    df_unique['VABRMN'] = df_unique['VABNSP']

    # Duplica VABLOD per VABCEL (cellulare)
    df_unique['VABCEL'] = df_unique['VABLOD']

    # Aggiungi colonne per dati da compilare
    df_unique['VABNCL'] = ''  # N. Colli
    df_unique['VABPKB'] = ''  # Peso

    # Aggiungi campi fissi
    for campo, valore in CAMPI_FISSI.items():
        df_unique[campo] = valore

    print("✓ Trasformazione completata")

    # Mostra prime 3 righe
    print("\nPrime 3 spedizioni:")
    print("=" * 80)
    for idx, row in df_unique.head(3).iterrows():
        print(f"\nSpedizione {idx + 1}:")
        print(f"  N. Spedizione: {row['VABNSP']}")
        print(f"  Destinatario:  {row['VABRSD']}")
        print(f"  Indirizzo:     {row['VABIND']}")
        print(f"  CAP/Città:     {row['VABCAD']} {row['VABLOD']}")
        print(f"  Provincia:     {row['VABPRD']}")

    return df_unique

def main():
    """Funzione principale"""

    # File di input
    input_file = Path.home() / "Documents" / "LISTADDT.csv"

    if not input_file.exists():
        print(f"❌ File non trovato: {input_file}")
        return

    # Trasforma
    df_trasformato = trasforma_csv(input_file)

    if df_trasformato is not None:
        # Salva file intermedio per verifica
        output_file = Path.home() / "Documents" / "LISTADDT_trasformato.csv"
        df_trasformato.to_csv(output_file, sep=';', index=False, encoding='utf-8')
        print(f"\n✓ File trasformato salvato in: {output_file}")
        print(f"\nPuoi aprirlo con Excel per verificare la struttura")
        print(f"Colonne presenti: {list(df_trasformato.columns)}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Script di verifica CSV BRT
Controlla che il file esportato sia corretto
"""

import sys
from pathlib import Path


def verifica_csv_brt(file_path):
    """Verifica la correttezza del CSV BRT"""

    print(f"\n{'='*70}")
    print(f"VERIFICA CSV BRT: {Path(file_path).name}")
    print(f"{'='*70}\n")

    # Leggi file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Errore lettura file: {e}")
        return False

    print(f"✓ File letto correttamente")
    print(f"✓ Numero righe: {len(lines)}\n")

    # Verifica formato
    errori = []
    warnings = []

    for idx, line in enumerate(lines, 1):
        # Rimuovi newline
        line = line.rstrip('\n\r')

        # Splitta per punto e virgola
        fields = line.split(';')

        # Verifica numero colonne (almeno 19)
        if len(fields) < 19:
            errori.append(f"Riga {idx}: Colonne insufficienti ({len(fields)}/19)")
            continue

        # Verifica campi obbligatori
        # VABCCM (pos 1) - Codice cliente
        if not fields[1]:
            errori.append(f"Riga {idx}: VABCCM (codice cliente) vuoto")

        # VABNSP (pos 2) - Numero spedizione
        if not fields[2]:
            errori.append(f"Riga {idx}: VABNSP (numero spedizione) vuoto")

        # VABCBO (pos 3) - Codice bolla
        if not fields[3]:
            errori.append(f"Riga {idx}: VABCBO (codice bolla) vuoto")
        elif fields[3] not in ['1', '2', '4', '6']:
            warnings.append(f"Riga {idx}: VABCBO '{fields[3]}' non standard (valori: 1,2,4,6)")

        # VABRSD (pos 4) - Ragione sociale destinatario
        if not fields[4]:
            errori.append(f"Riga {idx}: VABRSD (destinatario) vuoto")

        # VABIND (pos 5) - Indirizzo
        if not fields[5]:
            errori.append(f"Riga {idx}: VABIND (indirizzo) vuoto")

        # VABCAD (pos 6) - CAP
        if not fields[6]:
            errori.append(f"Riga {idx}: VABCAD (CAP) vuoto")

        # VABLOD (pos 7) - Località
        if not fields[7]:
            errori.append(f"Riga {idx}: VABLOD (località) vuoto")

        # VABPRD (pos 8) - Provincia
        if not fields[8]:
            errori.append(f"Riga {idx}: VABPRD (provincia) vuoto")

        # VABNCL (pos 13) - Numero colli
        if not fields[13]:
            errori.append(f"Riga {idx}: VABNCL (numero colli) vuoto")
        else:
            try:
                colli = int(fields[13])
                if colli <= 0:
                    errori.append(f"Riga {idx}: VABNCL deve essere > 0")
            except ValueError:
                errori.append(f"Riga {idx}: VABNCL '{fields[13]}' non è un numero")

        # VABPKB (pos 14) - Peso
        if not fields[14]:
            errori.append(f"Riga {idx}: VABPKB (peso) vuoto")
        else:
            try:
                peso = float(fields[14])
                if peso <= 0:
                    errori.append(f"Riga {idx}: VABPKB deve essere > 0")
            except ValueError:
                errori.append(f"Riga {idx}: VABPKB '{fields[14]}' non è un numero")

    # Report
    print(f"{'─'*70}")
    print(f"RISULTATI VERIFICA")
    print(f"{'─'*70}\n")

    if not errori and not warnings:
        print("✅ CSV VALIDO - Nessun errore trovato!")
        print(f"\nIl file è pronto per essere caricato su BRT.")
        return True
    else:
        if errori:
            print(f"❌ TROVATI {len(errori)} ERRORI:\n")
            for err in errori[:10]:  # Mostra max 10
                print(f"  • {err}")
            if len(errori) > 10:
                print(f"  ... e altri {len(errori) - 10} errori")

        if warnings:
            print(f"\n⚠️  TROVATI {len(warnings)} AVVISI:\n")
            for warn in warnings[:10]:  # Mostra max 10
                print(f"  • {warn}")
            if len(warnings) > 10:
                print(f"  ... e altri {len(warnings) - 10} avvisi")

        print(f"\n{'─'*70}")
        if errori:
            print("❌ Correggi gli errori prima di caricare il file su BRT")
            return False
        else:
            print("⚠️  Il file ha degli avvisi ma potrebbe funzionare")
            return True


def main():
    """Funzione principale"""

    if len(sys.argv) < 2:
        print("\nUso: python3 verifica_csv_brt.py <file.csv>\n")
        print("Esempio:")
        print("  python3 verifica_csv_brt.py spedizioni_BRT_20251010_153045.csv\n")
        return

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"\n❌ File non trovato: {file_path}\n")
        return

    # Verifica
    verifica_csv_brt(file_path)
    print()


if __name__ == '__main__':
    main()
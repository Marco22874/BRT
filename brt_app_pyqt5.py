#!/usr/bin/env python3
"""
Applicazione per Gestione Spedizioni BRT - PyQt5
Converte il file LISTADDT.csv nel formato richiesto da BRT
"""

__version__ = "2.11.0"
__app_name__ = "Gestione Spedizioni IGEA <-> BRT"
__release_date__ = "2025-10-11"
__developer__ = "Marco De Luca"

import sys
import platform
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import urllib.request
import urllib.error
import webbrowser
import subprocess
import shutil
import os
import time
import zipfile

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton, QLineEdit,
                              QTextEdit, QProgressBar, QFileDialog, QMessageBox,
                              QGroupBox, QGridLayout, QStackedWidget, QMenuBar, QAction, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon


def get_monospace_font():
    """
    Restituisce il font monospaced appropriato in base al sistema operativo
    per evitare warning su font mancanti
    """
    system = platform.system()

    if system == "Windows":
        return "Courier New"
    elif system == "Darwin":  # macOS
        return "Monaco"
    else:  # Linux e altri
        return "Monospace"


# Cache del font monospaced per uso globale
MONOSPACE_FONT = get_monospace_font()


class UpdateDownloader(QThread):
    """Thread per scaricare l'aggiornamento"""
    download_progress = pyqtSignal(int)  # Percentuale download
    download_complete = pyqtSignal(str)  # Path del file scaricato
    download_failed = pyqtSignal(str)  # Messaggio di errore

    def __init__(self, download_url, filename, download_path):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        self.download_path = download_path

    def run(self):
        """Scarica il file"""
        try:
            file_path = Path(self.download_path) / self.filename

            # Scarica con progress
            req = urllib.request.Request(self.download_url)
            req.add_header('User-Agent', 'BRT-Spedizioni-App')

            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192

                with open(file_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.download_progress.emit(progress)

            self.download_complete.emit(str(file_path))

        except Exception as e:
            self.download_failed.emit(str(e))


class UpdateChecker(QThread):
    """Thread per controllare aggiornamenti su GitHub"""
    update_available = pyqtSignal(str, str, str)  # (nuova_versione, url_release, download_url)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.github_repo = "Marco22874/BRT"

    def run(self):
        """Controlla se c'è una nuova versione su GitHub"""
        try:
            # Chiamata API GitHub per ottenere l'ultima release
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'BRT-Spedizioni-App')

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())

            latest_version = data.get('tag_name', '').lstrip('v')
            release_url = data.get('html_url', '')

            # Trova il file giusto per la piattaforma corrente
            download_url = self._get_platform_download_url(data.get('assets', []))

            # Confronta versioni
            if latest_version and self._is_newer_version(latest_version):
                self.update_available.emit(latest_version, release_url, download_url)

        except Exception as e:
            # Ignora errori di rete silenziosamente
            print(f"Update check failed: {e}")

    def _get_platform_download_url(self, assets):
        """Trova l'URL di download corretto per la piattaforma"""
        system = platform.system()

        for asset in assets:
            name = asset.get('name', '')
            name_lower = name.lower()

            if system == 'Windows':
                # Cerca file con _win o windows nel nome
                if ('_win' in name_lower or 'windows' in name_lower) and name_lower.endswith('.zip'):
                    return asset.get('browser_download_url', '')
            elif system == 'Darwin':
                # Cerca file senza _win/windows (quindi è per macOS)
                if name_lower.endswith('.zip') and '_win' not in name_lower and 'windows' not in name_lower:
                    return asset.get('browser_download_url', '')

        return ''

    def _is_newer_version(self, latest):
        """Confronta le versioni (formato: X.Y.Z)"""
        try:
            current_parts = [int(x) for x in self.current_version.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]

            # Confronta major, minor, patch
            for curr, lat in zip(current_parts, latest_parts):
                if lat > curr:
                    return True
                elif lat < curr:
                    return False

            return False
        except:
            return False


class BRTSpedizioniApp(QMainWindow):
    """Applicazione principale per gestione spedizioni BRT"""

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

    def __init__(self):
        super().__init__()

        # Variabili
        self.df_spedizioni = None
        self.current_index = 0
        # Salva il JSON nella stessa cartella dell'applicazione
        self.save_file = Path(__file__).parent / "brt_spedizioni_data.json"
        self.settings_file = Path(__file__).parent / "brt_settings.json"
        # Modalità navigazione saltati
        self.skip_navigation_mode = False

        # Impostazioni di default
        self.default_colli = 1
        self.default_peso = 2

        # Carica impostazioni salvate
        self.load_settings()

        # Inizializza interfaccia
        self.init_ui()

        # Carica dati salvati se esistono
        self.load_saved_data()

        # Avvia check aggiornamenti (in background)
        self.check_for_updates()

    def init_ui(self):
        """Inizializza l'interfaccia utente"""

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setGeometry(100, 100, 900, 800)

        # Imposta icona applicazione (logo IGEA)
        icon_path = Path(__file__).parent / "igea_logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Crea menu bar
        self.create_menu_bar()

        # Crea stacked widget per cambiare tra schermata principale e impostazioni
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Crea le due schermate
        self.main_screen = self.create_main_screen()
        self.settings_screen = self.create_settings_screen()

        # Aggiungi le schermate allo stack
        self.stacked_widget.addWidget(self.main_screen)
        self.stacked_widget.addWidget(self.settings_screen)

        # Mostra schermata principale
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def create_menu_bar(self):
        """Crea la barra dei menu"""
        menubar = self.menuBar()

        # Menu File
        file_menu = menubar.addMenu('File')

        # Azione Impostazioni
        settings_action = QAction('Impostazioni', self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        # Menu Info
        info_menu = menubar.addMenu('Info')

        # Azione Info
        about_action = QAction('Informazioni', self)
        about_action.triggered.connect(self.show_about_dialog)
        info_menu.addAction(about_action)

    def create_main_screen(self):
        """Crea la schermata principale"""
        # Widget per la schermata principale
        main_widget = QWidget()

        # Layout principale
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # Spazio ridotto tra elementi principali
        main_layout.setContentsMargins(10, 20, 10, 10)  # Margine superiore per distanziare i loghi dal bordo
        main_widget.setLayout(main_layout)

        # === HEADER: Loghi ===
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)

        # Logo IGEA (sinistra)
        igea_logo_label = QLabel()
        igea_logo_label.setAlignment(Qt.AlignCenter)
        icon_path = Path(__file__).parent / "igea_logo.png"
        igea_pixmap = QPixmap(str(icon_path))
        if not igea_pixmap.isNull():
            igea_logo_label.setPixmap(igea_pixmap.scaledToHeight(80, Qt.SmoothTransformation))
        header_layout.addWidget(igea_logo_label)

        # Frecce centrali (HTML per controllare line-height)
        arrows_label = QLabel('<div style="line-height: 80%;">→<br>←</div>')
        arrows_label.setAlignment(Qt.AlignCenter)
        arrows_font = QFont()
        arrows_font.setPointSize(24)
        arrows_font.setBold(True)
        arrows_label.setFont(arrows_font)
        arrows_label.setStyleSheet("color: #666666; padding: 0px 20px;")
        header_layout.addWidget(arrows_label)

        # Logo BRT (destra)
        brt_logo_label = QLabel()
        brt_logo_label.setAlignment(Qt.AlignCenter)
        brt_logo_path = Path(__file__).parent / "Logo_BRT.svg.png"
        if brt_logo_path.exists():
            brt_pixmap = QPixmap(str(brt_logo_path))
            if not brt_pixmap.isNull():
                brt_logo_label.setPixmap(brt_pixmap.scaledToHeight(80, Qt.SmoothTransformation))
        header_layout.addWidget(brt_logo_label)

        main_layout.addLayout(header_layout)

        # === STEP 1: Caricamento file ===
        step1_title = QLabel("STEP 1: Carica File CSV")
        step1_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px; margin-bottom: 8px;")
        main_layout.addWidget(step1_title)

        step1_group = QGroupBox()
        step1_layout = QHBoxLayout()
        step1_layout.setContentsMargins(10, 10, 10, 15)

        self.file_label = QLabel("Nessun file caricato")
        step1_layout.addWidget(self.file_label)

        step1_layout.addStretch()

        load_btn = QPushButton("Carica file .csv")
        load_btn.clicked.connect(self.load_csv)
        step1_layout.addWidget(load_btn)

        step1_group.setLayout(step1_layout)
        main_layout.addWidget(step1_group)

        # Info label separato (fuori dal group box)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: green; font-weight: bold;")
        main_layout.addWidget(self.info_label)

        # === STEP 2: Compilazione dati ===
        step2_title = QLabel("STEP 2: Compila Dati Spedizione")
        step2_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 0px; margin-bottom: 8px;")
        main_layout.addWidget(step2_title)

        step2_group = QGroupBox()
        step2_layout = QVBoxLayout()

        # Layout a 2 colonne per destinatario e dati spedizione
        columns_layout = QHBoxLayout()

        # === COLONNA SINISTRA: Destinatario ===
        left_column = QVBoxLayout()

        dest_title = QLabel("Destinatario (da CSV)")
        dest_title.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        left_column.addWidget(dest_title)

        dest_group = QGroupBox()
        dest_layout = QVBoxLayout()

        self.dest_text = QTextEdit()
        self.dest_text.setReadOnly(True)
        self.dest_text.setFixedHeight(150)
        self.dest_text.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        font = QFont(get_monospace_font(), 10)
        self.dest_text.setFont(font)
        dest_layout.addWidget(self.dest_text)

        dest_group.setLayout(dest_layout)
        left_column.addWidget(dest_group)

        columns_layout.addLayout(left_column)

        # === COLONNA DESTRA: Dati Spedizione ===
        right_column = QVBoxLayout()

        sped_title = QLabel("Dati Spedizione (da compilare)")
        sped_title.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        right_column.addWidget(sped_title)

        sped_group = QGroupBox()
        sped_layout = QGridLayout()

        # N. Colli
        sped_layout.addWidget(QLabel("N. Colli:"), 0, 0)
        self.colli_input = QLineEdit(str(self.default_colli))
        self.colli_input.setMaximumWidth(100)
        self.colli_input.returnPressed.connect(lambda: self.peso_input.setFocus())
        sped_layout.addWidget(self.colli_input, 0, 1)

        # Peso
        sped_layout.addWidget(QLabel("Peso tot (kg):"), 1, 0)
        self.peso_input = QLineEdit(str(self.default_peso))
        self.peso_input.setMaximumWidth(100)
        self.peso_input.returnPressed.connect(self.save_and_next)
        sped_layout.addWidget(self.peso_input, 1, 1)

        # Template rapidi
        template_label = QLabel("Template rapidi:")
        sped_layout.addWidget(template_label, 2, 0)

        template_row = QVBoxLayout()

        btn1 = QPushButton("1 collo - 5kg")
        btn1.clicked.connect(lambda: self.apply_template(1, 5))
        template_row.addWidget(btn1)

        btn2 = QPushButton("1 collo - 10kg")
        btn2.clicked.connect(lambda: self.apply_template(1, 10))
        template_row.addWidget(btn2)

        btn3 = QPushButton("2 colli - 15kg")
        btn3.clicked.connect(lambda: self.apply_template(2, 15))
        template_row.addWidget(btn3)

        sped_layout.addLayout(template_row, 2, 1)

        sped_group.setLayout(sped_layout)
        right_column.addWidget(sped_group)

        columns_layout.addLayout(right_column)

        step2_layout.addLayout(columns_layout)

        # Progress
        self.progress_label = QLabel("0/0 (0%)")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        step2_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        step2_layout.addWidget(self.progress_bar)

        # Riepilogo
        self.summary_label = QLabel("")
        self.summary_label.setAlignment(Qt.AlignCenter)
        step2_layout.addWidget(self.summary_label)

        # Bottoni navigazione
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Precedente")
        self.prev_btn.clicked.connect(self.previous_item)
        self.prev_btn.setStyleSheet("border: none; padding: 8px 15px; border-radius: 4px;")
        nav_layout.addWidget(self.prev_btn)

        self.skip_btn = QPushButton("Salta")
        self.skip_btn.clicked.connect(self.skip_item)
        self.skip_btn.setStyleSheet("border: none; padding: 8px 15px; border-radius: 4px;")
        nav_layout.addWidget(self.skip_btn)

        self.goto_skipped_btn = QPushButton("↻ Vai a Saltati")
        self.goto_skipped_btn.clicked.connect(self.goto_next_skipped)
        self.goto_skipped_btn.setStyleSheet("background-color: #FFA500; color: white; font-weight: bold; border: none; padding: 8px 15px; border-radius: 4px;")
        nav_layout.addWidget(self.goto_skipped_btn)

        self.save_next_btn = QPushButton("✓ SALVA E SUCCESSIVO ▶")
        self.save_next_btn.clicked.connect(self.save_and_next_unified)
        self.save_next_btn.setStyleSheet("background-color: #16FEBC; color: #333333; font-weight: bold; border: none; padding: 8px 15px; border-radius: 4px;")
        nav_layout.addWidget(self.save_next_btn)

        step2_layout.addLayout(nav_layout)

        step2_group.setLayout(step2_layout)
        main_layout.addWidget(step2_group)

        # === STEP 3: Esportazione ===
        step3_title = QLabel("STEP 3: Genera CSV per BRT")
        step3_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px; margin-bottom: 8px;")
        main_layout.addWidget(step3_title)

        step3_group = QGroupBox()
        step3_layout = QHBoxLayout()
        step3_layout.setContentsMargins(10, 10, 10, 15)

        step3_layout.addStretch()  # Spazio per centrare il pulsante

        self.export_btn = QPushButton("↑ Esporta CSV per BRT")
        self.export_btn.clicked.connect(self.export_brt_csv)
        self.export_btn.setStyleSheet("background-color: #5F38E6; color: white; font-weight: bold; border: none; padding: 10px; border-radius: 4px;")  # Viola
        step3_layout.addWidget(self.export_btn)

        step3_layout.addStretch()  # Spazio per centrare il pulsante

        step3_group.setLayout(step3_layout)
        main_layout.addWidget(step3_group)

        # Export label separato (fuori dal group box)
        self.export_label = QLabel("")
        self.export_label.setStyleSheet("color: green; font-weight: bold;")
        self.export_label.setWordWrap(True)
        main_layout.addWidget(self.export_label)

        return main_widget

    def create_settings_screen(self):
        """Crea la schermata impostazioni"""
        settings_widget = QWidget()

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        settings_widget.setLayout(layout)

        # Titolo
        title = QLabel("IMPOSTAZIONI")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Group box per valori di default
        defaults_group = QGroupBox("Valori di Default")
        defaults_group.setStyleSheet("font-size: 14px; font-weight: bold;")
        defaults_layout = QGridLayout()
        defaults_layout.setSpacing(15)

        # N. Colli default
        defaults_layout.addWidget(QLabel("N. Colli di default:"), 0, 0)
        self.settings_colli_input = QLineEdit(str(self.default_colli))
        self.settings_colli_input.setMaximumWidth(150)
        defaults_layout.addWidget(self.settings_colli_input, 0, 1)

        # Peso default
        defaults_layout.addWidget(QLabel("Peso di default (kg):"), 1, 0)
        self.settings_peso_input = QLineEdit(str(self.default_peso))
        self.settings_peso_input.setMaximumWidth(150)
        defaults_layout.addWidget(self.settings_peso_input, 1, 1)

        defaults_group.setLayout(defaults_layout)
        layout.addWidget(defaults_group)

        # Spazio
        layout.addStretch()

        # Bottoni
        buttons_layout = QHBoxLayout()

        # Bottone Torna Indietro
        back_btn = QPushButton("← Torna Indietro")
        back_btn.clicked.connect(self.show_main_screen)
        back_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; border: none; padding: 10px 20px; border-radius: 4px;")
        buttons_layout.addWidget(back_btn)

        buttons_layout.addStretch()

        # Bottone Salva
        save_btn = QPushButton("✓ Salva Impostazioni")
        save_btn.clicked.connect(self.save_settings_and_return)
        save_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; border: none; padding: 10px 20px; border-radius: 4px;")
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        return settings_widget

    def show_settings(self):
        """Mostra la schermata impostazioni"""
        # Aggiorna i valori negli input delle impostazioni
        self.settings_colli_input.setText(str(self.default_colli))
        self.settings_peso_input.setText(str(self.default_peso))
        self.stacked_widget.setCurrentWidget(self.settings_screen)

    def show_main_screen(self):
        """Mostra la schermata principale"""
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def show_about_dialog(self):
        """Mostra il dialog con le informazioni sull'applicazione"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Informazioni")
        dialog.setMinimumWidth(500)

        # Layout principale
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header con loghi e frecce
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        # Logo IGEA (sinistra)
        igea_logo = QLabel()
        igea_path = Path(__file__).parent / "igea_logo.png"
        if igea_path.exists():
            pixmap_igea = QPixmap(str(igea_path))
            scaled_igea = pixmap_igea.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            igea_logo.setPixmap(scaled_igea)
        header_layout.addWidget(igea_logo)

        # Frecce al centro
        arrows_label = QLabel("→\n←")
        arrows_label.setFont(QFont("Arial", 32))
        arrows_label.setAlignment(Qt.AlignCenter)
        arrows_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(arrows_label)

        # Logo BRT (destra)
        brt_logo = QLabel()
        brt_path = Path(__file__).parent / "Logo_BRT.svg.png"
        if brt_path.exists():
            pixmap_brt = QPixmap(str(brt_path))
            scaled_brt = pixmap_brt.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            brt_logo.setPixmap(scaled_brt)
        header_layout.addWidget(brt_logo)

        main_layout.addLayout(header_layout)

        # Informazioni app
        info_text = f"""
<div style='text-align: center;'>
<h2>{__app_name__}</h2>
<p><b>Versione:</b> {__version__}</p>
<p><b>Data di rilascio:</b> {__release_date__}</p>
<br>
<p><b>Sviluppato da:</b> {__developer__}</p>
</div>
        """

        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        # Bottone OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        ok_button.setMinimumWidth(100)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        dialog.setLayout(main_layout)

        # Imposta icona finestra se disponibile
        if igea_path.exists():
            dialog.setWindowIcon(QIcon(str(igea_path)))

        dialog.exec_()

    def save_settings_and_return(self):
        """Salva le impostazioni e torna alla schermata principale"""
        try:
            # Valida input
            colli = int(self.settings_colli_input.text().strip())
            peso = float(self.settings_peso_input.text().strip().replace(',', '.'))

            if colli <= 0 or peso <= 0:
                QMessageBox.warning(self, "Attenzione",
                    "I valori devono essere maggiori di zero")
                return

            # Salva i nuovi valori di default
            self.default_colli = colli
            self.default_peso = peso

            # Salva su file
            settings_data = {
                'default_colli': self.default_colli,
                'default_peso': self.default_peso
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)

            QMessageBox.information(self, "Successo",
                "Impostazioni salvate con successo!")

            # Torna alla schermata principale
            self.show_main_screen()

        except ValueError:
            QMessageBox.warning(self, "Attenzione",
                "Valori non validi. Inserire numeri validi.")

    def load_settings(self):
        """Carica le impostazioni salvate"""
        if not self.settings_file.exists():
            return

        try:
            with open(self.settings_file, 'r') as f:
                settings_data = json.load(f)

            self.default_colli = settings_data.get('default_colli', 1)
            self.default_peso = settings_data.get('default_peso', 2)

        except Exception as e:
            print(f"Errore nel caricamento delle impostazioni: {e}")

    def check_for_updates(self):
        """Avvia il controllo aggiornamenti in background"""
        self.update_checker = UpdateChecker(__version__)
        self.update_checker.update_available.connect(self.show_update_dialog)
        self.update_checker.start()

    def show_update_dialog(self, new_version, release_url, download_url):
        """Mostra il dialog di aggiornamento disponibile"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Aggiornamento Disponibile")
        msg.setIcon(QMessageBox.Information)

        text = f"""
<div style='text-align: center;'>
<h3>Nuova versione disponibile!</h3>
<p>È disponibile la versione <b>{new_version}</b></p>
<p>Versione attuale: <b>{__version__}</b></p>
<br>
<p>Vuoi scaricare l'aggiornamento?</p>
</div>
        """
        msg.setText(text)
        msg.setTextFormat(Qt.RichText)

        # Bottoni
        download_btn = msg.addButton("Scarica Ora", QMessageBox.AcceptRole)
        later_btn = msg.addButton("Ricordamelo dopo", QMessageBox.RejectRole)

        # Imposta icona personalizzata
        icon_path = Path(__file__).parent / "igea_logo.png"
        if icon_path.exists():
            msg.setWindowIcon(QIcon(str(icon_path)))

        msg.exec_()

        # Se ha cliccato su Scarica
        if msg.clickedButton() == download_btn:
            if download_url:
                self.start_download(download_url)
            else:
                # Fallback: apri la pagina GitHub
                webbrowser.open(release_url)

    def start_download(self, download_url):
        """Avvia il download dell'aggiornamento"""
        # Determina il nome del file dall'URL
        filename = download_url.split('/')[-1]

        # Percorso dove scaricare (cartella parent dell'app per evitare conflitti)
        if getattr(sys, 'frozen', False):
            # Se è un eseguibile PyInstaller (--onedir su Windows)
            # sys.executable = Desktop/Gestione_Spedizioni_BRT/Gestione_Spedizioni_BRT.exe
            # Dobbiamo scaricare nel Desktop (parent della cartella app)
            app_dir = Path(sys.executable).parent.parent
        else:
            # Se è uno script Python
            app_dir = Path(__file__).parent

        # Crea dialog con progress bar
        self.download_dialog = QMessageBox(self)
        self.download_dialog.setWindowTitle("Download in corso")
        self.download_dialog.setText(f"Download di {filename} in corso...\n\nL'applicazione verrà chiusa e aggiornata automaticamente.")
        self.download_dialog.setStandardButtons(QMessageBox.NoButton)

        # Aggiungi progress bar al dialog
        self.download_progress = QProgressBar()
        self.download_progress.setMinimum(0)
        self.download_progress.setMaximum(100)
        self.download_progress.setValue(0)

        # Layout custom per il dialog
        layout = self.download_dialog.layout()
        layout.addWidget(self.download_progress, layout.rowCount(), 0, 1, layout.columnCount())

        # Avvia il downloader
        self.downloader = UpdateDownloader(download_url, filename, str(app_dir))
        self.downloader.download_progress.connect(self.on_download_progress)
        self.downloader.download_complete.connect(self.on_download_complete)
        self.downloader.download_failed.connect(self.on_download_failed)
        self.downloader.start()

        # Mostra il dialog
        self.download_dialog.show()

    def on_download_progress(self, progress):
        """Aggiorna la progress bar del download"""
        self.download_progress.setValue(progress)

    def on_download_complete(self, file_path):
        """Download completato - installa e riavvia"""
        self.download_dialog.close()

        try:
            self.install_update(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Errore Installazione",
                f"Impossibile installare l'aggiornamento:\n\n{e}\n\nIl file è stato salvato in:\n{file_path}")

    def install_update(self, downloaded_file):
        """Installa l'aggiornamento e riavvia l'applicazione"""
        downloaded_path = Path(downloaded_file)
        system = platform.system()

        if getattr(sys, 'frozen', False):
            # Eseguibile PyInstaller
            current_exe = Path(sys.executable)
            app_dir = current_exe.parent
        else:
            # Script Python (modalità sviluppo)
            current_exe = Path(__file__)
            app_dir = current_exe.parent

        if system == 'Windows':
            # Windows: sostituisci .exe
            self.install_windows_update(downloaded_path, current_exe, app_dir)
        elif system == 'Darwin':
            # macOS: estrai .zip e sostituisci .app
            self.install_macos_update(downloaded_path, current_exe, app_dir)

    def install_windows_update(self, downloaded_path, current_exe, app_dir):
        """Installa aggiornamento su Windows"""
        # Determina la cartella dell'app corrente e la parent
        if getattr(sys, 'frozen', False):
            # Se siamo nell'eseguibile PyInstaller (modalità --onedir)
            # sys.executable punta a Gestione_Spedizioni_BRT/Gestione_Spedizioni_BRT.exe
            current_app_folder = current_exe.parent
            parent_dir = current_app_folder.parent
        else:
            # Modalità sviluppo
            current_app_folder = app_dir / "Gestione_Spedizioni_BRT"
            parent_dir = app_dir

        # Estrai il contenuto dello zip nella cartella parent
        extract_dir = parent_dir / "temp_update"
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(downloaded_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Trova la cartella dell'applicazione nel contenuto estratto
        new_app_folder = None
        for item in extract_dir.iterdir():
            if item.is_dir():
                # Verifica che contenga un exe
                exe_files = list(item.glob("*.exe"))
                if exe_files:
                    new_app_folder = item
                    break

        if not new_app_folder:
            raise Exception("Cartella applicazione non trovata nell'archivio")

        # Nome per il backup
        backup_folder = parent_dir / (current_app_folder.name + "_old")

        # Crea script batch per sostituire la cartella dopo la chiusura
        update_script = parent_dir / "update_brt.bat"

        script_content = f"""@echo off
echo Attendere chiusura applicazione...
timeout /t 3 /nobreak > nul

:retry
tasklist /FI "IMAGENAME eq {current_exe.name}" 2>NUL | find /I /N "{current_exe.name}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto retry
)

echo Aggiornamento in corso...
if exist "{backup_folder}" rmdir /s /q "{backup_folder}"
if exist "{current_app_folder}" ren "{current_app_folder}" "{backup_folder.name}"
move /Y "{new_app_folder}" "{current_app_folder}"

if exist "{current_app_folder}" (
    echo Avvio nuova versione...
    start "" "{current_app_folder}\\{current_exe.name}"
    timeout /t 2 /nobreak > nul
    if exist "{backup_folder}" rmdir /s /q "{backup_folder}"
    rmdir /s /q "{extract_dir}"
    del /F /Q "{downloaded_path}"
) else (
    echo Errore: ripristino versione precedente
    if exist "{backup_folder}" ren "{backup_folder}" "{current_app_folder.name}"
)

del "%~f0"
"""

        with open(update_script, 'w') as f:
            f.write(script_content)

        # Avvia lo script e chiudi l'applicazione
        subprocess.Popen(['cmd', '/c', str(update_script)],
                        creationflags=subprocess.CREATE_NO_WINDOW)

        QApplication.quit()

    def install_macos_update(self, downloaded_path, current_exe, app_dir):
        """Installa aggiornamento su macOS"""
        # Estrai il contenuto dello zip
        extract_dir = app_dir / "temp_update"
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(downloaded_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Trova la nuova app nel contenuto estratto
        new_app = None
        for item in extract_dir.iterdir():
            if item.suffix == '.app':
                new_app = item
                break

        if not new_app:
            raise Exception("File .app non trovato nell'archivio")

        # Determina il percorso dell'app corrente
        if getattr(sys, 'frozen', False):
            # Se siamo nell'app bundle (.app/Contents/MacOS/executable)
            current_app = current_exe.parent.parent.parent
        else:
            # Modalità sviluppo
            current_app = app_dir / "brt_app_pyqt5.app"

        # Crea script shell per sostituire l'app dopo la chiusura
        update_script = app_dir / "update_brt.sh"

        script_content = f"""#!/bin/bash
sleep 2
rm -rf "{current_app}"
mv "{new_app}" "{current_app}"
open "{current_app}"
rm -rf "{extract_dir}"
rm -f "{downloaded_path}"
rm -f "$0"
"""

        with open(update_script, 'w') as f:
            f.write(script_content)

        os.chmod(update_script, 0o755)

        # Avvia lo script e chiudi l'applicazione
        subprocess.Popen(['/bin/bash', str(update_script)])

        QApplication.quit()

    def on_download_failed(self, error_msg):
        """Download fallito"""
        self.download_dialog.close()

        QMessageBox.critical(self, "Errore Download",
            f"Impossibile scaricare l'aggiornamento:\n\n{error_msg}")


    def apply_template(self, colli, peso):
        """Applica template rapido"""
        self.colli_input.setText(str(colli))
        self.peso_input.setText(str(peso))

    def load_csv(self):
        """Carica e processa il file CSV"""

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona LISTADDT.csv",
            str(Path.home() / "Documents"),
            "CSV files (*.csv);;All files (*.*)"
        )

        if not file_path:
            return

        try:
            # Leggi CSV forzando le colonne di testo come stringhe
            # SpedLocalita2 (telefono) e SpedCAP devono essere stringhe per evitare conversione in float
            df = pd.read_csv(file_path, sep=';', encoding='utf-8', dtype={
                'SpedLocalita2': str,
                'SpedCAP': str
            })

            # Verifica colonne necessarie
            required_cols = ['RegisNumero', 'SpedRagSoc1', 'SpedIndirizzo',
                             'SpedLocalita', 'SpedLocalita2', 'SpedCAP',
                             'SpedProvincia', 'AccompCodPorto']

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                QMessageBox.critical(self, "Errore",
                    f"Colonne mancanti nel CSV:\n{', '.join(missing_cols)}")
                return

            # Seleziona solo le colonne necessarie
            df = df[required_cols].copy()

            # Assicurati che SpedLocalita2 e SpedCAP siano stringhe pulite (rimuovi NaN)
            df['SpedLocalita2'] = df['SpedLocalita2'].fillna('').astype(str)
            df['SpedCAP'] = df['SpedCAP'].fillna('').astype(str)

            # Rimuovi duplicati basati su RegisNumero
            df_unique = df.drop_duplicates(subset=['RegisNumero'], keep='first')

            # Rinomina colonne secondo mapping BRT
            df_unique = df_unique.rename(columns={
                'RegisNumero': 'VABNSP',
                'SpedRagSoc1': 'VABRSD',
                'SpedIndirizzo': 'VABIND',
                'SpedLocalita': 'VABLOD',
                'SpedLocalita2': 'VABTRC',
                'SpedCAP': 'VABCAD',
                'SpedProvincia': 'VABPRD',
                'AccompCodPorto': 'VABCBO'
            })

            # Duplica VABNSP per VABRMN
            df_unique['VABRMN'] = df_unique['VABNSP']

            # VABCEL deve contenere SpedLocalita2 (già mappata in VABTRC)
            df_unique['VABCEL'] = df_unique['VABTRC']

            # Aggiungi colonne per dati da compilare
            df_unique['VABNCL'] = ''
            df_unique['VABPKB'] = ''

            # Aggiungi campi fissi
            for campo, valore in self.CAMPI_FISSI.items():
                df_unique[campo] = valore

            # Salva dataframe
            self.df_spedizioni = df_unique
            self.current_index = 0

            # Elimina JSON salvato (nuovo file = nuova sessione)
            if self.save_file.exists():
                self.save_file.unlink()

            # Aggiorna interfaccia
            num_rows = len(self.df_spedizioni)
            num_orig = len(df)
            duplicates = num_orig - num_rows

            self.file_label.setText(f"✓ {Path(file_path).name}")
            self.info_label.setText(
                f"✓ {num_rows} spedizioni caricate ({duplicates} duplicati rimossi)"
            )

            # Mostra primo record
            self.show_current_record()

            QMessageBox.information(self, "Successo",
                f"File caricato con successo!\n\n"
                f"Spedizioni uniche: {num_rows}\n"
                f"Duplicati rimossi: {duplicates}")

        except Exception as e:
            QMessageBox.critical(self, "Errore",
                f"Errore nel caricamento del file:\n{str(e)}")

    def show_current_record(self):
        """Mostra il record corrente"""

        if self.df_spedizioni is None or len(self.df_spedizioni) == 0:
            return

        # IMPORTANTE: Verifica che l'indice sia valido
        if self.current_index >= len(self.df_spedizioni):
            self.current_index = len(self.df_spedizioni) - 1
            return

        # Ottieni record corrente
        record = self.df_spedizioni.iloc[self.current_index]

        # Aggiorna dati destinatario (usa HTML per formattazione con sfondo colorato)
        dest_info = (
            f"<div style='font-family: {MONOSPACE_FONT}; font-size: 10pt;'>"
            f"N. Spedizione: {record['VABNSP']}<br>"
            f"Destinatario:  {record['VABRSD']}<br>"
            f"Indirizzo:     {record['VABIND']}<br>"
            f"CAP:           {record['VABCAD']}    Città: {record['VABLOD']}<br>"
            f"Provincia:     {record['VABPRD']}<br>"
            f"Telefono:      {record['VABTRC']}"
        )

        # Aggiungi dati salvati se presenti con sfondo colorato
        if record['VABNCL'] and record['VABNCL'] != '' and record['VABNCL'] != 'SKIP':
            dest_info += (
                f"<br><br>"
                f"Colli: {record['VABNCL']}<br>"
                f"Peso: {record['VABPKB']} kg<br>"
                f"<div style='background-color: #28a745; color: white; padding: 5px; margin-top: 5px; font-weight: bold;'>"
                f"✓ SALVATO"
                f"</div>"
            )
        elif record['VABNCL'] == 'SKIP':
            dest_info += (
                f"<br><br>"
                f"<div style='background-color: #dc3545; color: white; padding: 5px; margin-top: 5px; font-weight: bold;'>"
                f"✗ SALTATO"
                f"</div>"
            )

        dest_info += "</div>"
        self.dest_text.setHtml(dest_info)

        # Carica dati spedizione se già compilati (escludi SKIP)
        if record['VABNCL'] and record['VABNCL'] != 'SKIP':
            self.colli_input.setText(str(record['VABNCL']))
        else:
            self.colli_input.setText(str(self.default_colli))

        if record['VABPKB'] and record['VABPKB'] != 'SKIP':
            self.peso_input.setText(str(record['VABPKB']))
        else:
            self.peso_input.setText(str(self.default_peso))

        # Aggiorna progress - conta solo record REALMENTE compilati (no vuoti, no SKIP)
        total = len(self.df_spedizioni)
        completed = int(((self.df_spedizioni['VABNCL'] != '') &
                         (self.df_spedizioni['VABNCL'] != 'SKIP')).sum())
        progress_pct = int((completed / total) * 100) if total > 0 else 0

        self.progress_label.setText(f"Cliente {self.current_index + 1}/{total} ({progress_pct}%)")
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(completed)

        # Aggiorna riepilogo
        skipped = int((self.df_spedizioni['VABNCL'] == 'SKIP').sum())
        empty = total - completed - skipped

        if empty == 0 and skipped == 0:
            # Tutti i record sono completati
            self.summary_label.setText(
                f"<span style='background-color: #28a745; color: white; padding: 5px 10px; font-weight: bold; border-radius: 3px;'>✓ COMPLETO - Tutti i {total} record compilati!</span>"
            )
        else:
            self.summary_label.setText(
                f"COMPLETATI: {completed} ✓  |  DA FARE: {empty}  |  SALTATI: {skipped}"
            )

        # Abilita/disabilita bottoni in base alla posizione
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Aggiorna lo stato dei bottoni di navigazione"""

        if self.df_spedizioni is None or len(self.df_spedizioni) == 0:
            return

        total = len(self.df_spedizioni)
        is_last = self.current_index >= total - 1

        # Verifica se il record corrente è già salvato
        current_record = self.df_spedizioni.iloc[self.current_index]
        current_is_saved = current_record['VABNCL'] != ''

        # Verifica se tutti i record sono stati completati (NO vuoti, NO SKIP)
        empty_records = int((self.df_spedizioni['VABNCL'] == '').sum())
        skipped_records = int((self.df_spedizioni['VABNCL'] == 'SKIP').sum())
        all_completed = bool((empty_records == 0) and (skipped_records == 0))

        # Bottone Precedente: disabilita se siamo al primo
        self.prev_btn.setEnabled(self.current_index > 0)

        # Bottone Salta: disabilita se siamo all'ultimo
        self.skip_btn.setEnabled(not is_last)

        # Bottone "Vai a Saltati": mostra SOLO se ci sono record saltati
        if skipped_records > 0:
            self.goto_skipped_btn.setVisible(True)
        else:
            self.goto_skipped_btn.setVisible(False)

        # Bottone SALVA E SUCCESSIVO/ESPORTA:
        # - Si attiva se i campi correnti sono compilati
        # - All'ultimo record, controlla anche che NON ci siano SKIP
        colli_valid = self.colli_input.text().strip() != ''
        peso_valid = self.peso_input.text().strip() != ''

        if is_last:
            # All'ultimo record: attiva SOLO se non ci sono record skippati
            can_save = colli_valid and peso_valid and (skipped_records == 0)
        else:
            # Durante la navigazione: attiva se i campi sono validi
            can_save = colli_valid and peso_valid

        # Se tutto è completato, mostra "COMPLETATO" in grigio
        if all_completed:
            self.save_next_btn.setText("✓ COMPLETATO")
            self.save_next_btn.setEnabled(False)
            self.save_next_btn.setStyleSheet("background-color: #CCCCCC; color: #666666; border: none; padding: 8px 15px; border-radius: 4px;")
        else:
            self.save_next_btn.setEnabled(can_save)

            if is_last:
                self.save_next_btn.setText("✓ SALVA E COMPLETA")
                if can_save:
                    self.save_next_btn.setStyleSheet("background-color: #DC012E; color: white; font-weight: bold; border: none; padding: 8px 15px; border-radius: 4px;")
                else:
                    self.save_next_btn.setStyleSheet("background-color: #CCCCCC; color: #666666; border: none; padding: 8px 15px; border-radius: 4px;")
            else:
                self.save_next_btn.setText("✓ SALVA E SUCCESSIVO ▶")
                if can_save:
                    self.save_next_btn.setStyleSheet("background-color: #16FEBC; color: #333333; font-weight: bold; border: none; padding: 8px 15px; border-radius: 4px;")
                else:
                    self.save_next_btn.setStyleSheet("background-color: #CCCCCC; color: #666666; border: none; padding: 8px 15px; border-radius: 4px;")

        # Bottone Esporta: abilita SOLO se TUTTI i record sono completati (NO SKIP!)
        self.export_btn.setVisible(True)
        self.export_btn.setEnabled(all_completed)

        if all_completed:
            self.export_btn.setStyleSheet("background-color: #5F38E6; color: white; font-weight: bold; border: none; padding: 10px; border-radius: 4px;")
        else:
            self.export_btn.setStyleSheet("background-color: #CCCCCC; color: #666666; border: none; padding: 10px; border-radius: 4px;")

    def save_and_next_unified(self):
        """Pulsante unificato: salva e successivo oppure salva ed esporta"""

        if self.df_spedizioni is None:
            return

        # Valida input
        try:
            colli = self.colli_input.text().strip()
            peso = self.peso_input.text().strip()

            if not colli or not peso:
                QMessageBox.warning(self, "Attenzione",
                    "Compilare tutti i campi (colli e peso)")
                return

            # Converti e valida
            colli_int = int(colli)
            peso_float = float(peso.replace(',', '.'))

            if colli_int <= 0 or peso_float <= 0:
                QMessageBox.warning(self, "Attenzione",
                    "Colli e peso devono essere maggiori di zero")
                return

        except ValueError:
            QMessageBox.warning(self, "Attenzione",
                "Valori non validi per colli o peso")
            return

        # Salva dati nel record corrente
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABNCL')] = str(colli_int)
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABPKB')] = f"{peso_float:.1f}"

        # Salva su file
        self.save_data_to_file()

        # Se siamo in modalità navigazione saltati, vai al prossimo saltato
        if self.skip_navigation_mode:
            # Trova tutti i record saltati
            skipped_indices = self.df_spedizioni[self.df_spedizioni['VABNCL'] == 'SKIP'].index.tolist()

            if not skipped_indices:
                # Non ci sono più record saltati!
                # Esci dalla modalità e trova il primo record vuoto (se esiste)
                self.skip_navigation_mode = False

                # Cerca il primo record NON compilato
                empty_indices = self.df_spedizioni[self.df_spedizioni['VABNCL'] == ''].index.tolist()

                if empty_indices:
                    # Ci sono ancora record vuoti da compilare
                    # Vai al primo record vuoto
                    first_empty = self.df_spedizioni.index.get_loc(empty_indices[0])
                    self.current_index = first_empty
                else:
                    # Tutto completato! Vai all'ultimo record
                    total = len(self.df_spedizioni)
                    self.current_index = total - 1

                self.show_current_record()
                return

            # Cerca il primo record saltato DOPO l'indice corrente
            next_skipped = None
            for idx in skipped_indices:
                idx_pos = self.df_spedizioni.index.get_loc(idx)
                if idx_pos > self.current_index:
                    next_skipped = idx_pos
                    break

            # Se non ce ne sono dopo, prendi il primo in assoluto
            if next_skipped is None:
                next_skipped = self.df_spedizioni.index.get_loc(skipped_indices[0])

            # Vai al prossimo record saltato
            self.current_index = next_skipped
        else:
            # Modalità normale: vai al prossimo in sequenza
            total = len(self.df_spedizioni)
            is_last = self.current_index >= total - 1

            if not is_last:
                # Vai al prossimo record
                self.current_index += 1

        # Aggiorna visualizzazione
        self.show_current_record()

    def save_and_next(self):
        """Salva dati correnti e passa al successivo"""

        if self.df_spedizioni is None:
            return

        # Verifica di non essere già all'ultimo record
        if self.current_index >= len(self.df_spedizioni) - 1:
            QMessageBox.warning(self, "Attenzione",
                "Sei già all'ultimo record!\n\n"
                "Non ci sono altri clienti da compilare.")
            return

        # Valida input
        try:
            colli = self.colli_input.text().strip()
            peso = self.peso_input.text().strip()

            if not colli or not peso:
                QMessageBox.warning(self, "Attenzione",
                    "Compilare tutti i campi (colli e peso)")
                return

            # Converti e valida
            colli_int = int(colli)
            peso_float = float(peso.replace(',', '.'))

            if colli_int <= 0 or peso_float <= 0:
                QMessageBox.warning(self, "Attenzione",
                    "Colli e peso devono essere maggiori di zero")
                return

        except ValueError:
            QMessageBox.warning(self, "Attenzione",
                "Valori non validi per colli o peso")
            return

        # Salva dati SOLO nel record corrente (non aggiunge mai righe)
        # Usa iloc per accesso posizionale, non at che usa l'indice del DataFrame
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABNCL')] = str(colli_int)
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABPKB')] = f"{peso_float:.1f}"

        # Salva su file
        self.save_data_to_file()

        # Vai al prossimo (abbiamo già verificato che non sia l'ultimo)
        self.current_index += 1
        self.show_current_record()

    def save_current(self):
        """Salva il record corrente senza passare al successivo"""

        if self.df_spedizioni is None:
            return

        # Valida input
        try:
            colli = self.colli_input.text().strip()
            peso = self.peso_input.text().strip()

            if not colli or not peso:
                QMessageBox.warning(self, "Attenzione",
                    "Compilare tutti i campi (colli e peso)")
                return

            # Converti e valida
            colli_int = int(colli)
            peso_float = float(peso.replace(',', '.'))

            if colli_int <= 0 or peso_float <= 0:
                QMessageBox.warning(self, "Attenzione",
                    "Colli e peso devono essere maggiori di zero")
                return

        except ValueError:
            QMessageBox.warning(self, "Attenzione",
                "Valori non validi per colli o peso")
            return

        # Salva dati nel record corrente
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABNCL')] = str(colli_int)
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABPKB')] = f"{peso_float:.1f}"

        # Salva su file
        self.save_data_to_file()

        # Aggiorna visualizzazione (rimane sullo stesso record)
        self.show_current_record()

    def skip_item(self):
        """Salta il record corrente"""

        if self.df_spedizioni is None:
            return

        # Marca come saltato
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABNCL')] = 'SKIP'
        self.df_spedizioni.iloc[self.current_index, self.df_spedizioni.columns.get_loc('VABPKB')] = 'SKIP'

        # Salva
        self.save_data_to_file()

        # Vai al prossimo
        if self.current_index < len(self.df_spedizioni) - 1:
            self.current_index += 1
            self.show_current_record()

    def previous_item(self):
        """Torna al record precedente"""

        if self.df_spedizioni is None or self.current_index == 0:
            return

        # Esci dalla modalità navigazione saltati
        self.skip_navigation_mode = False

        self.current_index -= 1
        self.show_current_record()

    def goto_next_skipped(self):
        """Vai al prossimo record saltato (SKIP)"""

        if self.df_spedizioni is None:
            return

        # Trova tutti i record saltati
        skipped_indices = self.df_spedizioni[self.df_spedizioni['VABNCL'] == 'SKIP'].index.tolist()

        if not skipped_indices:
            QMessageBox.information(self, "Info", "Non ci sono record saltati da compilare!")
            self.skip_navigation_mode = False
            return

        # Attiva modalità navigazione saltati
        self.skip_navigation_mode = True

        # Cerca il primo record saltato DOPO l'indice corrente
        next_skipped = None
        for idx in skipped_indices:
            idx_pos = self.df_spedizioni.index.get_loc(idx)
            if idx_pos > self.current_index:
                next_skipped = idx_pos
                break

        # Se non ce ne sono dopo, prendi il primo in assoluto (ricomincia dal primo)
        if next_skipped is None:
            next_skipped = self.df_spedizioni.index.get_loc(skipped_indices[0])

        # Vai al record saltato
        self.current_index = next_skipped
        self.show_current_record()

    def save_data_to_file(self):
        """Salva i dati compilati su file JSON"""

        if self.df_spedizioni is None:
            return

        try:
            # Salva SOLO i record compilati (con VABNCL non vuoto)
            df_to_save = self.df_spedizioni[self.df_spedizioni['VABNCL'] != ''][['VABNSP', 'VABNCL', 'VABPKB']]

            data = {
                'last_modified': datetime.now().isoformat(),
                'data': df_to_save.to_dict('records')
            }

            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Errore nel salvataggio: {e}")

    def load_saved_data(self):
        """Carica i dati salvati precedentemente"""

        if not self.save_file.exists() or self.df_spedizioni is None:
            return

        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)

            # Ripristina dati compilati
            for item in data['data']:
                mask = self.df_spedizioni['VABNSP'] == item['VABNSP']
                if mask.any():
                    idx = self.df_spedizioni[mask].index[0]
                    self.df_spedizioni.at[idx, 'VABNCL'] = item['VABNCL']
                    self.df_spedizioni.at[idx, 'VABPKB'] = item['VABPKB']

        except Exception as e:
            print(f"Errore nel caricamento dati salvati: {e}")

    def export_brt_csv(self):
        """Esporta il CSV finale per BRT"""

        if self.df_spedizioni is None:
            QMessageBox.warning(self, "Attenzione", "Carica prima un file CSV")
            return

        # Filtra solo record completati
        df_export = self.df_spedizioni[
            (self.df_spedizioni['VABNCL'] != '') &
            (self.df_spedizioni['VABNCL'] != 'SKIP')
        ].copy()

        if len(df_export) == 0:
            QMessageBox.warning(self, "Attenzione",
                "Nessun record completato da esportare")
            return

        # Ordina colonne secondo tracciato BRT
        colonne_brt = [
            'VABATB', 'VABCCM', 'VABNSP', 'VABCBO', 'VABRSD', 'VABIND',
            'VABCAD', 'VABLOD', 'VABPRD', 'VABNZD', 'VABCTR', 'VABTSP',
            'VABNAS', 'VABNCL', 'VABPKB', 'VABRMN', 'VABRMA', 'VABTRC',
            'VABCEL'
        ]

        # Aggiungi colonne mancanti se necessario
        for col in colonne_brt:
            if col not in df_export.columns:
                df_export[col] = ''

        # Seleziona e ordina colonne
        df_export = df_export[colonne_brt]

        # Chiedi dove salvare
        default_filename = f"spedizioni_BRT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva CSV per BRT",
            str(Path.home() / "Documents" / default_filename),
            "CSV files (*.csv);;All files (*.*)"
        )

        if not file_path:
            return

        try:
            # Esporta CSV (con header, separatore punto e virgola)
            df_export.to_csv(file_path, sep=';', index=False, header=True, encoding='utf-8')

            self.export_label.setText(
                f"✓ Esportate {len(df_export)} spedizioni in:\n{Path(file_path).name}"
            )

            QMessageBox.information(self, "Successo",
                f"File esportato con successo!\n\n"
                f"Spedizioni esportate: {len(df_export)}\n"
                f"File: {Path(file_path).name}\n\n"
                f"Ora puoi caricare questo file sul gestionale BRT.")

        except Exception as e:
            QMessageBox.critical(self, "Errore",
                f"Errore nell'esportazione:\n{str(e)}")


def main():
    """Funzione principale"""
    app = QApplication(sys.argv)
    window = BRTSpedizioniApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
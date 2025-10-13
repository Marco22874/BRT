"""
Main window module for BRT Shipping Management Application
Contains the main application window class
"""

import sys
import platform
import pandas as pd
from pathlib import Path
import webbrowser
import subprocess
import os
import zipfile
from typing import Optional, Dict, Any, Tuple

from PyQt5.QtWidgets import (QMainWindow, QStackedWidget, QAction,
                              QApplication, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from core.constants import (UIConstants, Colors, RecordStatus, FileSettings,
                            BRTDefaults, CSVColumns, Messages)
from core.utils import MONOSPACE_FONT, logger
from core.models import validate_shipment_input
from services.updater import UpdateDownloader, UpdateChecker
from .dialogs import DownloadDialog, AboutDialog
from .components.settings_manager import SettingsManager
from .components.csv_handler import CsvHandler
from .components.navigation_handler import NavigationHandler
from .components.ui_builder import UIBuilder


# Application metadata (imported from main module)
__version__ = "4.1.0"
__app_name__ = "Gestione Spedizioni IGEA <-> BRT"
__release_date__ = "2025-10-13"
__developer__ = "Marco De Luca"


class BRTSpedizioniApp(QMainWindow):
    """Main application for BRT shipping management"""

    # BRT fixed fields configuration
    CAMPI_FISSI = {
        'VABATB': '',  # empty for Italy
        'VABCCM': '0091808',  # Customer code
        'VABNAS': 'DISPOSITIVI MEDICI',  # Goods type
        'VABRMA': 'IGEA SRL',  # Alphabetic reference
        'VABCTR': '100',  # Tariff code
        'VABNZD': '',  # empty for Italy
        'VABTSP': 'C',  # Express service
    }

    def __init__(self) -> None:
        super().__init__()

        # Variables
        self.df_spedizioni: Optional[pd.DataFrame] = None
        self.current_index: int = 0
        # Save JSON in the same folder as the application
        self.save_file: Path = Path(__file__).parent.parent / "brt_spedizioni_data.json"
        settings_file: Path = Path(__file__).parent.parent / "brt_settings.json"

        # Initialize settings manager
        self.settings_manager = SettingsManager(settings_file)

        # Initialize CSV handler
        self.csv_handler = CsvHandler(self, self.save_file)

        # Initialize navigation handler
        self.navigation_handler = NavigationHandler(self)

        # Initialize UI builder
        self.ui_builder = UIBuilder(Path(__file__).parent.parent)

        # Default settings
        self.default_colli: int = 1
        self.default_peso: int = 2

        # BRT configurable fields (will be loaded from settings)
        self.brt_customer_code: str = BRTDefaults.DEFAULT_CUSTOMER_CODE
        self.brt_alphabetic_ref: str = BRTDefaults.DEFAULT_ALPHABETIC_REF
        self.brt_goods_type: str = BRTDefaults.DEFAULT_GOODS_TYPE
        self.brt_tariff_code: str = BRTDefaults.DEFAULT_TARIFF_CODE
        self.brt_service_type: str = BRTDefaults.DEFAULT_SERVICE_TYPE

        # Cache for DataFrame counts (to avoid repeated calculations)
        self._cache_total: int = 0
        self._cache_completed: int = 0
        self._cache_skipped: int = 0
        self._cache_empty: int = 0
        self._cache_dirty: bool = True

        # Load saved settings
        self.load_settings()

        # Initialize interface
        self._init_ui()

        # Load saved data if it exists
        self.load_saved_data()

        # Start update check (in background)
        self.check_for_updates()

    def _init_ui(self) -> None:
        """Initialize the user interface"""

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setGeometry(100, 100, 900, 800)

        # Set application icon (IGEA logo)
        icon_path = Path(__file__).parent.parent / FileSettings.LOGO_IGEA
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create menu bar
        self._create_menu_bar()

        # Create stacked widget to switch between main screen and settings
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create the two screens using UI builder
        self.main_screen, main_widgets = self._create_main_screen_with_builder()
        self.settings_screen, settings_inputs = self._create_settings_screen_with_builder()

        # Assign widget references
        self.file_label = main_widgets['file_label']
        self.info_label = main_widgets['info_label']
        self.dest_text = main_widgets['dest_text']
        self.colli_input = main_widgets['colli_input']
        self.peso_input = main_widgets['peso_input']
        self.progress_label = main_widgets['progress_label']
        self.progress_bar = main_widgets['progress_bar']
        self.summary_label = main_widgets['summary_label']
        self.prev_btn = main_widgets['prev_btn']
        self.skip_btn = main_widgets['skip_btn']
        self.goto_skipped_btn = main_widgets['goto_skipped_btn']
        self.save_next_btn = main_widgets['save_next_btn']
        self.export_btn = main_widgets['export_btn']
        self.export_label = main_widgets['export_label']

        # Assign settings input references
        self.settings_colli_input = settings_inputs['settings_colli_input']
        self.settings_peso_input = settings_inputs['settings_peso_input']
        self.settings_customer_code_input = settings_inputs['settings_customer_code_input']
        self.settings_alphabetic_ref_input = settings_inputs['settings_alphabetic_ref_input']
        self.settings_goods_type_input = settings_inputs['settings_goods_type_input']
        self.settings_tariff_code_input = settings_inputs['settings_tariff_code_input']
        self.settings_service_type_input = settings_inputs['settings_service_type_input']

        # Add screens to stack
        self.stacked_widget.addWidget(self.main_screen)
        self.stacked_widget.addWidget(self.settings_screen)

        # Show main screen
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def _create_main_screen_with_builder(self) -> tuple:
        """Create main screen using UI builder.

        Returns:
            Tuple of (widget, dict of widget references)
        """
        callbacks = {
            'load_csv': self.load_csv,
            'peso_focus': lambda: self.peso_input.setFocus(),
            'save_and_next': self.save_and_next,
            'template': self.apply_template,
            'previous': self.previous_item,
            'skip': self.skip_item,
            'goto_skipped': self.goto_next_skipped,
            'save_and_next_unified': self.save_and_next_unified,
            'export_csv': self.export_brt_csv
        }

        return self.ui_builder.create_main_screen(
            self._get_button_style,
            self.default_colli,
            self.default_peso,
            callbacks
        )

    def _create_settings_screen_with_builder(self) -> tuple:
        """Create settings screen using UI builder.

        Returns:
            Tuple of (widget, dict of input references)
        """
        brt_config = {
            'brt_customer_code': self.brt_customer_code,
            'brt_alphabetic_ref': self.brt_alphabetic_ref,
            'brt_goods_type': self.brt_goods_type,
            'brt_tariff_code': self.brt_tariff_code,
            'brt_service_type': self.brt_service_type
        }

        callbacks = {
            'back': self.show_main_screen,
            'save': self.save_settings_and_return
        }

        return self.ui_builder.create_settings_screen(
            self._get_button_style,
            self.default_colli,
            self.default_peso,
            brt_config,
            callbacks
        )

    def _create_menu_bar(self) -> None:
        """Create the menu bar"""
        menubar = self.menuBar()
        if menubar is None:
            return

        # File menu
        file_menu = menubar.addMenu('File')
        if file_menu is None:
            return

        # Settings action
        settings_action = QAction('Impostazioni', self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        # Info menu
        info_menu = menubar.addMenu('Info')
        if info_menu is None:
            return

        # About action
        about_action = QAction('Informazioni', self)
        about_action.triggered.connect(self.show_about_dialog)
        info_menu.addAction(about_action)

    def show_settings(self) -> None:
        """Show the settings screen"""
        # Update the values in the settings inputs
        self.settings_colli_input.setText(str(self.default_colli))
        self.settings_peso_input.setText(str(self.default_peso))

        # Update BRT fields
        self.settings_customer_code_input.setText(self.brt_customer_code)
        self.settings_alphabetic_ref_input.setText(self.brt_alphabetic_ref)
        self.settings_goods_type_input.setText(self.brt_goods_type)
        self.settings_tariff_code_input.setText(self.brt_tariff_code)
        self.settings_service_type_input.setText(self.brt_service_type)

        self.stacked_widget.setCurrentWidget(self.settings_screen)

    def show_main_screen(self) -> None:
        """Show the main screen"""
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def show_about_dialog(self) -> None:
        """Show the about dialog"""
        dialog = AboutDialog(self, __app_name__, __version__, __release_date__, __developer__)
        dialog.exec_()

    def save_settings_and_return(self) -> None:
        """Save settings and return to main screen"""
        try:
            # Validate input
            colli = int(self.settings_colli_input.text().strip())
            peso = float(self.settings_peso_input.text().strip().replace(',', '.'))

            if colli <= 0 or peso <= 0:
                QMessageBox.warning(self, Messages.TITLE_WARNING,
                    Messages.MSG_SETTINGS_POSITIVE)
                return

            # Save the new default values
            self.default_colli = colli
            self.default_peso = peso

            # Save BRT fields from UI
            self.brt_customer_code = self.settings_customer_code_input.text().strip()
            self.brt_alphabetic_ref = self.settings_alphabetic_ref_input.text().strip()
            self.brt_goods_type = self.settings_goods_type_input.text().strip()
            self.brt_tariff_code = self.settings_tariff_code_input.text().strip()
            self.brt_service_type = self.settings_service_type_input.text().strip()

            # Save to file using SettingsManager
            settings_data = {
                'default_colli': self.default_colli,
                'default_peso': self.default_peso,
                'brt_customer_code': self.brt_customer_code,
                'brt_alphabetic_ref': self.brt_alphabetic_ref,
                'brt_goods_type': self.brt_goods_type,
                'brt_tariff_code': self.brt_tariff_code,
                'brt_service_type': self.brt_service_type
            }

            self.settings_manager.save(settings_data)

            QMessageBox.information(self, Messages.TITLE_SUCCESS,
                Messages.MSG_SETTINGS_SAVED)

            # Return to main screen
            self.show_main_screen()

        except ValueError as e:
            logger.warning(f"Invalid input in settings: {e}")
            QMessageBox.warning(self, Messages.TITLE_WARNING,
                Messages.MSG_INVALID_SETTINGS)

    def load_settings(self) -> None:
        """Load saved settings"""
        settings = self.settings_manager.load()

        # Apply loaded settings
        self.default_colli = settings['default_colli']
        self.default_peso = settings['default_peso']
        self.brt_customer_code = settings['brt_customer_code']
        self.brt_alphabetic_ref = settings['brt_alphabetic_ref']
        self.brt_goods_type = settings['brt_goods_type']
        self.brt_tariff_code = settings['brt_tariff_code']
        self.brt_service_type = settings['brt_service_type']

    def check_for_updates(self) -> None:
        """Start update check in background"""
        self.update_checker = UpdateChecker(__version__)
        self.update_checker.update_available.connect(self.show_update_dialog)
        self.update_checker.start()

    def show_update_dialog(self, new_version: str, release_url: str, download_url: str) -> None:
        """Show update available dialog"""
        msg = QMessageBox(self)
        msg.setWindowTitle(Messages.TITLE_UPDATE_AVAILABLE)
        msg.setIcon(QMessageBox.Information)

        text = Messages.format(Messages.MSG_UPDATE_AVAILABLE,
                               new_version=new_version,
                               current_version=__version__)
        msg.setText(text)
        msg.setTextFormat(Qt.RichText)

        # Buttons
        download_btn = msg.addButton(Messages.BTN_DOWNLOAD_NOW, QMessageBox.AcceptRole)
        later_btn = msg.addButton(Messages.BTN_REMIND_LATER, QMessageBox.RejectRole)

        # Set custom icon
        igea_icon_path = Path(__file__).parent.parent / FileSettings.LOGO_IGEA
        if igea_icon_path.exists():
            msg.setWindowIcon(QIcon(str(igea_icon_path)))

        msg.exec_()

        # If user clicked Download
        if msg.clickedButton() == download_btn:
            if download_url:
                self.start_download(download_url)
            else:
                # Fallback: open GitHub page
                webbrowser.open(release_url)

    def start_download(self, download_url: str) -> None:
        """Start downloading the update"""
        # Determine the filename from the URL
        filename = download_url.split('/')[-1]

        # Path where to download (parent folder of app to avoid conflicts)
        if getattr(sys, 'frozen', False):
            # If it's a PyInstaller executable (--onedir on Windows)
            # sys.executable = Desktop/Gestione_Spedizioni_BRT/Gestione_Spedizioni_BRT.exe
            # We must download to Desktop (parent of the app folder)
            download_dir = Path(sys.executable).parent.parent
        else:
            # If it's a Python script
            download_dir = Path(__file__).parent.parent

        # Create custom download dialog with progress bar
        self.download_dialog = DownloadDialog(self, filename)

        # Start the downloader
        self.downloader = UpdateDownloader(download_url, filename, str(download_dir))
        self.downloader.download_progress.connect(self.download_dialog.update_progress)
        self.downloader.download_complete.connect(self.on_download_complete)
        self.downloader.download_failed.connect(self.on_download_failed)
        self.downloader.start()

        # Show the dialog
        self.download_dialog.show()

    def on_download_complete(self, file_path: str) -> None:
        """Download completed - install and restart"""
        self.download_dialog.close()

        try:
            self.install_update(file_path)
        except Exception as e:
            QMessageBox.critical(self, Messages.TITLE_INSTALL_ERROR,
                Messages.format(Messages.MSG_UPDATE_INSTALL_ERROR, error=e, path=file_path))

    def install_update(self, downloaded_file: str) -> None:
        """Install the update and restart the application"""
        downloaded_path = Path(downloaded_file)
        system = platform.system()

        if getattr(sys, 'frozen', False):
            # PyInstaller executable
            current_exe = Path(sys.executable)
            app_dir = current_exe.parent.parent
        else:
            # Python script (development mode)
            current_exe = Path(__file__)
            app_dir = current_exe.parent.parent

        if system == 'Windows':
            # Windows: replace .exe
            self.install_windows_update(downloaded_path, current_exe, app_dir)
        elif system == 'Darwin':
            # macOS: extract .zip and replace .app
            self.install_macos_update(downloaded_path, current_exe, app_dir)

    def install_windows_update(self, downloaded_path: Path, current_exe: Path, app_dir: Path) -> None:
        """Install update on Windows"""
        # Determine current app folder and parent
        if getattr(sys, 'frozen', False):
            # If we're in PyInstaller executable (--onedir mode)
            # sys.executable points to Gestione_Spedizioni_BRT/Gestione_Spedizioni_BRT.exe
            current_app_folder = current_exe.parent
            parent_dir = current_app_folder.parent
        else:
            # Development mode
            current_app_folder = app_dir / "Gestione_Spedizioni_BRT"
            parent_dir = app_dir

        # Extract zip content to parent folder
        extract_dir = parent_dir / FileSettings.TEMP_UPDATE_DIR
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(downloaded_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find the application folder in extracted content
        new_app_folder = None
        for item in extract_dir.iterdir():
            if item.is_dir():
                # Verify it contains an exe
                exe_files = list(item.glob("*.exe"))
                if exe_files:
                    new_app_folder = item
                    break

        if not new_app_folder:
            raise Exception("Cartella applicazione non trovata nell'archivio")

        # Name for backup
        backup_folder = parent_dir / (current_app_folder.name + "_old")

        # Create batch script to replace folder after closing
        update_script = parent_dir / FileSettings.UPDATE_SCRIPT_WIN

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

REM 1. Elimina la vecchia cartella completamente
if exist "{current_app_folder}" (
    echo Eliminazione vecchia versione...
    rmdir /s /q "{current_app_folder}"
)

REM 2. Copia la nuova cartella dalla temp alla posizione corretta
echo Installazione nuova versione...
xcopy "{new_app_folder}" "{current_app_folder}" /E /I /Q /Y

REM 3. Verifica che l'exe esista
if exist "{current_app_folder}\\{current_exe.name}" (
    echo Avvio nuova versione...
    start "" "{current_app_folder}\\{current_exe.name}"
    timeout /t 2 /nobreak > nul

    REM 4. Cleanup: elimina temp e zip
    echo Pulizia file temporanei...
    if exist "{extract_dir}" rmdir /s /q "{extract_dir}"
    if exist "{downloaded_path}" del /F /Q "{downloaded_path}"

    echo Aggiornamento completato!
) else (
    echo ERRORE: Aggiornamento fallito!
    pause
)

del "%~f0"
"""

        with open(str(update_script), 'w', encoding='utf-8') as f:
            f.write(script_content)

        # Start the script and close the application
        subprocess.Popen(['cmd', '/c', str(update_script)],
                        creationflags=subprocess.CREATE_NO_WINDOW)

        QApplication.quit()

    def install_macos_update(self, downloaded_path: Path, current_exe: Path, app_dir: Path) -> None:
        """Install update on macOS"""
        # Extract zip content
        extract_dir = app_dir / FileSettings.TEMP_UPDATE_DIR
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(str(downloaded_path), 'r') as zip_ref:
            zip_ref.extractall(str(extract_dir))

        # Find new app in extracted content
        new_app = None
        for item in extract_dir.iterdir():
            if item.suffix == '.app':
                new_app = item
                break

        if not new_app:
            raise Exception("File .app non trovato nell'archivio")

        # Determine current app path
        if getattr(sys, 'frozen', False):
            # If we're in app bundle (.app/Contents/MacOS/executable)
            current_app = current_exe.parent.parent.parent
        else:
            # Development mode
            current_app = app_dir / "brt_app_pyqt5.app"

        # Create shell script to replace app after closing
        update_script = app_dir / FileSettings.UPDATE_SCRIPT_MAC

        script_content = f"""#!/bin/bash
sleep 2
rm -rf "{current_app}"
mv "{new_app}" "{current_app}"
open "{current_app}"
rm -rf "{extract_dir}"
rm -f "{downloaded_path}"
rm -f "$0"
"""

        with open(str(update_script), 'w', encoding='utf-8') as f:
            f.write(script_content)

        os.chmod(str(update_script), 0o755)

        # Start the script and close the application
        subprocess.Popen(['/bin/bash', str(update_script)])

        QApplication.quit()

    def on_download_failed(self, error_msg: str) -> None:
        """Download failed"""
        self.download_dialog.close()

        QMessageBox.critical(self, Messages.TITLE_DOWNLOAD_ERROR,
            Messages.format(Messages.MSG_UPDATE_DOWNLOAD_ERROR, error=error_msg))


    def apply_template(self, colli: int, peso: int) -> None:
        """Apply quick template"""
        self.colli_input.setText(str(colli))
        self.peso_input.setText(str(peso))

    def load_csv(self) -> None:
        """Load and process the CSV file"""

        # Prepare BRT configuration
        brt_config = {
            'brt_customer_code': self.brt_customer_code,
            'brt_goods_type': self.brt_goods_type,
            'brt_alphabetic_ref': self.brt_alphabetic_ref,
            'brt_tariff_code': self.brt_tariff_code,
            'brt_service_type': self.brt_service_type
        }

        # Use CSV handler to load file
        result = self.csv_handler.load_csv(brt_config)

        if result is not None:
            df_unique, filename, num_rows, duplicates = result

            # Save dataframe
            self.df_spedizioni = df_unique
            self.current_index = 0

            # Invalidate cache for new DataFrame
            self._invalidate_cache()

            # Update interface
            self.file_label.setText(Messages.format(Messages.LABEL_FILE_LOADED, filename=filename))
            self.info_label.setText(
                Messages.format(Messages.LABEL_SHIPMENTS_LOADED, count=num_rows, duplicates=duplicates)
            )

            # Show first record
            self.show_current_record()

    def _validate_shipment_data(self) -> Optional[Tuple[int, float]]:
        """Validate colli and peso input fields.

        Returns:
            Optional[Tuple[int, float]]: (colli, peso) if valid, None if invalid
        """
        colli = self.colli_input.text().strip()
        peso = self.peso_input.text().strip()

        colli_int, peso_float, error_msg = validate_shipment_input(colli, peso)

        if error_msg or colli_int is None or peso_float is None:
            if error_msg:
                QMessageBox.warning(self, Messages.TITLE_WARNING, error_msg)
            return None

        return (colli_int, peso_float)

    def _invalidate_cache(self) -> None:
        """Mark the cache as dirty to force recalculation on next access."""
        self._cache_dirty = True

    def _update_cache(self) -> None:
        """Update cached DataFrame counts if cache is dirty."""
        if self.df_spedizioni is None or not self._cache_dirty:
            return

        # Calculate all counts once
        self._cache_total = len(self.df_spedizioni)

        # Count completed records (not empty and not SKIP)
        self._cache_completed = int(
            ((self.df_spedizioni[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.EMPTY.value) &
             (self.df_spedizioni[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.SKIP.value)).sum()
        )

        # Count skipped records
        self._cache_skipped = int(
            (self.df_spedizioni[CSVColumns.OUTPUT_NUM_COLLI] == RecordStatus.SKIP.value).sum()
        )

        # Calculate empty records
        self._cache_empty = self._cache_total - self._cache_completed - self._cache_skipped

        # Mark cache as clean
        self._cache_dirty = False

    def _get_button_style(self, style_type: str) -> str:
        """Get button style by type.

        Args:
            style_type: Type of button style. Options:
                - 'primary': Primary action button (green/teal)
                - 'danger': Danger/final action button (red)
                - 'warning': Warning button (orange)
                - 'info': Info button (purple)
                - 'secondary': Secondary action button (gray)
                - 'disabled': Disabled button (light gray)
                - 'success': Success button (green)

        Returns:
            str: CSS stylesheet string for the button
        """
        # Base style for all buttons
        base_style = "border: none; border-radius: 4px;"

        # Style configurations
        styles = {
            'primary': f"background-color: {Colors.PRIMARY}; color: {Colors.TEXT_BLACK}; font-weight: bold; {base_style} padding: {UIConstants.BUTTON_PADDING_NORMAL};",
            'danger': f"background-color: {Colors.DANGER}; color: {Colors.TEXT_WHITE}; font-weight: bold; {base_style} padding: {UIConstants.BUTTON_PADDING_NORMAL};",
            'warning': f"background-color: {Colors.WARNING}; color: {Colors.TEXT_WHITE}; font-weight: bold; {base_style} padding: {UIConstants.BUTTON_PADDING_NORMAL};",
            'info': f"background-color: {Colors.INFO}; color: {Colors.TEXT_WHITE}; font-weight: bold; {base_style} padding: {UIConstants.BUTTON_PADDING_EXTRA};",
            'secondary': f"background-color: {Colors.SECONDARY}; color: {Colors.TEXT_WHITE}; font-weight: bold; {base_style} padding: {UIConstants.BUTTON_PADDING_LARGE};",
            'disabled': f"background-color: {Colors.DISABLED}; color: {Colors.DISABLED_TEXT}; {base_style} padding: {UIConstants.BUTTON_PADDING_NORMAL};",
            'disabled_export': f"background-color: {Colors.DISABLED}; color: {Colors.DISABLED_TEXT}; {base_style} padding: {UIConstants.BUTTON_PADDING_EXTRA};",
            'success': f"background-color: {Colors.SUCCESS}; color: {Colors.TEXT_WHITE}; font-weight: bold; {base_style} padding: {UIConstants.BUTTON_PADDING_LARGE};",
            'plain': f"{base_style} padding: {UIConstants.BUTTON_PADDING_NORMAL};"
        }

        return styles.get(style_type, styles['plain'])

    def _format_recipient_info(self, record: pd.Series) -> str:
        """Format recipient information as HTML.

        Args:
            record: DataFrame row containing shipment data

        Returns:
            str: HTML formatted recipient information
        """
        dest_info = (
            f"<div style='font-family: {MONOSPACE_FONT}; font-size: 10pt;'>"
            f"N. Spedizione: {record[CSVColumns.OUTPUT_NUM_SPEDIZIONE]}<br>"
            f"Destinatario:  {record[CSVColumns.OUTPUT_RAGIONE_SOCIALE]}<br>"
            f"Indirizzo:     {record[CSVColumns.OUTPUT_INDIRIZZO]}<br>"
            f"CAP:           {record[CSVColumns.OUTPUT_CAP]}    Città: {record[CSVColumns.OUTPUT_LOCALITA]}<br>"
            f"Provincia:     {record[CSVColumns.OUTPUT_PROVINCIA]}<br>"
            f"Telefono:      {record[CSVColumns.OUTPUT_TELEFONO_REF]}"
        )

        # Add saved data if present with colored background
        if (record[CSVColumns.OUTPUT_NUM_COLLI] and  # type: ignore
            record[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.EMPTY.value and  # type: ignore
            record[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.SKIP.value):  # type: ignore
            dest_info += (
                f"<br><br>"
                f"Colli: {record[CSVColumns.OUTPUT_NUM_COLLI]}<br>"
                f"Peso: {record[CSVColumns.OUTPUT_PESO_KG]} kg<br>"
                f"<div style='background-color: {Colors.SUCCESS}; color: white; padding: 5px; margin-top: 5px; font-weight: bold;'>"
                f"✓ SALVATO"
                f"</div>"
            )
        elif record[CSVColumns.OUTPUT_NUM_COLLI] == RecordStatus.SKIP.value:  # type: ignore
            dest_info += (
                f"<br><br>"
                f"<div style='background-color: #dc3545; color: white; padding: 5px; margin-top: 5px; font-weight: bold;'>"
                f"✗ SALTATO"
                f"</div>"
            )

        dest_info += "</div>"
        return dest_info

    def _update_input_fields(self, record: pd.Series) -> None:
        """Update input fields with record data or defaults.

        Args:
            record: DataFrame row containing shipment data
        """
        # Load shipment data if already filled (exclude SKIP)
        if (record[CSVColumns.OUTPUT_NUM_COLLI] and  # type: ignore
            record[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.SKIP.value):  # type: ignore
            self.colli_input.setText(str(record[CSVColumns.OUTPUT_NUM_COLLI]))
        else:
            self.colli_input.setText(str(self.default_colli))

        if (record[CSVColumns.OUTPUT_PESO_KG] and  # type: ignore
            record[CSVColumns.OUTPUT_PESO_KG] != RecordStatus.SKIP.value):  # type: ignore
            self.peso_input.setText(str(record[CSVColumns.OUTPUT_PESO_KG]))
        else:
            self.peso_input.setText(str(self.default_peso))

    def _update_progress_display(self) -> None:
        """Update progress bar and summary labels based on cached data."""
        # Update cache if needed
        self._update_cache()

        # Use cached values for progress calculation
        total = self._cache_total
        completed = self._cache_completed
        skipped = self._cache_skipped
        empty = self._cache_empty

        progress_pct = int((completed / total) * 100) if total > 0 else 0

        self.progress_label.setText(Messages.format(Messages.LABEL_PROGRESS,
                                                     current=self.current_index + 1,
                                                     total=total,
                                                     percent=progress_pct))
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(completed)

        if empty == 0 and skipped == 0:
            # All records are completed
            self.summary_label.setText(
                Messages.format(Messages.LABEL_SUMMARY_COMPLETE, total=total)
            )
        else:
            self.summary_label.setText(
                Messages.format(Messages.LABEL_SUMMARY, completed=completed, empty=empty, skipped=skipped)
            )

    def show_current_record(self) -> None:
        """Show the current record by updating all UI components."""

        if self.df_spedizioni is None or len(self.df_spedizioni) == 0:
            return

        # IMPORTANT: Verify that the index is valid
        if self.current_index >= len(self.df_spedizioni):  # type: ignore
            self.current_index = len(self.df_spedizioni) - 1
            return

        # Get current record
        record = self.df_spedizioni.iloc[self.current_index]

        # Update UI components
        self.dest_text.setHtml(self._format_recipient_info(record))
        self._update_input_fields(record)
        self._update_progress_display()

        # Enable/disable buttons based on position
        self.update_navigation_buttons()

    def _calculate_navigation_state(self) -> Dict[str, Any]:
        """Calculate the state for navigation buttons (business logic).

        Returns:
            Dict containing all button states and configuration
        """
        # Update cache if needed
        self._update_cache()

        # Use cached values
        total = self._cache_total
        empty_records = self._cache_empty
        skipped_records = self._cache_skipped

        is_last = self.current_index >= total - 1  # type: ignore
        is_first = self.current_index == 0

        # Check if all records are completed (NO empty, NO SKIP)
        all_completed = bool((empty_records == 0) and (skipped_records == 0))

        # Validate current input fields
        colli_valid = self.colli_input.text().strip() != ''
        peso_valid = self.peso_input.text().strip() != ''
        fields_valid = colli_valid and peso_valid

        # Determine if save is allowed
        if is_last:
            # At last record: activate ONLY if there are no skipped records
            can_save = fields_valid and (skipped_records == 0)
        else:
            # During navigation: activate if fields are valid
            can_save = fields_valid

        return {
            # Button enable/disable states
            'prev_enabled': not is_first,
            'skip_enabled': not is_last,
            'goto_skipped_visible': skipped_records > 0,
            'save_enabled': can_save if not all_completed else False,
            'export_enabled': all_completed,

            # Button appearance
            'all_completed': all_completed,
            'is_last': is_last,
            'can_save': can_save,
        }

    def _apply_navigation_state(self, state: Dict[str, Any]) -> None:
        """Apply calculated state to navigation buttons (UI logic).

        Args:
            state: Dictionary containing button states from _calculate_navigation_state
        """
        # Previous button
        self.prev_btn.setEnabled(state['prev_enabled'])

        # Skip button
        self.skip_btn.setEnabled(state['skip_enabled'])

        # "Go to Skipped" button
        self.goto_skipped_btn.setVisible(state['goto_skipped_visible'])

        # Save/Next button
        if state['all_completed']:
            # All completed: show "COMPLETATO" in gray
            self.save_next_btn.setText(Messages.BTN_COMPLETED)
            self.save_next_btn.setEnabled(False)
            self.save_next_btn.setStyleSheet(self._get_button_style('disabled'))
        else:
            self.save_next_btn.setEnabled(state['save_enabled'])

            if state['is_last']:
                # Last record: show "SAVE AND COMPLETE"
                self.save_next_btn.setText(Messages.BTN_SAVE_AND_COMPLETE)
                if state['can_save']:
                    self.save_next_btn.setStyleSheet(self._get_button_style('danger'))
                else:
                    self.save_next_btn.setStyleSheet(self._get_button_style('disabled'))
            else:
                # Regular record: show "SAVE AND NEXT"
                self.save_next_btn.setText(Messages.BTN_SAVE_AND_NEXT)
                if state['can_save']:
                    self.save_next_btn.setStyleSheet(self._get_button_style('primary'))
                else:
                    self.save_next_btn.setStyleSheet(self._get_button_style('disabled'))

        # Export button
        self.export_btn.setVisible(True)
        self.export_btn.setEnabled(state['export_enabled'])

        if state['export_enabled']:
            self.export_btn.setStyleSheet(self._get_button_style('info'))
        else:
            self.export_btn.setStyleSheet(self._get_button_style('disabled_export'))

    def update_navigation_buttons(self) -> None:
        """Update navigation button states by calculating and applying state."""

        if self.df_spedizioni is None or len(self.df_spedizioni) == 0:
            return

        # Calculate state (business logic)
        state = self._calculate_navigation_state()

        # Apply state to UI
        self._apply_navigation_state(state)

    def save_and_next_unified(self) -> None:
        """Unified button: save and next or save and export"""

        if self.df_spedizioni is None:
            return

        # Validate input
        validated_data = self._validate_shipment_data()
        if validated_data is None:
            return

        colli_int, peso_float = validated_data

        # Save data in current record using navigation handler
        self.navigation_handler.save_record_data(
            self.df_spedizioni, self.current_index, colli_int, peso_float
        )

        # Invalidate cache since DataFrame changed
        self._invalidate_cache()

        # Save to file
        self.save_data_to_file()

        # Navigate to next record (skip-mode aware)
        self.current_index = self.navigation_handler.handle_save_and_next_unified(
            self.df_spedizioni, self.current_index
        )

        # Update display
        self.show_current_record()

    def save_and_next(self) -> None:
        """Save current data and move to next"""

        if self.df_spedizioni is None:
            return

        # Check we're not already at the last record
        next_index = self.navigation_handler.go_to_next(self.df_spedizioni, self.current_index)
        if next_index is None:
            QMessageBox.warning(self, Messages.TITLE_WARNING,
                Messages.MSG_ALREADY_LAST)
            return

        # Validate input
        validated_data = self._validate_shipment_data()
        if validated_data is None:
            return

        colli_int, peso_float = validated_data

        # Save data in current record using navigation handler
        self.navigation_handler.save_record_data(
            self.df_spedizioni, self.current_index, colli_int, peso_float
        )

        # Invalidate cache since DataFrame changed
        self._invalidate_cache()

        # Save to file
        self.save_data_to_file()

        # Go to next
        self.current_index = next_index
        self.show_current_record()

    def save_current(self) -> None:
        """Save current record without moving to next"""

        if self.df_spedizioni is None:
            return

        # Validate input
        validated_data = self._validate_shipment_data()
        if validated_data is None:
            return

        colli_int, peso_float = validated_data

        # Save data in current record using navigation handler
        self.navigation_handler.save_record_data(
            self.df_spedizioni, self.current_index, colli_int, peso_float
        )

        # Invalidate cache since DataFrame changed
        self._invalidate_cache()

        # Save to file
        self.save_data_to_file()

        # Update display (stays on same record)
        self.show_current_record()

    def skip_item(self) -> None:
        """Skip current record"""

        if self.df_spedizioni is None:
            return

        # Mark as skipped using navigation handler
        self.navigation_handler.skip_current_record(self.df_spedizioni, self.current_index)

        # Invalidate cache since DataFrame changed
        self._invalidate_cache()

        # Save
        self.save_data_to_file()

        # Go to next
        self.current_index = self.navigation_handler.go_to_next_with_skip(
            self.df_spedizioni, self.current_index
        )
        self.show_current_record()

    def previous_item(self) -> None:
        """Go back to previous record"""

        prev_index = self.navigation_handler.go_to_previous(self.df_spedizioni, self.current_index)

        if prev_index is not None:
            self.current_index = prev_index
            self.show_current_record()

    def goto_next_skipped(self) -> None:
        """Go to next skipped record (SKIP)"""

        next_skipped = self.navigation_handler.goto_next_skipped(
            self.df_spedizioni, self.current_index
        )

        if next_skipped is not None:
            self.current_index = next_skipped
            self.show_current_record()

    def save_data_to_file(self) -> None:
        """Save compiled data to JSON file"""
        self.csv_handler.save_data_to_file(self.df_spedizioni)

    def load_saved_data(self) -> None:
        """Load previously saved data"""
        self.csv_handler.load_saved_data(self.df_spedizioni)
        # Invalidate cache since DataFrame might have changed
        if self.df_spedizioni is not None:
            self._invalidate_cache()

    def export_brt_csv(self) -> None:
        """Export final CSV for BRT"""

        # Use CSV handler to export file
        success, filename, num_exported = self.csv_handler.export_brt_csv(self.df_spedizioni)

        if success:
            # Update export label
            self.export_label.setText(
                Messages.format(Messages.LABEL_SHIPMENTS_EXPORTED,
                               count=num_exported,
                               filename=filename)
            )



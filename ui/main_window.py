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
                            BRTDefaults, CSVColumns, Messages, FilterType)
from core.utils import MONOSPACE_FONT, logger
from services.updater import UpdateDownloader, UpdateChecker
from .dialogs import DownloadDialog, AboutDialog
from .components.settings_manager import SettingsManager
from .components.csv_handler import CsvHandler
from .components.navigation_handler import NavigationHandler
from .components.ui_builder import UIBuilder


# Application metadata (imported from main module)
__version__ = "6.4.0"
__app_name__ = "Gestione Spedizioni IGEA <-> BRT"
__release_date__ = "2025-10-14"
__developer__ = "Marco De Luca"


class BRTSpedizioniApp(QMainWindow):
    """Main application for BRT shipping management"""

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
        self.default_peso: float = 1.0

        # BRT configurable fields (will be loaded from settings)
        self.brt_customer_code: str = BRTDefaults.DEFAULT_CUSTOMER_CODE
        self.brt_alphabetic_ref: str = BRTDefaults.DEFAULT_ALPHABETIC_REF
        self.brt_goods_type: str = BRTDefaults.DEFAULT_GOODS_TYPE
        self.brt_tariff_code: str = BRTDefaults.DEFAULT_TARIFF_CODE
        self.brt_service_type: str = BRTDefaults.DEFAULT_SERVICE_TYPE
        self.brt_note: str = BRTDefaults.DEFAULT_NOTE

        # Cache for DataFrame counts (to avoid repeated calculations)
        self._cache_total: int = 0
        self._cache_completed: int = 0
        self._cache_skipped: int = 0
        self._cache_empty: int = 0
        self._cache_dirty: bool = True

        # Filter state
        self.current_filter: FilterType = FilterType.ALL

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
        self.drag_drop_widget = main_widgets['drag_drop_widget']
        self.dest_text = main_widgets['dest_text']
        self.colli_input = main_widgets['colli_input']
        self.peso_input = main_widgets['peso_input']
        self.progress_label = main_widgets['progress_label']
        self.progress_bar = main_widgets['progress_bar']
        self.filter_all_btn = main_widgets['filter_all_btn']
        self.filter_completed_btn = main_widgets['filter_completed_btn']
        self.filter_todo_btn = main_widgets['filter_todo_btn']
        self.filter_skipped_btn = main_widgets['filter_skipped_btn']
        self.prev_btn = main_widgets['prev_btn']
        self.next_btn = main_widgets['next_btn']
        self.skip_btn = main_widgets['skip_btn']
        self.save_next_btn = main_widgets['save_next_btn']
        self.export_btn = main_widgets['export_btn']
        self.export_label = main_widgets['export_label']

        # Connect drag & drop signal
        self.drag_drop_widget.file_selected.connect(self.load_csv_from_path)

        # Assign settings input references
        self.settings_colli_input = settings_inputs['settings_colli_input']
        self.settings_peso_input = settings_inputs['settings_peso_input']
        self.settings_customer_code_input = settings_inputs['settings_customer_code_input']
        self.settings_alphabetic_ref_input = settings_inputs['settings_alphabetic_ref_input']
        self.settings_goods_type_input = settings_inputs['settings_goods_type_input']
        self.settings_tariff_code_input = settings_inputs['settings_tariff_code_input']
        self.settings_service_type_input = settings_inputs['settings_service_type_input']
        self.settings_note_input = settings_inputs['settings_note_input']

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
            'next': self.next_item,
            'skip': self.skip_item,
            'save_and_next_unified': self.save_and_next_unified,
            'export_csv': self.export_brt_csv,
            'filter_change': self.change_filter
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
            'brt_service_type': self.brt_service_type,
            'brt_note': self.brt_note
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
        self.settings_note_input.setText(self.brt_note)

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
            self.brt_note = self.settings_note_input.text().strip()

            # Save to file using SettingsManager
            settings_data = {
                'default_colli': self.default_colli,
                'default_peso': self.default_peso,
                'brt_customer_code': self.brt_customer_code,
                'brt_alphabetic_ref': self.brt_alphabetic_ref,
                'brt_goods_type': self.brt_goods_type,
                'brt_tariff_code': self.brt_tariff_code,
                'brt_service_type': self.brt_service_type,
                'brt_note': self.brt_note
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
        self.brt_note = settings.get('brt_note', BRTDefaults.DEFAULT_NOTE)  # Use default if not present

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


    def apply_template(self, colli: int, peso: float) -> None:
        """Apply quick template"""
        self.colli_input.setValue(colli)
        self.peso_input.setValue(peso)

    def load_csv(self) -> None:
        """Load and process the CSV file (via file dialog)"""
        self._load_csv_internal(file_path=None)

    def load_csv_from_path(self, file_path: str) -> None:
        """Load and process the CSV file from a specific path (drag & drop).

        Args:
            file_path: Path to the CSV file
        """
        self._load_csv_internal(file_path=file_path)

    def _load_csv_internal(self, file_path: Optional[str] = None) -> None:
        """Internal method to load and process the CSV file.

        Args:
            file_path: Optional path to CSV file. If None, shows file dialog.
        """
        # Prepare BRT configuration
        brt_config = {
            'brt_customer_code': self.brt_customer_code,
            'brt_goods_type': self.brt_goods_type,
            'brt_alphabetic_ref': self.brt_alphabetic_ref,
            'brt_tariff_code': self.brt_tariff_code,
            'brt_service_type': self.brt_service_type,
            'brt_note': self.brt_note
        }

        # Use CSV handler to load file
        result = self.csv_handler.load_csv(brt_config, file_path=file_path)

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
        # Get values directly from SpinBox widgets (no validation needed, always valid)
        colli_int = self.colli_input.value()
        peso_float = self.peso_input.value()

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
                - 'pill_active': Pill badge active filter button
                - 'pill_inactive': Pill badge inactive filter button

        Returns:
            str: CSS stylesheet string for the button
        """
        # Base style for all buttons
        base_style = "border: none; border-radius: 4px;"
        base_style_with_border = "border: 1px solid #cccccc; border-radius: 4px;"

        # Pill badge styles for filter buttons
        pill_active = """
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 11px;
            font-weight: bold;
        """

        pill_inactive = """
            background-color: transparent;
            color: #6c757d;
            border: 2px solid #dee2e6;
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: normal;
        """

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
            'plain': f"background-color: #f8f8f8; color: {Colors.TEXT_BLACK}; {base_style_with_border} padding: {UIConstants.BUTTON_PADDING_NORMAL};",
            'pill_active': pill_active,
            'pill_inactive': pill_inactive
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
            f"<div style='font-family: {MONOSPACE_FONT}; font-size: 11pt;'>"
            f"<span style='font-weight: bold; font-size: 12pt;'>N. Spedizione: {record[CSVColumns.OUTPUT_NUM_SPEDIZIONE]}</span><br>"
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
                f"<br>"
                f"Colli: {record[CSVColumns.OUTPUT_NUM_COLLI]}<br>"
                f"Peso: {record[CSVColumns.OUTPUT_PESO_KG]} kg"
                f"<div style='background-color: {Colors.SUCCESS}; color: white; padding: 5px; margin-top: 5px; font-size: 12pt; font-weight: bold;'>"
                f"✓ COMPLETATO"
                f"</div>"
            )
        elif record[CSVColumns.OUTPUT_NUM_COLLI] == RecordStatus.SKIP.value:  # type: ignore
            dest_info += (
                f"<br>"
                f"<div style='background-color: {Colors.DANGER}; color: white; padding: 5px; margin-top: 5px; font-size: 12pt; font-weight: bold;'>"
                f"✗ ESCLUSO"
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
            self.colli_input.setValue(int(record[CSVColumns.OUTPUT_NUM_COLLI]))
        else:
            self.colli_input.setValue(self.default_colli)

        if (record[CSVColumns.OUTPUT_PESO_KG] and  # type: ignore
            record[CSVColumns.OUTPUT_PESO_KG] != RecordStatus.SKIP.value):  # type: ignore
            self.peso_input.setValue(float(record[CSVColumns.OUTPUT_PESO_KG]))
        else:
            self.peso_input.setValue(self.default_peso)

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

        # Update filter button texts with counts
        self._update_filter_buttons()

    def _update_filter_buttons(self) -> None:
        """Update filter button texts with record counts and highlight active filter."""
        if self.df_spedizioni is None:
            return

        # Update cache if needed
        self._update_cache()

        # Use cached values
        total = self._cache_total
        completed = self._cache_completed
        skipped = self._cache_skipped
        empty = self._cache_empty

        # Update button texts with counts and filter icon
        filter_icon = "▼ "  # Triangle (funnel icon)

        if self.current_filter == FilterType.ALL:
            self.filter_all_btn.setText(f"{filter_icon}{Messages.BTN_FILTER_ALL} ({total})")
            self.filter_completed_btn.setText(f"{Messages.BTN_FILTER_COMPLETED} ({completed})")
            self.filter_todo_btn.setText(f"{Messages.BTN_FILTER_TODO} ({empty})")
            self.filter_skipped_btn.setText(f"{Messages.BTN_FILTER_SKIPPED} ({skipped})")
        elif self.current_filter == FilterType.COMPLETED:
            self.filter_all_btn.setText(f"{Messages.BTN_FILTER_ALL} ({total})")
            self.filter_completed_btn.setText(f"{filter_icon}{Messages.BTN_FILTER_COMPLETED} ({completed})")
            self.filter_todo_btn.setText(f"{Messages.BTN_FILTER_TODO} ({empty})")
            self.filter_skipped_btn.setText(f"{Messages.BTN_FILTER_SKIPPED} ({skipped})")
        elif self.current_filter == FilterType.TODO:
            self.filter_all_btn.setText(f"{Messages.BTN_FILTER_ALL} ({total})")
            self.filter_completed_btn.setText(f"{Messages.BTN_FILTER_COMPLETED} ({completed})")
            self.filter_todo_btn.setText(f"{filter_icon}{Messages.BTN_FILTER_TODO} ({empty})")
            self.filter_skipped_btn.setText(f"{Messages.BTN_FILTER_SKIPPED} ({skipped})")
        elif self.current_filter == FilterType.SKIPPED:
            self.filter_all_btn.setText(f"{Messages.BTN_FILTER_ALL} ({total})")
            self.filter_completed_btn.setText(f"{Messages.BTN_FILTER_COMPLETED} ({completed})")
            self.filter_todo_btn.setText(f"{Messages.BTN_FILTER_TODO} ({empty})")
            self.filter_skipped_btn.setText(f"{filter_icon}{Messages.BTN_FILTER_SKIPPED} ({skipped})")

        # Highlight active filter button with pill badge style
        if self.current_filter == FilterType.ALL:
            self.filter_all_btn.setStyleSheet(self._get_button_style('pill_active'))
            self.filter_completed_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_todo_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_skipped_btn.setStyleSheet(self._get_button_style('pill_inactive'))
        elif self.current_filter == FilterType.COMPLETED:
            self.filter_all_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_completed_btn.setStyleSheet(self._get_button_style('pill_active'))
            self.filter_todo_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_skipped_btn.setStyleSheet(self._get_button_style('pill_inactive'))
        elif self.current_filter == FilterType.TODO:
            self.filter_all_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_completed_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_todo_btn.setStyleSheet(self._get_button_style('pill_active'))
            self.filter_skipped_btn.setStyleSheet(self._get_button_style('pill_inactive'))
        elif self.current_filter == FilterType.SKIPPED:
            self.filter_all_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_completed_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_todo_btn.setStyleSheet(self._get_button_style('pill_inactive'))
            self.filter_skipped_btn.setStyleSheet(self._get_button_style('pill_active'))

    def change_filter(self, filter_type: FilterType) -> None:
        """Change the active filter and navigate to first matching record.

        Args:
            filter_type: The filter type to activate
        """
        if self.df_spedizioni is None:
            return

        # Update current filter
        self.current_filter = filter_type

        # Find first record matching the filter
        first_matching_idx = self._find_first_matching_record(filter_type)

        if first_matching_idx is not None:
            self.current_index = first_matching_idx
            self.show_current_record()
        else:
            # No records match the filter - stay on current record but update UI
            self._update_filter_buttons()

    def _find_first_matching_record(self, filter_type: FilterType) -> Optional[int]:
        """Find the first record that matches the given filter.

        Args:
            filter_type: The filter type to match

        Returns:
            Optional[int]: Index of first matching record, or None if no match
        """
        if self.df_spedizioni is None:
            return None

        for idx in range(len(self.df_spedizioni)):
            record = self.df_spedizioni.iloc[idx]
            num_colli = record[CSVColumns.OUTPUT_NUM_COLLI]

            if filter_type == FilterType.ALL:
                return 0  # ALL filter shows all records, start from first
            elif filter_type == FilterType.COMPLETED:
                # Completed: not empty and not SKIP
                if num_colli != '' and num_colli != RecordStatus.EMPTY.value and num_colli != RecordStatus.SKIP.value:
                    return idx
            elif filter_type == FilterType.TODO:
                # TODO: empty records
                if num_colli == '' or num_colli == RecordStatus.EMPTY.value:
                    return idx
            elif filter_type == FilterType.SKIPPED:
                # Skipped: SKIP status
                if num_colli == RecordStatus.SKIP.value:
                    return idx

        return None

    def _find_previous_matching_record(self, filter_type: FilterType, current_idx: int) -> Optional[int]:
        """Find the previous record that matches the given filter.

        Args:
            filter_type: The filter type to match
            current_idx: Current record index

        Returns:
            Optional[int]: Index of previous matching record, or None if no match
        """
        if self.df_spedizioni is None or current_idx == 0:
            return None

        # Search backwards from current index
        for idx in range(current_idx - 1, -1, -1):
            if self._record_matches_filter(idx, filter_type):
                return idx

        return None

    def _find_next_matching_record(self, filter_type: FilterType, current_idx: int) -> Optional[int]:
        """Find the next record that matches the given filter.

        Args:
            filter_type: The filter type to match
            current_idx: Current record index

        Returns:
            Optional[int]: Index of next matching record, or None if no match
        """
        if self.df_spedizioni is None:
            return None

        total = len(self.df_spedizioni)
        if current_idx >= total - 1:
            return None

        # Search forward from current index
        for idx in range(current_idx + 1, total):
            if self._record_matches_filter(idx, filter_type):
                return idx

        return None

    def _record_matches_filter(self, idx: int, filter_type: FilterType) -> bool:
        """Check if a record at given index matches the filter.

        Args:
            idx: Record index
            filter_type: The filter type to match

        Returns:
            bool: True if record matches filter, False otherwise
        """
        if self.df_spedizioni is None:
            return False

        record = self.df_spedizioni.iloc[idx]
        num_colli = record[CSVColumns.OUTPUT_NUM_COLLI]

        if filter_type == FilterType.ALL:
            return True  # ALL filter matches all records
        elif filter_type == FilterType.COMPLETED:
            # Completed: not empty and not SKIP
            return num_colli != '' and num_colli != RecordStatus.EMPTY.value and num_colli != RecordStatus.SKIP.value
        elif filter_type == FilterType.TODO:
            # TODO: empty records
            return num_colli == '' or num_colli == RecordStatus.EMPTY.value
        elif filter_type == FilterType.SKIPPED:
            # Skipped: SKIP status
            return num_colli == RecordStatus.SKIP.value

        return False

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
        completed_records = self._cache_completed

        # Check if we're at the last record considering the active filter
        is_last_in_dataframe = self.current_index >= total - 1  # type: ignore
        is_last_in_filter = self._find_next_matching_record(self.current_filter, self.current_index) is None
        is_last = is_last_in_filter  # Use filter-aware "last" check

        # Check if we're at the first record considering the active filter
        is_first_in_dataframe = self.current_index == 0
        is_first_in_filter = self._find_previous_matching_record(self.current_filter, self.current_index) is None
        is_first = is_first_in_filter  # Use filter-aware "first" check

        # Check if current record is processed (completed or skipped)
        current_record = self.df_spedizioni.iloc[self.current_index]
        is_current_processed = (
            current_record[CSVColumns.OUTPUT_NUM_COLLI] != '' and
            current_record[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.EMPTY.value
        )

        # Check if all records are completed (NO empty, NO SKIP)
        all_completed = bool((empty_records == 0) and (skipped_records == 0))

        # Export rules:
        # - Enabled: if all records are completed (no TODO, no SKIPPED)
        # - Enabled: if there are completed + skipped records (but no TODO)
        # - Disabled: if there are TODO records
        # - Disabled: if all records are skipped (no completed)
        can_export = (completed_records > 0) and (empty_records == 0)

        # SpinBox/DoubleSpinBox always have valid values, so fields are always valid
        fields_valid = True

        # Determine if save is allowed
        # In COMPLETED filter, save button should always be disabled
        if self.current_filter == FilterType.COMPLETED:
            can_save = False
        elif is_last:
            # At last record in filter
            if self.current_filter == FilterType.ALL and is_last_in_dataframe:
                # Special case: filter TUTTI at absolute last record
                # Only allow if there's exactly 1 record left to do (the current one)
                can_save = fields_valid and (empty_records == 1)
            else:
                # For all other cases (filtered views), allow saving at last filtered record
                can_save = fields_valid
        else:
            # During navigation: activate if fields are valid
            can_save = fields_valid

        # Previous/Next buttons: allow free navigation in all filter types
        # Users should be able to navigate freely through records regardless of completion status
        prev_enabled = not is_first
        next_enabled = not is_last

        # Skip button behavior depends on active filter:
        # - In COMPLETED filter: enable skip button to allow changing completed records to skipped
        # - In SKIPPED filter: disable skip button (records are already skipped)
        # - In other filters: enable if not at last record
        if self.current_filter == FilterType.COMPLETED:
            skip_enabled = True  # Allow skipping completed records
        elif self.current_filter == FilterType.SKIPPED:
            skip_enabled = False  # Already skipped
        else:
            skip_enabled = not is_last

        return {
            # Button enable/disable states
            'prev_enabled': prev_enabled,
            'next_enabled': next_enabled,
            'skip_enabled': skip_enabled,
            'save_enabled': can_save if not all_completed else False,
            'export_enabled': can_export,

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

        # Next button
        self.next_btn.setEnabled(state['next_enabled'])

        # Skip button - update text and style based on active filter
        self.skip_btn.setEnabled(state['skip_enabled'])
        self.skip_btn.setText(Messages.BTN_SKIP)

        # Apply style based on enabled/disabled state
        if state['skip_enabled']:
            self.skip_btn.setStyleSheet(self._get_button_style('danger'))
        else:
            self.skip_btn.setStyleSheet(self._get_button_style('disabled'))

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
                    self.save_next_btn.setStyleSheet(self._get_button_style('success'))
                else:
                    self.save_next_btn.setStyleSheet(self._get_button_style('disabled'))
            else:
                # Regular record: show "SAVE AND NEXT"
                self.save_next_btn.setText(Messages.BTN_SAVE_AND_NEXT)
                if state['can_save']:
                    self.save_next_btn.setStyleSheet(self._get_button_style('success'))
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

        # Navigate to next record matching the current filter
        next_index = self._find_next_matching_record(self.current_filter, self.current_index)

        if next_index is not None:
            self.current_index = next_index
        # else: stay on current record (we're at the last matching record)

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

        # Navigate to next record matching the current filter
        next_index = self._find_next_matching_record(self.current_filter, self.current_index)

        if next_index is not None:
            self.current_index = next_index
        # else: stay on current record (we're at the last matching record)

        self.show_current_record()

    def previous_item(self) -> None:
        """Go back to previous record (respecting current filter)"""

        if self.df_spedizioni is None:
            return

        # Find previous record matching current filter
        prev_index = self._find_previous_matching_record(self.current_filter, self.current_index)

        if prev_index is not None:
            self.current_index = prev_index
            self.show_current_record()

    def next_item(self) -> None:
        """Go forward to next record (respecting current filter)"""

        if self.df_spedizioni is None:
            return

        # Find next record matching current filter
        next_index = self._find_next_matching_record(self.current_filter, self.current_index)

        if next_index is not None:
            self.current_index = next_index
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



"""
CSV Handler module for BRT Shipping Management Application
Manages CSV loading and export operations
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from core.constants import (CSVColumns, RecordStatus, BRTDefaults,
                            FileSettings, Messages)
from core.utils import logger


class CsvHandler:
    """Handles CSV file loading and export operations"""

    def __init__(self, parent: QWidget, save_file: Path):
        """Initialize CSV handler.

        Args:
            parent: Parent widget for dialogs
            save_file: Path to JSON save file
        """
        self.parent = parent
        self.save_file = save_file

    def load_csv(self, brt_config: Dict[str, str]) -> Optional[Tuple[pd.DataFrame, str, int, int]]:
        """Load and process the CSV file.

        Args:
            brt_config: Dictionary with BRT configuration fields:
                - brt_customer_code
                - brt_goods_type
                - brt_alphabetic_ref
                - brt_tariff_code
                - brt_service_type

        Returns:
            Optional[Tuple[pd.DataFrame, str, int, int]]: (DataFrame, filename, num_rows, duplicates) or None if cancelled/error
        """
        default_dir = Path.home() / "Documents"
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            Messages.FILE_DIALOG_TITLE_LOAD,
            str(default_dir),
            Messages.FILE_DIALOG_FILTER
        )

        if not file_path:
            return None

        csv_path = Path(file_path)

        try:
            # Read CSV forcing text columns as strings
            # SpedLocalita2 (phone) and SpedCAP must be strings to avoid float conversion
            df = pd.read_csv(str(csv_path), sep=';', encoding='utf-8', dtype={
                CSVColumns.INPUT_TELEFONO: str,
                CSVColumns.INPUT_CAP: str
            })

            # Verify required columns
            required_cols = CSVColumns.get_required_input_columns()

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                QMessageBox.critical(self.parent, Messages.TITLE_ERROR,
                    Messages.format(Messages.MSG_MISSING_COLUMNS, columns=', '.join(missing_cols)))
                return None

            # Select only required columns
            df = df[required_cols].copy()

            # Ensure phone and CAP are clean strings (remove NaN)
            df[CSVColumns.INPUT_TELEFONO] = df[CSVColumns.INPUT_TELEFONO].fillna('').astype(str)
            df[CSVColumns.INPUT_CAP] = df[CSVColumns.INPUT_CAP].fillna('').astype(str)

            # Remove duplicates based on registration number
            df_unique = df.drop_duplicates(subset=[CSVColumns.INPUT_NUMERO], keep='first')

            # Rename columns according to BRT mapping
            df_unique = df_unique.rename(columns=CSVColumns.get_column_mapping())

            # Duplicate shipment number for sender reference
            df_unique[CSVColumns.OUTPUT_RIF_MITTENTE] = df_unique[CSVColumns.OUTPUT_NUM_SPEDIZIONE]

            # Mobile must contain phone (already mapped)
            df_unique[CSVColumns.OUTPUT_CELLULARE] = df_unique[CSVColumns.OUTPUT_TELEFONO_REF]

            # Add columns for data to be filled
            df_unique[CSVColumns.OUTPUT_NUM_COLLI] = RecordStatus.EMPTY.value
            df_unique[CSVColumns.OUTPUT_PESO_KG] = RecordStatus.EMPTY.value

            # Add fixed fields (use configurable values)
            df_unique[CSVColumns.OUTPUT_ABBUONO_TB] = BRTDefaults.DEFAULT_ABBUONO
            df_unique[CSVColumns.OUTPUT_COD_CLIENTE] = brt_config['brt_customer_code']
            df_unique[CSVColumns.OUTPUT_NATURA_SPEDIZIONE] = brt_config['brt_goods_type']
            df_unique[CSVColumns.OUTPUT_RIF_ALFABETICO] = brt_config['brt_alphabetic_ref']
            df_unique[CSVColumns.OUTPUT_COD_TARIFFA] = brt_config['brt_tariff_code']
            df_unique[CSVColumns.OUTPUT_NAZIONE_DEST] = BRTDefaults.DEFAULT_COUNTRY_DEST
            df_unique[CSVColumns.OUTPUT_TIPO_SERVIZIO] = brt_config['brt_service_type']

            # Delete saved JSON (new file = new session)
            if self.save_file.exists():
                self.save_file.unlink()

            # Success message
            num_rows = len(df_unique)
            num_orig = len(df)
            duplicates = num_orig - num_rows

            logger.info(f"Successfully loaded CSV file with {num_rows} unique shipments ({duplicates} duplicates removed)")

            QMessageBox.information(self.parent, Messages.TITLE_SUCCESS,
                Messages.format(Messages.MSG_FILE_LOADED, count=num_rows, duplicates=duplicates))

            return df_unique, csv_path.name, num_rows, duplicates

        except Exception as e:
            logger.error(f"Failed to load CSV file {csv_path}: {e}", exc_info=True)
            QMessageBox.critical(self.parent, Messages.TITLE_ERROR,
                Messages.format(Messages.MSG_FILE_LOAD_ERROR, error=str(e)))
            return None

    def export_brt_csv(self, df_spedizioni: Optional[pd.DataFrame]) -> Tuple[bool, str, int]:
        """Export final CSV for BRT.

        Args:
            df_spedizioni: DataFrame with shipment data (can be None)

        Returns:
            Tuple[bool, str, int]: (success, filename, num_exported)
        """
        if df_spedizioni is None:
            QMessageBox.warning(self.parent, Messages.TITLE_WARNING, Messages.MSG_LOAD_CSV_FIRST)
            return False, "", 0

        # Filter only completed records
        df_export = df_spedizioni[
            (df_spedizioni[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.EMPTY.value) &
            (df_spedizioni[CSVColumns.OUTPUT_NUM_COLLI] != RecordStatus.SKIP.value)
        ].copy()

        if len(df_export) == 0:
            QMessageBox.warning(self.parent, Messages.TITLE_WARNING,
                Messages.MSG_NO_RECORDS_TO_EXPORT)
            return False, "", 0

        # Order columns according to BRT specification
        colonne_brt = CSVColumns.get_brt_column_order()

        # Add missing columns if necessary
        for col in colonne_brt:
            if col not in df_export.columns:
                df_export[col] = RecordStatus.EMPTY.value

        # Select and order columns
        df_export = df_export[colonne_brt]

        # Ask where to save
        default_filename = f"{FileSettings.CSV_EXPORT_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = Path.home() / "Documents" / default_filename
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            Messages.FILE_DIALOG_TITLE_SAVE,
            str(default_path),
            Messages.FILE_DIALOG_FILTER
        )

        if not file_path:
            return False, "", 0

        export_path = Path(file_path)

        try:
            # Export CSV (with header, semicolon separator)
            df_export.to_csv(str(export_path), sep=';', index=False, header=True, encoding='utf-8')

            logger.info(f"Successfully exported {len(df_export)} shipments to {export_path}")

            QMessageBox.information(self.parent, Messages.TITLE_SUCCESS,
                Messages.format(Messages.MSG_FILE_EXPORTED,
                               count=len(df_export),
                               filename=export_path.name))

            return True, export_path.name, len(df_export)

        except Exception as e:
            logger.error(f"Failed to export BRT CSV to {export_path}: {e}", exc_info=True)
            QMessageBox.critical(self.parent, Messages.TITLE_ERROR,
                Messages.format(Messages.MSG_FILE_EXPORT_ERROR, error=str(e)))
            return False, "", 0

    def save_data_to_file(self, df_spedizioni: Optional[pd.DataFrame]) -> None:
        """Save compiled data to JSON file.

        Args:
            df_spedizioni: DataFrame with shipment data (can be None)
        """
        if df_spedizioni is None:
            return

        try:
            # Save ONLY completed records (with non-empty VABNCL)
            df_to_save = df_spedizioni[df_spedizioni['VABNCL'] != ''][['VABNSP', 'VABNCL', 'VABPKB']]

            data = {
                'last_modified': datetime.now().isoformat(),
                'data': df_to_save.to_dict('records')
            }

            with open(str(self.save_file), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save data to {self.save_file}: {e}", exc_info=True)

    def load_saved_data(self, df_spedizioni: Optional[pd.DataFrame]) -> None:
        """Load previously saved data into DataFrame.

        Args:
            df_spedizioni: DataFrame to load data into (can be None)
        """
        if not self.save_file.exists() or df_spedizioni is None:
            return

        try:
            with open(str(self.save_file), 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Restore completed data
            for item in data['data']:
                mask = df_spedizioni['VABNSP'] == item['VABNSP']
                if mask.any():
                    idx = df_spedizioni[mask].index[0]
                    df_spedizioni.at[idx, 'VABNCL'] = item['VABNCL']
                    df_spedizioni.at[idx, 'VABPKB'] = item['VABPKB']

        except Exception as e:
            logger.error(f"Failed to load saved data from {self.save_file}: {e}", exc_info=True)
            # Continue without restoring data - user will start fresh

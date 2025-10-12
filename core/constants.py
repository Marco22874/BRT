"""
Constants module for BRT Shipping Management Application
Contains all constant values, enums, and configuration settings
"""

from enum import Enum
from typing import Dict, List, Any


class UIConstants:
    """Constants for UI dimensions and spacing"""
    # Window dimensions
    WINDOW_WIDTH = 900
    WINDOW_HEIGHT = 800
    WINDOW_X = 100
    WINDOW_Y = 100

    # Logo dimensions
    LOGO_HEIGHT = 80
    LOGO_HEIGHT_DIALOG = 60

    # Input dimensions
    INPUT_WIDTH_SMALL = 100
    INPUT_WIDTH_MEDIUM = 150

    # Text dimensions
    DEST_TEXT_HEIGHT = 150
    DIALOG_MIN_WIDTH = 500

    # Spacing
    SPACING_SMALL = 10
    SPACING_MEDIUM = 20
    SPACING_LARGE = 50

    # Font size
    FONT_SIZE_TITLE = 20
    FONT_SIZE_SECTION = 14
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_LARGE = 24
    FONT_SIZE_ARROWS = 32

    # Button padding
    BUTTON_PADDING_NORMAL = "8px 15px"
    BUTTON_PADDING_LARGE = "10px 20px"
    BUTTON_PADDING_EXTRA = "10px"


class Colors:
    """Constants for UI colors"""
    # Primary colors
    PRIMARY = "#16FEBC"
    SUCCESS = "#28a745"
    DANGER = "#DC012E"
    WARNING = "#FFA500"
    INFO = "#5F38E6"
    SECONDARY = "#6c757d"

    # Status colors
    DISABLED = "#CCCCCC"
    DISABLED_TEXT = "#666666"

    # Text colors
    TEXT_GRAY = "#666666"
    TEXT_BLACK = "#333333"
    TEXT_WHITE = "white"

    # Background colors
    BG_LIGHT_GRAY = "#f0f0f0"
    BG_BLACK = "#000000"


class RecordStatus(Enum):
    """Enum for record status"""
    EMPTY = ""
    SKIP = "SKIP"

    def __str__(self):
        """Returns the enum value as a string"""
        return self.value


class FileSettings:
    """Constants for files and paths"""
    DATA_FILE = "brt_spedizioni_data.json"
    SETTINGS_FILE = "brt_settings.json"
    LOGO_IGEA = "igea_logo.png"
    LOGO_BRT = "Logo_BRT.svg.png"
    UPDATE_SCRIPT_WIN = "update_brt.bat"
    UPDATE_SCRIPT_MAC = "update_brt.sh"
    TEMP_UPDATE_DIR = "temp_update"
    CSV_EXPORT_PREFIX = "spedizioni_BRT_"


class BRTDefaults:
    """Default values for BRT fixed fields"""
    # Customer information
    DEFAULT_CUSTOMER_CODE = '0091808'
    DEFAULT_ALPHABETIC_REF = 'IGEA SRL'

    # Shipment defaults
    DEFAULT_GOODS_TYPE = 'DISPOSITIVI MEDICI'
    DEFAULT_TARIFF_CODE = '100'
    DEFAULT_SERVICE_TYPE = 'C'  # Express service

    # Fixed values for Italy
    DEFAULT_ABBUONO = ''  # Empty for Italy
    DEFAULT_COUNTRY_DEST = ''  # Empty for Italy


class NetworkSettings:
    """Constants for network settings"""
    GITHUB_REPO = "Marco22874/BRT"
    USER_AGENT = "BRT-Spedizioni-App"
    TIMEOUT_SHORT = 5
    TIMEOUT_MEDIUM = 30
    CHUNK_SIZE = 8192


class CSVColumns:
    """Constants for CSV column names and BRT mapping"""

    # Input CSV Columns (IGEA)
    INPUT_NUMERO = "RegisNumero"
    INPUT_RAGIONE_SOCIALE = "SpedRagSoc1"
    INPUT_INDIRIZZO = "SpedIndirizzo"
    INPUT_LOCALITA = "SpedLocalita"
    INPUT_TELEFONO = "SpedLocalita2"
    INPUT_CAP = "SpedCAP"
    INPUT_PROVINCIA = "SpedProvincia"
    INPUT_COD_PORTO = "AccompCodPorto"

    # BRT Output Columns
    OUTPUT_NUM_SPEDIZIONE = "VABNSP"
    OUTPUT_RAGIONE_SOCIALE = "VABRSD"
    OUTPUT_INDIRIZZO = "VABIND"
    OUTPUT_LOCALITA = "VABLOD"
    OUTPUT_TELEFONO_REF = "VABTRC"
    OUTPUT_CAP = "VABCAD"
    OUTPUT_PROVINCIA = "VABPRD"
    OUTPUT_COD_PORTO = "VABCBO"
    OUTPUT_RIF_MITTENTE = "VABRMN"
    OUTPUT_CELLULARE = "VABCEL"
    OUTPUT_NUM_COLLI = "VABNCL"
    OUTPUT_PESO_KG = "VABPKB"

    # Fixed BRT Columns
    OUTPUT_ABBUONO_TB = "VABATB"
    OUTPUT_COD_CLIENTE = "VABCCM"
    OUTPUT_NATURA_SPEDIZIONE = "VABNAS"
    OUTPUT_RIF_ALFABETICO = "VABRMA"
    OUTPUT_COD_TARIFFA = "VABCTR"
    OUTPUT_NAZIONE_DEST = "VABNZD"
    OUTPUT_TIPO_SERVIZIO = "VABTSP"

    @classmethod
    def get_required_input_columns(cls) -> List[str]:
        """Returns the list of required columns from the input CSV"""
        return [
            cls.INPUT_NUMERO,
            cls.INPUT_RAGIONE_SOCIALE,
            cls.INPUT_INDIRIZZO,
            cls.INPUT_LOCALITA,
            cls.INPUT_TELEFONO,
            cls.INPUT_CAP,
            cls.INPUT_PROVINCIA,
            cls.INPUT_COD_PORTO
        ]

    @classmethod
    def get_column_mapping(cls) -> Dict[str, str]:
        """Returns the mapping from input columns to output columns"""
        return {
            cls.INPUT_NUMERO: cls.OUTPUT_NUM_SPEDIZIONE,
            cls.INPUT_RAGIONE_SOCIALE: cls.OUTPUT_RAGIONE_SOCIALE,
            cls.INPUT_INDIRIZZO: cls.OUTPUT_INDIRIZZO,
            cls.INPUT_LOCALITA: cls.OUTPUT_LOCALITA,
            cls.INPUT_TELEFONO: cls.OUTPUT_TELEFONO_REF,
            cls.INPUT_CAP: cls.OUTPUT_CAP,
            cls.INPUT_PROVINCIA: cls.OUTPUT_PROVINCIA,
            cls.INPUT_COD_PORTO: cls.OUTPUT_COD_PORTO
        }

    @classmethod
    def get_brt_column_order(cls) -> List[str]:
        """Returns the column order for BRT export"""
        return [
            cls.OUTPUT_ABBUONO_TB,
            cls.OUTPUT_COD_CLIENTE,
            cls.OUTPUT_NUM_SPEDIZIONE,
            cls.OUTPUT_COD_PORTO,
            cls.OUTPUT_RAGIONE_SOCIALE,
            cls.OUTPUT_INDIRIZZO,
            cls.OUTPUT_CAP,
            cls.OUTPUT_LOCALITA,
            cls.OUTPUT_PROVINCIA,
            cls.OUTPUT_NAZIONE_DEST,
            cls.OUTPUT_COD_TARIFFA,
            cls.OUTPUT_TIPO_SERVIZIO,
            cls.OUTPUT_NATURA_SPEDIZIONE,
            cls.OUTPUT_NUM_COLLI,
            cls.OUTPUT_PESO_KG,
            cls.OUTPUT_RIF_MITTENTE,
            cls.OUTPUT_RIF_ALFABETICO,
            cls.OUTPUT_TELEFONO_REF,
            cls.OUTPUT_CELLULARE
        ]


class Messages:
    """Centralized messages for user interface - facilitates translation and maintenance"""

    # Dialog Titles
    TITLE_WARNING = "Attenzione"
    TITLE_ERROR = "Errore"
    TITLE_SUCCESS = "Successo"
    TITLE_INFO = "Info"
    TITLE_UPDATE_AVAILABLE = "Aggiornamento Disponibile"
    TITLE_DOWNLOAD = "Download in corso"
    TITLE_INSTALL_ERROR = "Errore Installazione"
    TITLE_DOWNLOAD_ERROR = "Errore Download"

    # Validation Messages
    MSG_EMPTY_FIELDS = "Compilare tutti i campi (colli e peso)"
    MSG_POSITIVE_VALUES = "Colli e peso devono essere maggiori di zero"
    MSG_INVALID_VALUES = "Valori non validi per colli o peso"
    MSG_INVALID_SETTINGS = "Valori non validi. Inserire numeri validi."
    MSG_SETTINGS_POSITIVE = "I valori devono essere maggiori di zero"

    # File Operations
    MSG_LOAD_CSV_FIRST = "Carica prima un file CSV"
    MSG_NO_RECORDS_TO_EXPORT = "Nessun record completato da esportare"
    MSG_MISSING_COLUMNS = "Colonne mancanti nel CSV:\n{columns}"
    MSG_FILE_LOAD_ERROR = "Errore nel caricamento del file:\n{error}"
    MSG_FILE_EXPORT_ERROR = "Errore nell'esportazione:\n{error}"

    # Success Messages
    MSG_FILE_LOADED = "File caricato con successo!\n\nSpedizioni uniche: {count}\nDuplicati rimossi: {duplicates}"
    MSG_FILE_EXPORTED = "File esportato con successo!\n\nSpedizioni esportate: {count}\nFile: {filename}\n\nOra puoi caricare questo file sul gestionale BRT."
    MSG_SETTINGS_SAVED = "Impostazioni salvate con successo!"

    # Navigation Messages
    MSG_ALREADY_LAST = "Sei già all'ultimo record!\n\nNon ci sono altri clienti da compilare."
    MSG_NO_SKIPPED = "Non ci sono record saltati da compilare!"

    # Update Messages
    MSG_UPDATE_AVAILABLE = """<div style='text-align: center;'>
<h3>Nuova versione disponibile!</h3>
<p>È disponibile la versione <b>{new_version}</b></p>
<p>Versione attuale: <b>{current_version}</b></p>
<br>
<p>Vuoi scaricare l'aggiornamento?</p>
</div>"""
    MSG_UPDATE_DOWNLOADING = "Download di {filename} in corso...\n\nL'applicazione verrà chiusa e aggiornata automaticamente."
    MSG_UPDATE_INSTALL_ERROR = "Impossibile installare l'aggiornamento:\n\n{error}\n\nIl file è stato salvato in:\n{path}"
    MSG_UPDATE_DOWNLOAD_ERROR = "Impossibile scaricare l'aggiornamento:\n\n{error}"

    # Button Labels
    BTN_COMPLETED = "✓ COMPLETATO"
    BTN_SAVE_AND_COMPLETE = "✓ SALVA E COMPLETA"
    BTN_SAVE_AND_NEXT = "✓ SALVA E SUCCESSIVO ▶"
    BTN_LOAD_CSV = "Carica file .csv"
    BTN_EXPORT_CSV = "↑ Esporta CSV per BRT"
    BTN_PREVIOUS = "◀ Precedente"
    BTN_SKIP = "Salta"
    BTN_GOTO_SKIPPED = "↻ Vai a Saltati"
    BTN_BACK = "← Torna Indietro"
    BTN_SAVE_SETTINGS = "✓ Salva Impostazioni"
    BTN_OK = "OK"
    BTN_DOWNLOAD_NOW = "Scarica Ora"
    BTN_REMIND_LATER = "Ricordamelo dopo"
    BTN_TEMPLATE_1 = "1 collo - 5kg"
    BTN_TEMPLATE_2 = "1 collo - 10kg"
    BTN_TEMPLATE_3 = "2 colli - 15kg"

    # Status Labels
    LABEL_NO_FILE = "Nessun file caricato"
    LABEL_FILE_LOADED = "✓ {filename}"
    LABEL_SHIPMENTS_LOADED = "✓ {count} spedizioni caricate ({duplicates} duplicati rimossi)"
    LABEL_SHIPMENTS_EXPORTED = "✓ Esportate {count} spedizioni in:\n{filename}"
    LABEL_PROGRESS = "Cliente {current}/{total} ({percent}%)"
    LABEL_PROGRESS_DEFAULT = "0/0 (0%)"
    LABEL_SUMMARY = "COMPLETATI: {completed} ✓  |  DA FARE: {empty}  |  SALTATI: {skipped}"
    LABEL_SUMMARY_COMPLETE = "<span style='background-color: #28a745; color: white; padding: 5px 10px; font-weight: bold; border-radius: 3px;'>✓ COMPLETO - Tutti i {total} record compilati!</span>"

    # UI Section Titles
    SECTION_STEP1 = "STEP 1: Carica File CSV"
    SECTION_STEP2 = "STEP 2: Compila Dati Spedizione"
    SECTION_STEP3 = "STEP 3: Genera CSV per BRT"

    # UI Field Labels
    LABEL_RECIPIENT = "Destinatario (da CSV)"
    LABEL_SHIPMENT_DATA = "Dati Spedizione (da compilare)"
    LABEL_NUM_PACKAGES = "N. Colli:"
    LABEL_TOTAL_WEIGHT = "Peso tot (kg):"
    LABEL_QUICK_TEMPLATES = "Template rapidi:"
    LABEL_DEFAULT_PACKAGES = "N. Colli di default:"
    LABEL_DEFAULT_WEIGHT = "Peso di default (kg):"
    LABEL_CUSTOMER_CODE = "Codice Cliente:"
    LABEL_ALPHABETIC_REF = "Riferimento Alfabetico:"
    LABEL_GOODS_TYPE = "Natura Spedizione:"
    LABEL_TARIFF_CODE = "Codice Tariffa:"
    LABEL_SERVICE_TYPE = "Tipo Servizio:"

    # Settings Screen
    SETTINGS_TITLE = "IMPOSTAZIONI"
    SETTINGS_DESCRIPTION = "Imposta i valori di default per il numero di colli e il peso delle spedizioni, e i campi fissi per BRT"
    SETTINGS_GROUP_DEFAULTS = "Valori di Default Spedizione"
    SETTINGS_GROUP_BRT = "Campi Fissi BRT"

    # File Dialog
    FILE_DIALOG_TITLE_LOAD = "Seleziona LISTADDT.csv"
    FILE_DIALOG_TITLE_SAVE = "Salva CSV per BRT"
    FILE_DIALOG_FILTER = "CSV files (*.csv);;All files (*.*)"

    @classmethod
    def format(cls, message: str, **kwargs: Any) -> str:
        """Format a message with given parameters.

        Args:
            message: Message template to format
            **kwargs: Parameters to substitute in the message

        Returns:
            str: Formatted message
        """
        return message.format(**kwargs)

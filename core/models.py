"""
Models module for BRT Shipping Management Application
Contains data models and business logic for settings and shipment data
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from .constants import BRTDefaults, FileSettings


@dataclass
class AppSettings:
    """Application settings data model"""
    default_colli: int = 1
    default_peso: float = 2.0
    brt_customer_code: str = BRTDefaults.DEFAULT_CUSTOMER_CODE
    brt_alphabetic_ref: str = BRTDefaults.DEFAULT_ALPHABETIC_REF
    brt_goods_type: str = BRTDefaults.DEFAULT_GOODS_TYPE
    brt_tariff_code: str = BRTDefaults.DEFAULT_TARIFF_CODE
    brt_service_type: str = BRTDefaults.DEFAULT_SERVICE_TYPE

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary for JSON serialization.

        Returns:
            Dict[str, Any]: Dictionary containing all settings fields with their current values.
                Keys include: default_colli, default_peso, brt_customer_code,
                brt_alphabetic_ref, brt_goods_type, brt_tariff_code, brt_service_type
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """
        Create settings instance from dictionary.

        Args:
            data: Dictionary containing settings values. Missing keys will use default values.
                Expected keys: default_colli, default_peso, brt_customer_code,
                brt_alphabetic_ref, brt_goods_type, brt_tariff_code, brt_service_type

        Returns:
            AppSettings: New instance with values from dictionary or defaults for missing keys
        """
        return cls(
            default_colli=data.get('default_colli', 1),
            default_peso=data.get('default_peso', 2.0),
            brt_customer_code=data.get('brt_customer_code', BRTDefaults.DEFAULT_CUSTOMER_CODE),
            brt_alphabetic_ref=data.get('brt_alphabetic_ref', BRTDefaults.DEFAULT_ALPHABETIC_REF),
            brt_goods_type=data.get('brt_goods_type', BRTDefaults.DEFAULT_GOODS_TYPE),
            brt_tariff_code=data.get('brt_tariff_code', BRTDefaults.DEFAULT_TARIFF_CODE),
            brt_service_type=data.get('brt_service_type', BRTDefaults.DEFAULT_SERVICE_TYPE)
        )

    def save_to_file(self, file_path: Path) -> None:
        """
        Save settings to JSON file.

        Serializes the current settings to a JSON file with UTF-8 encoding and indentation.

        Args:
            file_path: Path object pointing to the destination JSON file

        Raises:
            OSError: If the file cannot be written due to permissions or disk space
            TypeError: If settings contain non-serializable objects
        """
        with open(str(file_path), 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional['AppSettings']:
        """
        Load settings from JSON file.

        Reads and deserializes settings from a JSON file. Returns None if the file
        doesn't exist or cannot be parsed.

        Args:
            file_path: Path object pointing to the JSON file to load

        Returns:
            Optional[AppSettings]: Settings instance if successful, None if file doesn't exist
                or if JSON parsing/loading fails

        Raises:
            No exceptions are raised; errors are silently handled and None is returned
        """
        if not file_path.exists():
            return None

        try:
            with open(str(file_path), 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception:
            return None


@dataclass
class ShipmentRecord:
    """Single shipment record data model"""
    numero_spedizione: str
    num_colli: str
    peso_kg: str

    def to_dict(self) -> Dict[str, str]:
        """
        Convert shipment record to dictionary.

        Returns:
            Dict[str, str]: Dictionary with BRT field names as keys (VABNSP, VABNCL, VABPKB)
                and corresponding shipment values (numero_spedizione, num_colli, peso_kg)
        """
        return {
            'VABNSP': self.numero_spedizione,
            'VABNCL': self.num_colli,
            'VABPKB': self.peso_kg
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'ShipmentRecord':
        """
        Create shipment record from dictionary.

        Args:
            data: Dictionary with BRT field names as keys. Required keys: VABNSP, VABNCL, VABPKB

        Returns:
            ShipmentRecord: New instance with values from dictionary

        Raises:
            KeyError: If required keys are missing from the dictionary
        """
        return cls(
            numero_spedizione=data['VABNSP'],
            num_colli=data['VABNCL'],
            peso_kg=data['VABPKB']
        )


class ShipmentDataManager:
    """Manages shipment data persistence"""

    def __init__(self, file_path: Path):
        """
        Initialize the shipment data manager.

        Args:
            file_path: Path object pointing to the JSON file for storing shipment data
        """
        self.file_path = file_path

    def save(self, records: list[ShipmentRecord]) -> None:
        """
        Save shipment records to JSON file.

        Serializes a list of shipment records to JSON format with timestamp and UTF-8 encoding.

        Args:
            records: List of ShipmentRecord instances to save

        Raises:
            OSError: If the file cannot be written due to permissions or disk space
            TypeError: If records contain non-serializable objects
        """
        data = {
            'last_modified': datetime.now().isoformat(),
            'data': [record.to_dict() for record in records]
        }

        with open(str(self.file_path), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self) -> Optional[list[ShipmentRecord]]:
        """
        Load shipment records from JSON file.

        Reads and deserializes shipment records from the JSON file. Returns None if the file
        doesn't exist or cannot be parsed.

        Returns:
            Optional[list[ShipmentRecord]]: List of ShipmentRecord instances if successful,
                None if file doesn't exist or if JSON parsing fails

        Raises:
            No exceptions are raised; errors are silently handled and None is returned
        """
        if not self.file_path.exists():
            return None

        try:
            with open(str(self.file_path), 'r', encoding='utf-8') as f:
                data = json.load(f)

            return [ShipmentRecord.from_dict(item) for item in data['data']]
        except Exception:
            return None


def validate_shipment_input(colli: str, peso: str) -> tuple[Optional[int], Optional[float], Optional[str]]:
    """
    Validate shipment input fields

    Args:
        colli: Number of packages as string
        peso: Weight as string

    Returns:
        Tuple of (colli_int, peso_float, error_message)
        If validation fails, returns (None, None, error_message)
    """
    # Check empty fields
    if not colli or not peso:
        return None, None, "Compilare tutti i campi (colli e peso)"

    # Try to convert values
    try:
        colli_int = int(colli)
        peso_float = float(peso.replace(',', '.'))
    except ValueError:
        return None, None, "Valori non validi per colli o peso"

    # Check positive values
    if colli_int <= 0 or peso_float <= 0:
        return None, None, "Colli e peso devono essere maggiori di zero"

    return colli_int, peso_float, None

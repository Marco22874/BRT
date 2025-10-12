"""
Settings Manager component for BRT Shipping Management Application
Handles loading and saving application settings
"""

import json
from pathlib import Path
from typing import Dict, Any

from core.constants import BRTDefaults
from core.utils import logger


class SettingsManager:
    """Manages application settings persistence"""

    def __init__(self, settings_file: Path):
        """Initialize settings manager

        Args:
            settings_file: Path to settings JSON file
        """
        self.settings_file = settings_file

    def load(self) -> Dict[str, Any]:
        """Load settings from file

        Returns:
            Dict with settings or default values
        """
        # Default values
        settings = {
            'default_colli': 1,
            'default_peso': 2,
            'brt_customer_code': BRTDefaults.DEFAULT_CUSTOMER_CODE,
            'brt_alphabetic_ref': BRTDefaults.DEFAULT_ALPHABETIC_REF,
            'brt_goods_type': BRTDefaults.DEFAULT_GOODS_TYPE,
            'brt_tariff_code': BRTDefaults.DEFAULT_TARIFF_CODE,
            'brt_service_type': BRTDefaults.DEFAULT_SERVICE_TYPE
        }

        if not self.settings_file.exists():
            logger.debug(f"Settings file {self.settings_file} not found, using default values")
            return settings

        try:
            with open(str(self.settings_file), 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)

            # Update defaults with loaded values
            settings.update(loaded_settings)

            logger.info(f"Settings loaded successfully from {self.settings_file}")
            return settings

        except Exception as e:
            logger.error(f"Failed to load settings from {self.settings_file}: {e}", exc_info=True)
            return settings

    def save(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file

        Args:
            settings: Dictionary with settings to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(str(self.settings_file), 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

            logger.info(f"Settings saved successfully to {self.settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings to {self.settings_file}: {e}", exc_info=True)
            return False

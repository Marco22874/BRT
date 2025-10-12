#!/usr/bin/env python3
"""
BRT Shipping Management Application - PyQt5
Converts the LISTADDT.csv file to the format required by BRT
"""

__version__ = "3.6.0"
__app_name__ = "Gestione Spedizioni IGEA <-> BRT"
__release_date__ = "2025-10-12"
__developer__ = "Marco De Luca"

import sys
from PyQt5.QtWidgets import QApplication

# Import main window from UI package
from ui.main_window import BRTSpedizioniApp


def main() -> None:
    """Main function - Entry point for the application"""
    app = QApplication(sys.argv)
    window = BRTSpedizioniApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
BRT Shipping Management Application - PyQt5
Converts the LISTADDT.csv file to the format required by BRT
"""

__version__ = "6.4.1"
__app_name__ = "Gestione Spedizioni IGEA <-> BRT"
__release_date__ = "2025-10-14"
__developer__ = "Marco De Luca"

import sys
from PyQt5.QtWidgets import QApplication

# Import main window from UI package
from ui.main_window import BRTSpedizioniApp


def main() -> None:
    """
    Main function - Entry point for the application.

    Initializes the PyQt5 application, creates and displays the main window,
    and starts the Qt event loop. This function blocks until the application
    is closed by the user.

    The function:
        1. Creates a QApplication instance
        2. Instantiates the BRTSpedizioniApp main window
        3. Shows the window
        4. Enters the Qt event loop and exits with the application's return code
    """
    app = QApplication(sys.argv)
    window = BRTSpedizioniApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

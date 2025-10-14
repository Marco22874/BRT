"""
Dialog components for BRT Shipping Management Application
"""

from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon

from core.constants import UIConstants, Messages, FileSettings


class DownloadDialog(QDialog):
    """Custom dialog for showing download progress"""

    def __init__(self, parent: Optional[QWidget], filename: str) -> None:
        """
        Initialize the download dialog.

        Creates a modal dialog window displaying download progress with a progress bar
        and status message for the specified file.

        Args:
            parent: Parent widget for the dialog, or None for a top-level window
            filename: Name of the file being downloaded, shown in the status message
        """
        super().__init__(parent)
        self.setWindowTitle(Messages.TITLE_DOWNLOAD)
        self.setModal(True)
        self.setMinimumWidth(UIConstants.DIALOG_MIN_WIDTH)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(UIConstants.SPACING_MEDIUM)

        # Message label
        self.message_label = QLabel(Messages.format(Messages.MSG_UPDATE_DOWNLOADING, filename=filename))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Add some spacing at the bottom
        layout.addSpacing(UIConstants.SPACING_SMALL)

        self.setLayout(layout)

    def update_progress(self, progress: int) -> None:
        """
        Update the progress bar value.

        Updates the visual progress indicator to reflect the current download status.

        Args:
            progress: Current progress percentage (0-100)
        """
        self.progress_bar.setValue(progress)


class AboutDialog(QDialog):
    """About dialog showing application information"""

    def __init__(self, parent: Optional[QWidget], app_name: str, version: str,
                 release_date: str, developer: str, resource_path: Path) -> None:
        """
        Initialize the About dialog.

        Creates a dialog displaying application information including logos, version details,
        and developer information. The dialog shows IGEA and BRT logos side by side with
        arrows between them.

        Args:
            parent: Parent widget for the dialog, or None for a top-level window
            app_name: Name of the application to display
            version: Version string of the application
            release_date: Release date string to display
            developer: Developer/company name
            resource_path: Path to resources directory for logos
        """
        super().__init__(parent)
        self.resource_path = resource_path
        self.setWindowTitle("Informazioni")
        self.setMinimumWidth(500)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header with logos and arrows
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        # IGEA logo (left)
        igea_logo = QLabel()
        igea_logo_path = self.resource_path / FileSettings.LOGO_IGEA
        if igea_logo_path.exists():
            pixmap_igea = QPixmap(str(igea_logo_path))
            scaled_igea = pixmap_igea.scaledToHeight(UIConstants.LOGO_HEIGHT_DIALOG, Qt.SmoothTransformation)
            igea_logo.setPixmap(scaled_igea)
        header_layout.addWidget(igea_logo)

        # Arrows in the center
        arrows_label = QLabel("→\n←")
        arrows_label.setFont(QFont("Arial", 32))
        arrows_label.setAlignment(Qt.AlignCenter)
        arrows_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(arrows_label)

        # BRT logo (right)
        brt_logo = QLabel()
        brt_logo_path = self.resource_path / FileSettings.LOGO_BRT
        if brt_logo_path.exists():
            pixmap_brt = QPixmap(str(brt_logo_path))
            scaled_brt = pixmap_brt.scaledToHeight(UIConstants.LOGO_HEIGHT_DIALOG, Qt.SmoothTransformation)
            brt_logo.setPixmap(scaled_brt)
        header_layout.addWidget(brt_logo)

        main_layout.addLayout(header_layout)

        # App information
        info_text = f"""
<div style='text-align: center;'>
<h2>{app_name}</h2>
<p><b>Versione:</b> {version}</p>
<p><b>Data di rilascio:</b> {release_date}</p>
<br>
<p><b>Sviluppato da:</b> {developer}</p>
<p><b>Support:</b> support@nextcode.it</p>
</div>
        """

        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        # Ok button
        ok_button = QPushButton(Messages.BTN_OK)
        ok_button.clicked.connect(self.accept)
        ok_button.setMinimumWidth(100)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Set window icon if available
        if igea_logo_path.exists():
            self.setWindowIcon(QIcon(str(igea_logo_path)))

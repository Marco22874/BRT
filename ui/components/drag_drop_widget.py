"""
Drag & Drop Widget for CSV file loading
Supports both drag & drop and click to browse functionality
"""

from pathlib import Path
from typing import Callable, Optional
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent

from core.utils import logger


class DragDropWidget(QWidget):
    """Widget that accepts drag & drop of CSV files and click to browse"""

    # Signal emitted when a file is selected (either by drop or click)
    file_selected = pyqtSignal(str)

    def __init__(self, click_callback: Callable[[], None], parent: Optional[QWidget] = None):
        """Initialize drag & drop widget.

        Args:
            click_callback: Function to call when widget is clicked
            parent: Parent widget
        """
        super().__init__(parent)
        self.click_callback = click_callback

        # Enable drag & drop
        self.setAcceptDrops(True)

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the widget UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Main label
        self.label = QLabel(
            "Trascina qui il file CSV\n"
            "oppure clicca per selezionare"
        )
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)

        # Styling
        self.label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #555555;
                padding: 20px;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)

        layout.addWidget(self.label)
        self.setLayout(layout)

        # Make cursor change on hover
        self.setCursor(Qt.PointingHandCursor)

    def set_active_style(self) -> None:
        """Set active/hover style"""
        self.label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #333333;
                padding: 20px;
                border: 2px dashed #4CAF50;
                border-radius: 8px;
                background-color: #e8f5e9;
            }
        """)

    def set_normal_style(self) -> None:
        """Set normal style"""
        self.label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #555555;
                padding: 20px;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event.

        Args:
            event: Drag enter event
        """
        # Check if dragged data contains URLs (files)
        if event.mimeData().hasUrls():
            # Check if at least one file is a CSV
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.csv'):
                    event.acceptProposedAction()
                    self.set_active_style()
                    return

        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """Handle drag leave event"""
        self.set_normal_style()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event.

        Args:
            event: Drop event
        """
        # Reset style
        self.set_normal_style()

        # Get dropped files
        urls = event.mimeData().urls()

        # Process first CSV file found
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.csv'):
                logger.info(f"CSV file dropped: {file_path}")
                # Emit signal with file path
                self.file_selected.emit(file_path)
                event.acceptProposedAction()
                return

        event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click event.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            # Call the click callback (opens file dialog)
            self.click_callback()

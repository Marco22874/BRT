"""
UI Builder module for BRT Shipping Management Application
Creates UI components and layouts
"""

from pathlib import Path
from typing import Dict, Any, Callable
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QProgressBar,
                             QGroupBox, QGridLayout, QAction, QSpinBox, QDoubleSpinBox,
                             QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from core.constants import UIConstants, FileSettings, Messages, FilterType
from core.utils import get_monospace_font
from .drag_drop_widget import DragDropWidget


class UIBuilder:
    """Builds UI components for the main application"""

    def __init__(self, app_root: Path):
        """Initialize UI builder.

        Args:
            app_root: Root path of the application
        """
        self.app_root = app_root

    def create_header_logos(self) -> QHBoxLayout:
        """Create the header with IGEA and BRT logos.

        Returns:
            QHBoxLayout: Layout containing logos and arrows
        """
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)

        # IGEA logo (left)
        igea_logo_label = QLabel()
        igea_logo_label.setAlignment(Qt.AlignCenter)
        igea_logo_path = self.app_root / FileSettings.LOGO_IGEA
        igea_pixmap = QPixmap(str(igea_logo_path))
        if not igea_pixmap.isNull():
            igea_logo_label.setPixmap(igea_pixmap.scaledToHeight(UIConstants.LOGO_HEIGHT, Qt.SmoothTransformation))
        header_layout.addWidget(igea_logo_label)

        # Center arrows (HTML to control line-height)
        arrows_label = QLabel('<div style="line-height: 80%;">→<br>←</div>')
        arrows_label.setAlignment(Qt.AlignCenter)
        arrows_font = QFont()
        arrows_font.setPointSize(24)
        arrows_font.setBold(True)
        arrows_label.setFont(arrows_font)
        arrows_label.setStyleSheet("color: #666666; padding: 0px 20px;")
        header_layout.addWidget(arrows_label)

        # BRT logo (right)
        brt_logo_label = QLabel()
        brt_logo_label.setAlignment(Qt.AlignCenter)
        brt_logo_path = self.app_root / FileSettings.LOGO_BRT
        if brt_logo_path.exists():
            brt_pixmap = QPixmap(str(brt_logo_path))
            if not brt_pixmap.isNull():
                brt_logo_label.setPixmap(brt_pixmap.scaledToHeight(UIConstants.LOGO_HEIGHT, Qt.SmoothTransformation))
        header_layout.addWidget(brt_logo_label)

        return header_layout

    def create_step1_file_loading(
        self,
        main_layout: QVBoxLayout,
        load_csv_callback: Callable[[], None]
    ) -> Dict[str, Any]:
        """Create STEP 1: File loading section with drag & drop support.

        Args:
            main_layout: Main layout to add this section to
            load_csv_callback: Callback for load CSV button

        Returns:
            Dict with widget references: {'file_label', 'info_label', 'drag_drop_widget'}
        """
        step1_title = QLabel(Messages.SECTION_STEP1)
        step1_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 5px; margin-bottom: 3px;")
        main_layout.addWidget(step1_title)

        # Create drag & drop widget
        drag_drop_widget = DragDropWidget(load_csv_callback)
        main_layout.addWidget(drag_drop_widget)

        # Info row layout (file info + shipment info on same row)
        info_row_layout = QHBoxLayout()
        info_row_layout.setSpacing(20)
        info_row_layout.setContentsMargins(0, 5, 0, 0)

        # File name label (left column)
        file_label = QLabel(Messages.LABEL_NO_FILE)
        file_label.setStyleSheet("color: #666666;")
        info_row_layout.addWidget(file_label)

        # Success info label (right column)
        info_label = QLabel("")
        info_label.setStyleSheet("color: green; font-weight: bold;")
        info_row_layout.addWidget(info_label)

        info_row_layout.addStretch()  # Push content to the left

        main_layout.addLayout(info_row_layout)

        return {'file_label': file_label, 'info_label': info_label, 'drag_drop_widget': drag_drop_widget}

    def create_recipient_column(self) -> tuple[QVBoxLayout, QTextEdit]:
        """Create the left column with recipient data display.

        Returns:
            Tuple of (layout, dest_text widget)
        """
        left_column = QVBoxLayout()

        dest_title = QLabel(Messages.LABEL_RECIPIENT)
        dest_title.setStyleSheet("font-weight: bold; margin-top: 5px; margin-bottom: 3px;")
        left_column.addWidget(dest_title)

        dest_group = QGroupBox()
        dest_group.setStyleSheet("""
            QGroupBox {
                background-color: #f9f9f9;
                border: 1px solid #cccccc;
                border-radius: 8px;
                margin-top: 0px;
                padding: 10px;
            }
        """)
        dest_layout = QVBoxLayout()

        dest_text = QTextEdit()
        dest_text.setReadOnly(True)
        dest_text.setFixedHeight(200)  # Increased height for better visibility
        dest_text.setStyleSheet("""
            background-color: transparent;
            color: #000000;
            border: none;
            padding: 5px;
        """)
        font = QFont(get_monospace_font(), 10)
        dest_text.setFont(font)
        dest_layout.addWidget(dest_text)

        dest_group.setLayout(dest_layout)

        # Set size policy to allow vertical expansion
        dest_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        left_column.addWidget(dest_group)

        return left_column, dest_text

    def create_shipment_column(
        self,
        default_colli: int,
        default_peso: float,
        peso_focus_callback: Callable[[], None],
        save_and_next_callback: Callable[[], None],
        template_callback: Callable[[int, float], None]
    ) -> tuple[QVBoxLayout, QSpinBox, QDoubleSpinBox]:
        """Create the right column with shipment data inputs.

        Args:
            default_colli: Default number of packages
            default_peso: Default weight
            peso_focus_callback: Callback to set focus to peso input
            save_and_next_callback: Callback for save and next
            template_callback: Callback for template buttons

        Returns:
            Tuple of (layout, colli_input, peso_input)
        """
        right_column = QVBoxLayout()

        sped_title = QLabel(Messages.LABEL_SHIPMENT_DATA)
        sped_title.setStyleSheet("font-weight: bold; margin-top: 5px; margin-bottom: 3px;")
        right_column.addWidget(sped_title)

        sped_group = QGroupBox()
        sped_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 8px;
                margin-top: 0px;
                padding: 10px;
            }
        """)
        sped_layout = QGridLayout()

        # Style for SpinBox and DoubleSpinBox
        # Create nice looking spinboxes with styled buttons and arrows
        spinbox_style = """
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px 2px 4px 6px;
                background-color: white;
                color: #000000;
                min-height: 20px;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #cccccc;
                border-top-right-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f8f8, stop:0.5 #f0f0f0, stop:1 #e8e8e8);
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e8e8, stop:0.5 #e0e0e0, stop:1 #d8d8d8);
            }
            QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
                background: #d0d0d0;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid #cccccc;
                border-bottom-right-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f8f8, stop:0.5 #f0f0f0, stop:1 #e8e8e8);
            }
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e8e8, stop:0.5 #e0e0e0, stop:1 #d8d8d8);
            }
            QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
                background: #d0d0d0;
            }
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                width: 10px;
                height: 6px;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                width: 10px;
                height: 6px;
            }
        """

        # Get path to arrow SVG files in assets folder
        arrow_up_path = str(self.app_root / "assets" / "arrow_up.svg").replace('\\', '/')
        arrow_down_path = str(self.app_root / "assets" / "arrow_down.svg").replace('\\', '/')

        # Add arrow images to the style
        spinbox_style_with_arrows = spinbox_style.replace(
            "QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {",
            f"QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{\n                image: url({arrow_up_path});"
        ).replace(
            "QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {",
            f"QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{\n                image: url({arrow_down_path});"
        )

        # Row 0: Number of packages (SpinBox for integer with arrows)
        sped_layout.addWidget(QLabel(Messages.LABEL_NUM_PACKAGES), 0, 0)
        colli_input = QSpinBox()
        colli_input.setMinimum(1)
        colli_input.setMaximum(999)
        colli_input.setValue(default_colli)
        colli_input.setMaximumWidth(80)  # Reduced width for smaller arrows
        colli_input.setMinimumHeight(28)  # Match height with arrows
        colli_input.setStyleSheet(spinbox_style_with_arrows)
        colli_input.setButtonSymbols(QSpinBox.UpDownArrows)  # Force show arrows
        sped_layout.addWidget(colli_input, 0, 1)

        # Row 1: Weight (DoubleSpinBox for decimal with arrows)
        sped_layout.addWidget(QLabel(Messages.LABEL_TOTAL_WEIGHT), 1, 0)
        peso_input = QDoubleSpinBox()
        peso_input.setMinimum(0.1)
        peso_input.setMaximum(9999.9)
        peso_input.setDecimals(1)
        peso_input.setSingleStep(0.1)  # 100 grams increment (0.1 kg)
        peso_input.setValue(default_peso)
        peso_input.setMaximumWidth(80)  # Reduced width for smaller arrows
        peso_input.setMinimumHeight(28)  # Match height with arrows
        peso_input.setStyleSheet(spinbox_style_with_arrows)
        peso_input.setButtonSymbols(QDoubleSpinBox.UpDownArrows)  # Force show arrows
        sped_layout.addWidget(peso_input, 1, 1)

        # Row 2, Column 0: Quick templates label
        template_label = QLabel(Messages.LABEL_QUICK_TEMPLATES)
        sped_layout.addWidget(template_label, 2, 0, Qt.AlignTop)

        # Style for template buttons (consistent across platforms)
        template_btn_style = """
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """

        # Row 2-5, Columns 1-2: Template buttons directly in main grid (4 rows x 2 columns)
        btn1 = QPushButton(Messages.BTN_TEMPLATE_1)
        btn1.setFixedWidth(120)
        btn1.setStyleSheet(template_btn_style)
        btn1.clicked.connect(lambda: template_callback(1, 1.5))
        sped_layout.addWidget(btn1, 2, 1)

        btn2 = QPushButton(Messages.BTN_TEMPLATE_2)
        btn2.setFixedWidth(120)
        btn2.setStyleSheet(template_btn_style)
        btn2.clicked.connect(lambda: template_callback(1, 2))
        sped_layout.addWidget(btn2, 2, 2)

        btn3 = QPushButton(Messages.BTN_TEMPLATE_3)
        btn3.setFixedWidth(120)
        btn3.setStyleSheet(template_btn_style)
        btn3.clicked.connect(lambda: template_callback(1, 2.5))
        sped_layout.addWidget(btn3, 3, 1)

        btn4 = QPushButton(Messages.BTN_TEMPLATE_4)
        btn4.setFixedWidth(120)
        btn4.setStyleSheet(template_btn_style)
        btn4.clicked.connect(lambda: template_callback(1, 3))
        sped_layout.addWidget(btn4, 3, 2)

        btn5 = QPushButton(Messages.BTN_TEMPLATE_5)
        btn5.setFixedWidth(120)
        btn5.setStyleSheet(template_btn_style)
        btn5.clicked.connect(lambda: template_callback(1, 3.5))
        sped_layout.addWidget(btn5, 4, 1)

        btn6 = QPushButton(Messages.BTN_TEMPLATE_6)
        btn6.setFixedWidth(120)
        btn6.setStyleSheet(template_btn_style)
        btn6.clicked.connect(lambda: template_callback(1, 4))
        sped_layout.addWidget(btn6, 4, 2)

        btn7 = QPushButton(Messages.BTN_TEMPLATE_7)
        btn7.setFixedWidth(120)
        btn7.setStyleSheet(template_btn_style)
        btn7.clicked.connect(lambda: template_callback(1, 4.5))
        sped_layout.addWidget(btn7, 5, 1)

        btn8 = QPushButton(Messages.BTN_TEMPLATE_8)
        btn8.setFixedWidth(120)
        btn8.setStyleSheet(template_btn_style)
        btn8.clicked.connect(lambda: template_callback(1, 5))
        sped_layout.addWidget(btn8, 5, 2)

        # Set column stretch
        sped_layout.setColumnStretch(0, 0)  # Labels column - no stretch
        sped_layout.setColumnStretch(1, 1)  # First button column - can stretch
        sped_layout.setColumnStretch(2, 1)  # Second button column - can stretch

        # Set spacing
        sped_layout.setHorizontalSpacing(20)
        sped_layout.setVerticalSpacing(10)

        sped_group.setLayout(sped_layout)
        sped_group.setMinimumHeight(230)  # Match height with dest_group (200px text + margins)

        # Set size policy to match the left column height
        sped_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        right_column.addWidget(sped_group)

        return right_column, colli_input, peso_input

    def create_navigation_buttons(
        self,
        button_style_getter: Callable[[str], str],
        callbacks: Dict[str, Callable[[], None]]
    ) -> tuple[QHBoxLayout, Dict[str, QPushButton]]:
        """Create navigation buttons layout.

        Args:
            button_style_getter: Function to get button style by type
            callbacks: Dict with callbacks for each button

        Returns:
            Tuple of (layout, dict of button widgets)
        """
        nav_layout = QHBoxLayout()

        prev_btn = QPushButton(Messages.BTN_PREVIOUS)
        prev_btn.clicked.connect(callbacks['previous'])
        prev_btn.setStyleSheet(button_style_getter('plain'))
        nav_layout.addWidget(prev_btn)

        next_btn = QPushButton(Messages.BTN_NEXT)
        next_btn.clicked.connect(callbacks['next'])
        next_btn.setStyleSheet(button_style_getter('plain'))
        nav_layout.addWidget(next_btn)

        skip_btn = QPushButton(Messages.BTN_SKIP)
        skip_btn.clicked.connect(callbacks['skip'])
        skip_btn.setStyleSheet(button_style_getter('danger'))
        nav_layout.addWidget(skip_btn)

        save_next_btn = QPushButton(Messages.BTN_SAVE_AND_NEXT)
        save_next_btn.clicked.connect(callbacks['save_and_next'])
        save_next_btn.setStyleSheet(button_style_getter('success'))
        nav_layout.addWidget(save_next_btn)

        buttons = {
            'prev_btn': prev_btn,
            'next_btn': next_btn,
            'skip_btn': skip_btn,
            'save_next_btn': save_next_btn
        }

        return nav_layout, buttons

    def create_filter_buttons(
        self,
        button_style_getter: Callable[[str], str],
        callbacks: Dict[str, Callable[[FilterType], None]]
    ) -> tuple[QHBoxLayout, Dict[str, QPushButton]]:
        """Create filter buttons layout (TUTTI, COMPLETATI, DA FARE, ESCLUSI).

        Args:
            button_style_getter: Function to get button style by type
            callbacks: Dict with callback for filter change

        Returns:
            Tuple of (layout, dict of button widgets)
        """
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        filter_layout.setContentsMargins(0, 5, 0, 5)

        # Pill badge style for filter buttons
        pill_style_active = """
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """

        pill_style_inactive = """
            QPushButton {
                background-color: transparent;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 20px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #6c757d;
            }
        """

        # Create filter buttons with pill badge style
        all_btn = QPushButton(Messages.BTN_FILTER_ALL)
        all_btn.clicked.connect(lambda: callbacks['filter_change'](FilterType.ALL))
        all_btn.setStyleSheet(pill_style_active)
        all_btn.setCursor(Qt.PointingHandCursor)
        filter_layout.addWidget(all_btn)

        completed_btn = QPushButton(Messages.BTN_FILTER_COMPLETED)
        completed_btn.clicked.connect(lambda: callbacks['filter_change'](FilterType.COMPLETED))
        completed_btn.setStyleSheet(pill_style_inactive)
        completed_btn.setCursor(Qt.PointingHandCursor)
        filter_layout.addWidget(completed_btn)

        todo_btn = QPushButton(Messages.BTN_FILTER_TODO)
        todo_btn.clicked.connect(lambda: callbacks['filter_change'](FilterType.TODO))
        todo_btn.setStyleSheet(pill_style_inactive)
        todo_btn.setCursor(Qt.PointingHandCursor)
        filter_layout.addWidget(todo_btn)

        skipped_btn = QPushButton(Messages.BTN_FILTER_SKIPPED)
        skipped_btn.clicked.connect(lambda: callbacks['filter_change'](FilterType.SKIPPED))
        skipped_btn.setStyleSheet(pill_style_inactive)
        skipped_btn.setCursor(Qt.PointingHandCursor)
        filter_layout.addWidget(skipped_btn)

        # Add stretch to center the buttons
        filter_layout.insertStretch(0, 1)
        filter_layout.addStretch(1)

        buttons = {
            'filter_all_btn': all_btn,
            'filter_completed_btn': completed_btn,
            'filter_todo_btn': todo_btn,
            'filter_skipped_btn': skipped_btn
        }

        return filter_layout, buttons

    def create_step2_data_entry(
        self,
        main_layout: QVBoxLayout,
        button_style_getter: Callable[[str], str],
        default_colli: int,
        default_peso: float,
        callbacks: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """Create STEP 2: Data entry section.

        Args:
            main_layout: Main layout to add this section to
            button_style_getter: Function to get button style
            default_colli: Default number of packages
            default_peso: Default weight
            callbacks: Dict with all callbacks needed

        Returns:
            Dict with widget references
        """
        step2_title = QLabel(Messages.SECTION_STEP2)
        step2_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 5px; margin-bottom: 3px;")
        main_layout.addWidget(step2_title)

        step2_group = QGroupBox()
        step2_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 8px;
                margin-top: 0px;
                padding: 10px;
            }
        """)
        step2_layout = QVBoxLayout()

        # 2-column layout for recipient and shipment data
        columns_layout = QHBoxLayout()
        left_col, dest_text = self.create_recipient_column()
        right_col, colli_input, peso_input = self.create_shipment_column(
            default_colli, default_peso,
            callbacks['peso_focus'], callbacks['save_and_next'], callbacks['template']
        )
        columns_layout.addLayout(left_col)
        columns_layout.addLayout(right_col)
        step2_layout.addLayout(columns_layout)

        # Progress
        progress_label = QLabel(Messages.LABEL_PROGRESS_DEFAULT)
        progress_label.setAlignment(Qt.AlignCenter)
        progress_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        step2_layout.addWidget(progress_label)

        # Filter buttons (between progress label and progress bar)
        filter_layout, filter_buttons = self.create_filter_buttons(
            button_style_getter,
            {
                'filter_change': callbacks.get('filter_change', lambda x: None)
            }
        )
        step2_layout.addLayout(filter_layout)

        # Progress bar with explicit minimum width to match parent
        progress_bar = QProgressBar()
        progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        progress_bar.setTextVisible(True)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                min-width: 100%;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        step2_layout.addWidget(progress_bar)

        # Navigation buttons
        nav_layout, nav_buttons = self.create_navigation_buttons(
            button_style_getter,
            {
                'previous': callbacks['previous'],
                'next': callbacks['next'],
                'skip': callbacks['skip'],
                'save_and_next': callbacks['save_and_next_unified']
            }
        )
        step2_layout.addLayout(nav_layout)

        step2_group.setLayout(step2_layout)
        main_layout.addWidget(step2_group)

        return {
            'dest_text': dest_text,
            'colli_input': colli_input,
            'peso_input': peso_input,
            'progress_label': progress_label,
            'progress_bar': progress_bar,
            **filter_buttons,
            **nav_buttons
        }

    def create_step3_export(
        self,
        main_layout: QVBoxLayout,
        button_style_getter: Callable[[str], str],
        export_callback: Callable[[], None]
    ) -> Dict[str, Any]:
        """Create STEP 3: Export section.

        Args:
            main_layout: Main layout to add this section to
            button_style_getter: Function to get button style
            export_callback: Callback for export button

        Returns:
            Dict with widget references: {'export_btn', 'export_label'}
        """
        step3_title = QLabel(Messages.SECTION_STEP3)
        step3_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px; margin-bottom: 3px;")
        main_layout.addWidget(step3_title)

        step3_group = QGroupBox()
        step3_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 8px;
                margin-top: 0px;
                padding: 10px;
            }
        """)
        step3_layout = QHBoxLayout()
        step3_layout.setContentsMargins(10, 8, 10, 8)

        step3_layout.addStretch()  # Space to center the button

        export_btn = QPushButton(Messages.BTN_EXPORT_CSV)
        export_btn.clicked.connect(export_callback)
        export_btn.setStyleSheet(button_style_getter('info'))
        step3_layout.addWidget(export_btn)

        step3_layout.addStretch()  # Space to center the button

        step3_group.setLayout(step3_layout)
        main_layout.addWidget(step3_group)

        # Separate export label (outside the group box)
        export_label = QLabel("")
        export_label.setStyleSheet("color: green; font-weight: bold;")
        export_label.setWordWrap(True)
        main_layout.addWidget(export_label)

        return {'export_btn': export_btn, 'export_label': export_label}

    def create_main_screen(
        self,
        button_style_getter: Callable[[str], str],
        default_colli: int,
        default_peso: float,
        callbacks: Dict[str, Callable]
    ) -> tuple[QWidget, Dict[str, Any]]:
        """Create the main screen by composing all sections.

        Args:
            button_style_getter: Function to get button style
            default_colli: Default number of packages
            default_peso: Default weight
            callbacks: Dict with all callbacks needed

        Returns:
            Tuple of (main_widget, dict of all widget references)
        """
        # Widget for the main screen
        main_widget = QWidget()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)  # Reduced spacing between main elements
        main_layout.setContentsMargins(10, 15, 10, 10)  # Top margin to distance logos from edge
        main_widget.setLayout(main_layout)

        # Add all sections
        main_layout.addLayout(self.create_header_logos())

        step1_widgets = self.create_step1_file_loading(main_layout, callbacks['load_csv'])

        step2_widgets = self.create_step2_data_entry(
            main_layout, button_style_getter, default_colli, default_peso, callbacks
        )

        step3_widgets = self.create_step3_export(
            main_layout, button_style_getter, callbacks['export_csv']
        )

        # Add stretch at the end to push everything up and reduce empty space at bottom
        main_layout.addStretch()

        # Combine all widget references
        all_widgets = {**step1_widgets, **step2_widgets, **step3_widgets}

        return main_widget, all_widgets

    def create_settings_screen(
        self,
        button_style_getter: Callable[[str], str],
        default_colli: int,
        default_peso: float,
        brt_config: Dict[str, str],
        callbacks: Dict[str, Callable[[], None]]
    ) -> tuple[QWidget, Dict[str, QLineEdit]]:
        """Create the settings screen.

        Args:
            button_style_getter: Function to get button style
            default_colli: Default number of packages
            default_peso: Default weight
            brt_config: BRT configuration fields
            callbacks: Dict with callbacks for buttons

        Returns:
            Tuple of (settings_widget, dict of input widgets)
        """
        settings_widget = QWidget()

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        settings_widget.setLayout(layout)

        # Title
        title = QLabel(Messages.SETTINGS_TITLE)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Description
        description = QLabel(Messages.SETTINGS_DESCRIPTION)
        description.setStyleSheet("font-size: 12px; color: #666666; margin-bottom: 20px;")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        # Style for all input fields in settings
        input_style = """
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px 8px;
                background-color: white;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #16FEBC;
            }
        """

        # Group box for default values
        defaults_group = QGroupBox(Messages.SETTINGS_GROUP_DEFAULTS)
        defaults_group.setStyleSheet("font-size: 14px; font-weight: bold;")
        defaults_layout = QGridLayout()
        defaults_layout.setSpacing(15)

        # Default number of packages
        defaults_layout.addWidget(QLabel(Messages.LABEL_DEFAULT_PACKAGES), 0, 0)
        settings_colli_input = QLineEdit(str(default_colli))
        settings_colli_input.setMaximumWidth(150)
        settings_colli_input.setStyleSheet(input_style)
        defaults_layout.addWidget(settings_colli_input, 0, 1)

        # Default weight
        defaults_layout.addWidget(QLabel(Messages.LABEL_DEFAULT_WEIGHT), 1, 0)
        settings_peso_input = QLineEdit(str(default_peso))
        settings_peso_input.setMaximumWidth(150)
        settings_peso_input.setStyleSheet(input_style)
        defaults_layout.addWidget(settings_peso_input, 1, 1)

        defaults_group.setLayout(defaults_layout)
        layout.addWidget(defaults_group)

        # Group box for BRT fixed fields
        brt_group = QGroupBox(Messages.SETTINGS_GROUP_BRT)
        brt_group.setStyleSheet("font-size: 14px; font-weight: bold;")
        brt_layout = QGridLayout()
        brt_layout.setSpacing(15)

        # Customer code
        brt_layout.addWidget(QLabel(Messages.LABEL_CUSTOMER_CODE), 0, 0)
        settings_customer_code_input = QLineEdit(brt_config['brt_customer_code'])
        settings_customer_code_input.setMaximumWidth(300)
        settings_customer_code_input.setStyleSheet(input_style)
        brt_layout.addWidget(settings_customer_code_input, 0, 1)

        # Alphabetic reference
        brt_layout.addWidget(QLabel(Messages.LABEL_ALPHABETIC_REF), 1, 0)
        settings_alphabetic_ref_input = QLineEdit(brt_config['brt_alphabetic_ref'])
        settings_alphabetic_ref_input.setMaximumWidth(300)
        settings_alphabetic_ref_input.setStyleSheet(input_style)
        brt_layout.addWidget(settings_alphabetic_ref_input, 1, 1)

        # Goods type (max 15 characters)
        brt_layout.addWidget(QLabel(Messages.LABEL_GOODS_TYPE), 2, 0)
        settings_goods_type_input = QLineEdit(brt_config['brt_goods_type'])
        settings_goods_type_input.setMaximumWidth(300)
        settings_goods_type_input.setMaxLength(15)  # BRT limit: 15 characters
        settings_goods_type_input.setStyleSheet(input_style)
        brt_layout.addWidget(settings_goods_type_input, 2, 1)

        # Tariff code
        brt_layout.addWidget(QLabel(Messages.LABEL_TARIFF_CODE), 3, 0)
        settings_tariff_code_input = QLineEdit(brt_config['brt_tariff_code'])
        settings_tariff_code_input.setMaximumWidth(300)
        settings_tariff_code_input.setStyleSheet(input_style)
        brt_layout.addWidget(settings_tariff_code_input, 3, 1)

        # Service type
        brt_layout.addWidget(QLabel(Messages.LABEL_SERVICE_TYPE), 4, 0)
        settings_service_type_input = QLineEdit(brt_config['brt_service_type'])
        settings_service_type_input.setMaximumWidth(300)
        settings_service_type_input.setStyleSheet(input_style)
        brt_layout.addWidget(settings_service_type_input, 4, 1)

        # Note (max 35 characters)
        brt_layout.addWidget(QLabel(Messages.LABEL_NOTE), 5, 0)
        settings_note_input = QLineEdit(brt_config['brt_note'])
        settings_note_input.setMaximumWidth(300)
        settings_note_input.setMaxLength(35)  # BRT limit: 35 characters
        settings_note_input.setStyleSheet(input_style)
        brt_layout.addWidget(settings_note_input, 5, 1)

        brt_group.setLayout(brt_layout)
        layout.addWidget(brt_group)

        # Spacer
        layout.addStretch()

        # Buttons
        buttons_layout = QHBoxLayout()

        # Back button
        back_btn = QPushButton(Messages.BTN_BACK)
        back_btn.clicked.connect(callbacks['back'])
        back_btn.setStyleSheet(button_style_getter('secondary'))
        buttons_layout.addWidget(back_btn)

        buttons_layout.addStretch()

        # Save button
        save_btn = QPushButton(Messages.BTN_SAVE_SETTINGS)
        save_btn.clicked.connect(callbacks['save'])
        save_btn.setStyleSheet(button_style_getter('success'))
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        # Return widget and input references
        inputs = {
            'settings_colli_input': settings_colli_input,
            'settings_peso_input': settings_peso_input,
            'settings_customer_code_input': settings_customer_code_input,
            'settings_alphabetic_ref_input': settings_alphabetic_ref_input,
            'settings_goods_type_input': settings_goods_type_input,
            'settings_tariff_code_input': settings_tariff_code_input,
            'settings_service_type_input': settings_service_type_input,
            'settings_note_input': settings_note_input
        }

        return settings_widget, inputs

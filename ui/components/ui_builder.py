"""
UI Builder module for BRT Shipping Management Application
Creates UI components and layouts
"""

from pathlib import Path
from typing import Dict, Any, Callable
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QProgressBar,
                             QGroupBox, QGridLayout, QAction)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from core.constants import UIConstants, FileSettings, Messages
from core.utils import get_monospace_font


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
    ) -> Dict[str, QLabel]:
        """Create STEP 1: File loading section.

        Args:
            main_layout: Main layout to add this section to
            load_csv_callback: Callback for load CSV button

        Returns:
            Dict with widget references: {'file_label', 'info_label'}
        """
        step1_title = QLabel(Messages.SECTION_STEP1)
        step1_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px; margin-bottom: 8px;")
        main_layout.addWidget(step1_title)

        step1_group = QGroupBox()
        step1_layout = QHBoxLayout()
        step1_layout.setContentsMargins(10, 10, 10, 15)

        file_label = QLabel(Messages.LABEL_NO_FILE)
        step1_layout.addWidget(file_label)

        step1_layout.addStretch()

        load_btn = QPushButton(Messages.BTN_LOAD_CSV)
        load_btn.clicked.connect(load_csv_callback)
        step1_layout.addWidget(load_btn)

        step1_group.setLayout(step1_layout)
        main_layout.addWidget(step1_group)

        # Separate info label (outside the group box)
        info_label = QLabel("")
        info_label.setStyleSheet("color: green; font-weight: bold;")
        main_layout.addWidget(info_label)

        return {'file_label': file_label, 'info_label': info_label}

    def create_recipient_column(self) -> tuple[QVBoxLayout, QTextEdit]:
        """Create the left column with recipient data display.

        Returns:
            Tuple of (layout, dest_text widget)
        """
        left_column = QVBoxLayout()

        dest_title = QLabel(Messages.LABEL_RECIPIENT)
        dest_title.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        left_column.addWidget(dest_title)

        dest_group = QGroupBox()
        dest_layout = QVBoxLayout()

        dest_text = QTextEdit()
        dest_text.setReadOnly(True)
        dest_text.setFixedHeight(150)
        dest_text.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        font = QFont(get_monospace_font(), 10)
        dest_text.setFont(font)
        dest_layout.addWidget(dest_text)

        dest_group.setLayout(dest_layout)
        left_column.addWidget(dest_group)

        return left_column, dest_text

    def create_shipment_column(
        self,
        default_colli: int,
        default_peso: float,
        peso_focus_callback: Callable[[], None],
        save_and_next_callback: Callable[[], None],
        template_callback: Callable[[int, float], None]
    ) -> tuple[QVBoxLayout, QLineEdit, QLineEdit]:
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
        sped_title.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        right_column.addWidget(sped_title)

        sped_group = QGroupBox()
        sped_layout = QGridLayout()

        # Number of packages
        sped_layout.addWidget(QLabel(Messages.LABEL_NUM_PACKAGES), 0, 0)
        colli_input = QLineEdit(str(default_colli))
        colli_input.setMaximumWidth(100)
        colli_input.returnPressed.connect(peso_focus_callback)
        sped_layout.addWidget(colli_input, 0, 1)

        # Weight
        sped_layout.addWidget(QLabel(Messages.LABEL_TOTAL_WEIGHT), 1, 0)
        peso_input = QLineEdit(str(default_peso))
        peso_input.setMaximumWidth(100)
        peso_input.returnPressed.connect(save_and_next_callback)
        sped_layout.addWidget(peso_input, 1, 1)

        # Quick templates
        template_label = QLabel(Messages.LABEL_QUICK_TEMPLATES)
        sped_layout.addWidget(template_label, 2, 0)

        # Grid layout for templates (4 rows x 2 columns)
        template_grid = QGridLayout()
        template_grid.setSpacing(5)

        # Row 1
        btn1 = QPushButton(Messages.BTN_TEMPLATE_1)
        btn1.clicked.connect(lambda: template_callback(1, 1.5))
        template_grid.addWidget(btn1, 0, 0)

        btn2 = QPushButton(Messages.BTN_TEMPLATE_2)
        btn2.clicked.connect(lambda: template_callback(1, 2))
        template_grid.addWidget(btn2, 0, 1)

        # Row 2
        btn3 = QPushButton(Messages.BTN_TEMPLATE_3)
        btn3.clicked.connect(lambda: template_callback(1, 2.5))
        template_grid.addWidget(btn3, 1, 0)

        btn4 = QPushButton(Messages.BTN_TEMPLATE_4)
        btn4.clicked.connect(lambda: template_callback(1, 3))
        template_grid.addWidget(btn4, 1, 1)

        # Row 3
        btn5 = QPushButton(Messages.BTN_TEMPLATE_5)
        btn5.clicked.connect(lambda: template_callback(1, 3.5))
        template_grid.addWidget(btn5, 2, 0)

        btn6 = QPushButton(Messages.BTN_TEMPLATE_6)
        btn6.clicked.connect(lambda: template_callback(1, 4))
        template_grid.addWidget(btn6, 2, 1)

        # Row 4
        btn7 = QPushButton(Messages.BTN_TEMPLATE_7)
        btn7.clicked.connect(lambda: template_callback(1, 4.5))
        template_grid.addWidget(btn7, 3, 0)

        btn8 = QPushButton(Messages.BTN_TEMPLATE_8)
        btn8.clicked.connect(lambda: template_callback(1, 5))
        template_grid.addWidget(btn8, 3, 1)

        sped_layout.addLayout(template_grid, 2, 1)

        sped_group.setLayout(sped_layout)
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

        skip_btn = QPushButton(Messages.BTN_SKIP)
        skip_btn.clicked.connect(callbacks['skip'])
        skip_btn.setStyleSheet(button_style_getter('plain'))
        nav_layout.addWidget(skip_btn)

        goto_skipped_btn = QPushButton(Messages.BTN_GOTO_SKIPPED)
        goto_skipped_btn.clicked.connect(callbacks['goto_skipped'])
        goto_skipped_btn.setStyleSheet(button_style_getter('warning'))
        nav_layout.addWidget(goto_skipped_btn)

        save_next_btn = QPushButton(Messages.BTN_SAVE_AND_NEXT)
        save_next_btn.clicked.connect(callbacks['save_and_next'])
        save_next_btn.setStyleSheet(button_style_getter('primary'))
        nav_layout.addWidget(save_next_btn)

        buttons = {
            'prev_btn': prev_btn,
            'skip_btn': skip_btn,
            'goto_skipped_btn': goto_skipped_btn,
            'save_next_btn': save_next_btn
        }

        return nav_layout, buttons

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
        step2_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 0px; margin-bottom: 8px;")
        main_layout.addWidget(step2_title)

        step2_group = QGroupBox()
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

        progress_bar = QProgressBar()
        step2_layout.addWidget(progress_bar)

        # Summary
        summary_label = QLabel("")
        summary_label.setAlignment(Qt.AlignCenter)
        step2_layout.addWidget(summary_label)

        # Navigation buttons
        nav_layout, nav_buttons = self.create_navigation_buttons(
            button_style_getter,
            {
                'previous': callbacks['previous'],
                'skip': callbacks['skip'],
                'goto_skipped': callbacks['goto_skipped'],
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
            'summary_label': summary_label,
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
        step3_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px; margin-bottom: 8px;")
        main_layout.addWidget(step3_title)

        step3_group = QGroupBox()
        step3_layout = QHBoxLayout()
        step3_layout.setContentsMargins(10, 10, 10, 15)

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
        main_layout.setSpacing(10)  # Reduced spacing between main elements
        main_layout.setContentsMargins(10, 20, 10, 10)  # Top margin to distance logos from edge
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

        # Group box for default values
        defaults_group = QGroupBox(Messages.SETTINGS_GROUP_DEFAULTS)
        defaults_group.setStyleSheet("font-size: 14px; font-weight: bold;")
        defaults_layout = QGridLayout()
        defaults_layout.setSpacing(15)

        # Default number of packages
        defaults_layout.addWidget(QLabel(Messages.LABEL_DEFAULT_PACKAGES), 0, 0)
        settings_colli_input = QLineEdit(str(default_colli))
        settings_colli_input.setMaximumWidth(150)
        defaults_layout.addWidget(settings_colli_input, 0, 1)

        # Default weight
        defaults_layout.addWidget(QLabel(Messages.LABEL_DEFAULT_WEIGHT), 1, 0)
        settings_peso_input = QLineEdit(str(default_peso))
        settings_peso_input.setMaximumWidth(150)
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
        brt_layout.addWidget(settings_customer_code_input, 0, 1)

        # Alphabetic reference
        brt_layout.addWidget(QLabel(Messages.LABEL_ALPHABETIC_REF), 1, 0)
        settings_alphabetic_ref_input = QLineEdit(brt_config['brt_alphabetic_ref'])
        settings_alphabetic_ref_input.setMaximumWidth(300)
        brt_layout.addWidget(settings_alphabetic_ref_input, 1, 1)

        # Goods type
        brt_layout.addWidget(QLabel(Messages.LABEL_GOODS_TYPE), 2, 0)
        settings_goods_type_input = QLineEdit(brt_config['brt_goods_type'])
        settings_goods_type_input.setMaximumWidth(300)
        brt_layout.addWidget(settings_goods_type_input, 2, 1)

        # Tariff code
        brt_layout.addWidget(QLabel(Messages.LABEL_TARIFF_CODE), 3, 0)
        settings_tariff_code_input = QLineEdit(brt_config['brt_tariff_code'])
        settings_tariff_code_input.setMaximumWidth(300)
        brt_layout.addWidget(settings_tariff_code_input, 3, 1)

        # Service type
        brt_layout.addWidget(QLabel(Messages.LABEL_SERVICE_TYPE), 4, 0)
        settings_service_type_input = QLineEdit(brt_config['brt_service_type'])
        settings_service_type_input.setMaximumWidth(300)
        brt_layout.addWidget(settings_service_type_input, 4, 1)

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
            'settings_service_type_input': settings_service_type_input
        }

        return settings_widget, inputs

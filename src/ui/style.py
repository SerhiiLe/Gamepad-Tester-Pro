"""
UI Stylesheet & Dark Theme Palette for PySide6
"""

DARK_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #0F172A;
    color: #F8FAFC;
}

QWidget {
    font-family: 'Segoe UI', 'Ubuntu', 'Roboto', 'DejaVu Sans', sans-serif;
    font-size: 13px;
    color: #F8FAFC;
}

QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #1E293B;
    border-radius: 6px;
    padding: 6px;
}

QTabBar::tab {
    background: #1E293B;
    color: #94A3B8;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #334155;
    border-bottom: none;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #0284C7;
    color: #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background: #334155;
    color: #F8FAFC;
}

QGroupBox {
    border: 1px solid #334155;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: bold;
    color: #38BDF8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 6px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748B;
}

QPushButton#btn_danger {
    background-color: #DC2626;
}
QPushButton#btn_danger:hover {
    background-color: #B91C1C;
}

QPushButton#btn_success {
    background-color: #16A34A;
}
QPushButton#btn_success:hover {
    background-color: #15803D;
}

QComboBox {
    background-color: #1E293B;
    border: 1px solid #475569;
    border-radius: 5px;
    padding: 5px 10px;
    color: #F8FAFC;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    color: #F8FAFC;
    selection-background-color: #0284C7;
}

QTableWidget {
    background-color: #1E293B;
    alternate-background-color: #162032;
    border: 1px solid #334155;
    border-radius: 4px;
    gridline-color: #334155;
    color: #F8FAFC;
}

QHeaderView::section {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 6px;
    border: 1px solid #334155;
    font-weight: 600;
}

QProgressBar {
    background-color: #1E293B;
    border: 1px solid #475569;
    border-radius: 4px;
    text-align: center;
    color: #FFFFFF;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #0284C7;
    border-radius: 3px;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #334155;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #0284C7;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #F8FAFC;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QTextEdit {
    background-color: #0B0F19;
    color: #38BDF8;
    font-family: 'Consolas', 'DejaVu Sans Mono', monospace;
    font-size: 12px;
    border: 1px solid #334155;
    border-radius: 4px;
}
"""


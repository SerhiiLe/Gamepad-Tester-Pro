"""
Analog Trigger Vertical Progress Widget
Displays vertical progress bars for L2/LT and R2/RT to save horizontal space.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGroupBox
from PySide6.QtCore import Qt
from ...analysis.triggers import TriggersAnalyzer
from ...i18n import tr


class TriggerWidget(QWidget):
    """Compact vertical progress bars for analog triggers (LT / RT)."""

    def __init__(self, analyzer: TriggersAnalyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.box = QGroupBox(tr("triggers_box_title"))
        self.box.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; }")
        l_box = QHBoxLayout(self.box)
        l_box.setContentsMargins(6, 8, 6, 8)
        l_box.setSpacing(10)

        # LT / L2 Column
        col_l = QVBoxLayout()
        self.lbl_l_name = QLabel(tr("trigger_lt_name"))
        self.lbl_l_name.setAlignment(Qt.AlignCenter)
        self.lbl_l_name.setStyleSheet("color: #38BDF8; font-size: 11px;")
        col_l.addWidget(self.lbl_l_name)

        self.lbl_l_val = QLabel("0%")
        self.lbl_l_val.setAlignment(Qt.AlignCenter)
        self.lbl_l_val.setStyleSheet("font-size: 11px; font-family: monospace;")
        col_l.addWidget(self.lbl_l_val)

        self.bar_l = QProgressBar()
        self.bar_l.setOrientation(Qt.Vertical)
        self.bar_l.setRange(0, 100)
        self.bar_l.setValue(0)
        self.bar_l.setFixedWidth(28)
        self.bar_l.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #475569;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 #0284C7, stop:1 #38BDF8);
                border-radius: 3px;
            }
        """)
        col_l.addWidget(self.bar_l, alignment=Qt.AlignCenter, stretch=1)
        l_box.addLayout(col_l)

        # RT / R2 Column
        col_r = QVBoxLayout()
        self.lbl_r_name = QLabel(tr("trigger_rt_name"))
        self.lbl_r_name.setAlignment(Qt.AlignCenter)
        self.lbl_r_name.setStyleSheet("color: #38BDF8; font-size: 11px;")
        col_r.addWidget(self.lbl_r_name)

        self.lbl_r_val = QLabel("0%")
        self.lbl_r_val.setAlignment(Qt.AlignCenter)
        self.lbl_r_val.setStyleSheet("font-size: 11px; font-family: monospace;")
        col_r.addWidget(self.lbl_r_val)

        self.bar_r = QProgressBar()
        self.bar_r.setOrientation(Qt.Vertical)
        self.bar_r.setRange(0, 100)
        self.bar_r.setValue(0)
        self.bar_r.setFixedWidth(28)
        self.bar_r.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #475569;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 #0284C7, stop:1 #38BDF8);
                border-radius: 3px;
            }
        """)
        col_r.addWidget(self.bar_r, alignment=Qt.AlignCenter, stretch=1)
        l_box.addLayout(col_r)

        layout.addWidget(self.box)
        self.setFixedWidth(115)

    def retranslate_ui(self):
        """Retranslates all text elements to active language."""
        self.box.setTitle(tr("triggers_box_title"))
        self.lbl_l_name.setText(tr("trigger_lt_name"))
        self.lbl_r_name.setText(tr("trigger_rt_name"))

    def update_values(self):
        """Called periodically by timer to update bars from analyzer state."""
        if hasattr(self.analyzer, 'get_normalized_values'):
            l_pct, r_pct = self.analyzer.get_normalized_values()
        else:
            l_pct, r_pct = 0.0, 0.0
            for code, trig in self.analyzer.triggers.items():
                pct = trig.curr_value * 100.0
                name_low = trig.name.lower()
                if "l2" in name_low or "lt" in name_low or "brake" in name_low or code in (0x02, 0x0A):
                    l_pct = pct
                else:
                    r_pct = pct

        self.bar_l.setValue(int(l_pct))
        self.lbl_l_val.setText(f"{int(l_pct)}%")

        self.bar_r.setValue(int(r_pct))
        self.lbl_r_val.setText(f"{int(r_pct)}%")

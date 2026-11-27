"""
Analog Trigger Vertical Progress Widget
Displays vertical progress bars for L2/LT and R2/RT to save horizontal space.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt
from ...analysis.triggers import TriggersAnalyzer
from ...i18n import tr


_TRIGGER_BAR_STYLE = """
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
"""


class TriggerBarColumn(QWidget):
    """Single vertical trigger column with label and vertically-scalable progress bar."""

    def __init__(self, title_key: str, bar_width: int = 36, parent=None):
        super().__init__(parent)
        self._title_key = title_key

        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        self.lbl_name = QLabel(tr(self._title_key))
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setStyleSheet("color: #38BDF8; font-size: 11px;")
        col.addWidget(self.lbl_name)

        self.bar = QProgressBar()
        self.bar.setOrientation(Qt.Vertical)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFixedWidth(bar_width)
        self.bar.setMinimumHeight(60)
        self.bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.bar.setStyleSheet(_TRIGGER_BAR_STYLE)
        col.addWidget(self.bar, stretch=1, alignment=Qt.AlignHCenter)

    def set_value(self, pct: float):
        """Updates progress bar percentage (0..100)."""
        self.bar.setValue(int(pct))

    def retranslate_ui(self):
        """Retranslates column label."""
        self.lbl_name.setText(tr(self._title_key))


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
        l_box.setContentsMargins(6, 2, 6, 8)
        l_box.setSpacing(10)

        self.col_l = TriggerBarColumn("trigger_lt_name")
        self.col_r = TriggerBarColumn("trigger_rt_name")
        self.bar_l = self.col_l.bar
        self.bar_r = self.col_r.bar

        l_box.addWidget(self.col_l)
        l_box.addWidget(self.col_r)

        layout.addWidget(self.box)
        self.setFixedWidth(115)

    def retranslate_ui(self):
        """Retranslates all text elements to active language."""
        self.box.setTitle(tr("triggers_box_title"))
        self.col_l.retranslate_ui()
        self.col_r.retranslate_ui()

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

        self.col_l.set_value(l_pct)
        self.col_r.set_value(r_pct)

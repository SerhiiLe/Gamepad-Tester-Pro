"""
Stick Anomalies & Metrics Table Widget
Displays side-by-side diagnostic metrics with separate tracking for axes X and Y,
enabling diagnosis of individual potentiometers, Hall sensors, and centering springs.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...analysis.sticks import StickAnalyzer
from ...i18n import tr


class StickAnomaliesWidget(QWidget):
    """Real-time comparative table of anomalous stick metrics with X/Y breakdown and rich tooltips."""

    NUM_ROWS = 9

    def __init__(self, left_analyzer: StickAnalyzer, right_analyzer: StickAnalyzer, parent=None):
        super().__init__(parent)
        self.left_analyzer = left_analyzer
        self.right_analyzer = right_analyzer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.box = QGroupBox(tr("anomalies_box_title"))
        self.box.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; }")
        l_box = QVBoxLayout(self.box)
        l_box.setContentsMargins(6, 6, 6, 6)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self._update_headers()

        # Flexible width adaptation without rigid pixel lock
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setRowCount(self.NUM_ROWS)

        for r_idx in range(self.NUM_ROWS):
            p_name = tr(f"anom_row{r_idx}_name")
            tol = tr(f"anom_row{r_idx}_tol")
            tooltip_text = tr(f"anom_row{r_idx}_tip")

            item_name = QTableWidgetItem(p_name)
            item_name.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item_name.setToolTip(tooltip_text)
            self.table.setItem(r_idx, 0, item_name)

            item_ls = QTableWidgetItem(tr("cell_not_tested"))
            item_ls.setTextAlignment(Qt.AlignCenter)
            item_ls.setForeground(QColor("#64748B"))
            self.table.setItem(r_idx, 1, item_ls)

            item_rs = QTableWidgetItem(tr("cell_not_tested"))
            item_rs.setTextAlignment(Qt.AlignCenter)
            item_rs.setForeground(QColor("#64748B"))
            self.table.setItem(r_idx, 2, item_rs)

            item_tol = QTableWidgetItem(tol)
            item_tol.setTextAlignment(Qt.AlignCenter)
            item_tol.setForeground(QColor("#94A3B8"))
            item_tol.setToolTip(f"{tol}")
            self.table.setItem(r_idx, 3, item_tol)

        l_box.addWidget(self.table)
        layout.addWidget(self.box)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(100)

    def _update_headers(self):
        self.table.setHorizontalHeaderLabels([
            tr("col_param_check"),
            tr("col_ls_left"),
            tr("col_rs_right"),
            tr("col_tolerance")
        ])

    def retranslate_ui(self):
        """Retranslates all text elements to active language."""
        self.box.setTitle(tr("anomalies_box_title"))
        self._update_headers()
        for r_idx in range(self.NUM_ROWS):
            p_name = tr(f"anom_row{r_idx}_name")
            tol = tr(f"anom_row{r_idx}_tol")
            tip = tr(f"anom_row{r_idx}_tip")

            item_name = self.table.item(r_idx, 0)
            if item_name:
                item_name.setText(p_name)
                item_name.setToolTip(tip)

            item_tol = self.table.item(r_idx, 3)
            if item_tol:
                item_tol.setText(tol)
                item_tol.setToolTip(tol)
        self.update_table()

    def update_table(self):
        ls = self.left_analyzer
        rs = self.right_analyzer

        not_tested = tr("cell_not_tested")

        # 0. Center drift X
        if ls.center_tested:
            self._set_cell(0, 1, f"{ls.center_drift_x_pct:.1f}%", is_bad=(ls.center_drift_x_pct > 5.0), is_warn=(ls.center_drift_x_pct > 3.0))
        else:
            self._set_cell(0, 1, not_tested, is_muted=True)

        if rs.center_tested:
            self._set_cell(0, 2, f"{rs.center_drift_x_pct:.1f}%", is_bad=(rs.center_drift_x_pct > 5.0), is_warn=(rs.center_drift_x_pct > 3.0))
        else:
            self._set_cell(0, 2, not_tested, is_muted=True)

        # 1. Center drift Y
        if ls.center_tested:
            self._set_cell(1, 1, f"{ls.center_drift_y_pct:.1f}%", is_bad=(ls.center_drift_y_pct > 5.0), is_warn=(ls.center_drift_y_pct > 3.0))
        else:
            self._set_cell(1, 1, not_tested, is_muted=True)

        if rs.center_tested:
            self._set_cell(1, 2, f"{rs.center_drift_y_pct:.1f}%", is_bad=(rs.center_drift_y_pct > 5.0), is_warn=(rs.center_drift_y_pct > 3.0))
        else:
            self._set_cell(1, 2, not_tested, is_muted=True)

        # 2. Circularity error (Combined 360°)
        if ls.circularity_tested:
            is_bad = (ls.circularity_error_pct > 12.0)
            is_warn = (ls.circularity_error_pct > 8.0)
            self._set_cell(2, 1, f"{ls.circularity_error_pct:.1f}%", is_bad=is_bad, is_warn=is_warn)
        else:
            self._set_cell(2, 1, not_tested, is_muted=True)

        if rs.circularity_tested:
            is_bad = (rs.circularity_error_pct > 12.0)
            is_warn = (rs.circularity_error_pct > 8.0)
            self._set_cell(2, 2, f"{rs.circularity_error_pct:.1f}%", is_bad=is_bad, is_warn=is_warn)
        else:
            self._set_cell(2, 2, not_tested, is_muted=True)

        # 3. Noise X
        if ls.jitter_tested:
            self._set_cell(3, 1, f"{ls.peak_jitter_x_pct:.2f}%", is_bad=(ls.peak_jitter_x_pct > 2.0), is_warn=(ls.peak_jitter_x_pct > 1.2))
        else:
            self._set_cell(3, 1, not_tested, is_muted=True)

        if rs.jitter_tested:
            self._set_cell(3, 2, f"{rs.peak_jitter_x_pct:.2f}%", is_bad=(rs.peak_jitter_x_pct > 2.0), is_warn=(rs.peak_jitter_x_pct > 1.2))
        else:
            self._set_cell(3, 2, not_tested, is_muted=True)

        # 4. Noise Y
        if ls.jitter_tested:
            self._set_cell(4, 1, f"{ls.peak_jitter_y_pct:.2f}%", is_bad=(ls.peak_jitter_y_pct > 2.0), is_warn=(ls.peak_jitter_y_pct > 1.2))
        else:
            self._set_cell(4, 1, not_tested, is_muted=True)

        if rs.jitter_tested:
            self._set_cell(4, 2, f"{rs.peak_jitter_y_pct:.2f}%", is_bad=(rs.peak_jitter_y_pct > 2.0), is_warn=(rs.peak_jitter_y_pct > 1.2))
        else:
            self._set_cell(4, 2, not_tested, is_muted=True)

        # 5. Snapback X
        if ls.snapback_tested:
            self._set_cell(5, 1, f"{ls.peak_snapback_x_pct:.1f}%", is_bad=(ls.peak_snapback_x_pct > 8.0), is_warn=(ls.peak_snapback_x_pct > 5.0))
        else:
            self._set_cell(5, 1, not_tested, is_muted=True)

        if rs.snapback_tested:
            self._set_cell(5, 2, f"{rs.peak_snapback_x_pct:.1f}%", is_bad=(rs.peak_snapback_x_pct > 8.0), is_warn=(rs.peak_snapback_x_pct > 5.0))
        else:
            self._set_cell(5, 2, not_tested, is_muted=True)

        # 6. Snapback Y
        if ls.snapback_tested:
            self._set_cell(6, 1, f"{ls.peak_snapback_y_pct:.1f}%", is_bad=(ls.peak_snapback_y_pct > 8.0), is_warn=(ls.peak_snapback_y_pct > 5.0))
        else:
            self._set_cell(6, 1, not_tested, is_muted=True)

        if rs.snapback_tested:
            self._set_cell(6, 2, f"{rs.peak_snapback_y_pct:.1f}%", is_bad=(rs.peak_snapback_y_pct > 8.0), is_warn=(rs.peak_snapback_y_pct > 5.0))
        else:
            self._set_cell(6, 2, not_tested, is_muted=True)

        # 7. Snapback Rate (%)
        if ls.snapback_tested and ls.total_flicks > 0:
            rate_str = f"{ls.snapback_rate_pct:.0f}% (X:{ls.snapback_rate_x_pct:.0f}% Y:{ls.snapback_rate_y_pct:.0f}%)"
            self._set_cell(7, 1, rate_str, is_bad=(ls.snapback_rate_pct > 20.0), is_warn=(ls.snapback_rate_pct > 0.0))
        else:
            self._set_cell(7, 1, not_tested, is_muted=True)

        if rs.snapback_tested and rs.total_flicks > 0:
            rate_str = f"{rs.snapback_rate_pct:.0f}% (X:{rs.snapback_rate_x_pct:.0f}% Y:{rs.snapback_rate_y_pct:.0f}%)"
            self._set_cell(7, 2, rate_str, is_bad=(rs.snapback_rate_pct > 20.0), is_warn=(rs.snapback_rate_pct > 0.0))
        else:
            self._set_cell(7, 2, not_tested, is_muted=True)

        # 8. Overall Status Verdict
        any_ls = (ls.center_tested or ls.circularity_tested or ls.jitter_tested or ls.snapback_tested)
        any_rs = (rs.center_tested or rs.circularity_tested or rs.jitter_tested or rs.snapback_tested)

        waiting_tests = tr("cell_waiting_tests")
        pass_str = tr("cell_pass")
        defect_str = tr("cell_defect")

        if not any_ls:
            self._set_cell(8, 1, waiting_tests, is_muted=True)
        else:
            ls_bad = (
                (ls.center_tested and (ls.center_drift_x_pct > 5.0 or ls.center_drift_y_pct > 5.0)) or
                (ls.circularity_tested and ls.circularity_error_pct > 12.0) or
                (ls.jitter_tested and (ls.peak_jitter_x_pct > 1.8 or ls.peak_jitter_y_pct > 1.8)) or
                (ls.snapback_tested and len(ls.snapback_events) > 0)
            )
            self._set_cell(8, 1, defect_str if ls_bad else pass_str, is_bad=ls_bad, is_bold=True)

        if not any_rs:
            self._set_cell(8, 2, waiting_tests, is_muted=True)
        else:
            rs_bad = (
                (rs.center_tested and (rs.center_drift_x_pct > 5.0 or rs.center_drift_y_pct > 5.0)) or
                (rs.circularity_tested and rs.circularity_error_pct > 12.0) or
                (rs.jitter_tested and (rs.peak_jitter_x_pct > 1.8 or rs.peak_jitter_y_pct > 1.8)) or
                (rs.snapback_tested and len(rs.snapback_events) > 0)
            )
            self._set_cell(8, 2, defect_str if rs_bad else pass_str, is_bad=rs_bad, is_bold=True)

    def _set_cell(self, row: int, col: int, text: str, is_bad: bool = False, is_warn: bool = False, is_bold: bool = False, is_muted: bool = False):
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem(text)
            self.table.setItem(row, col, item)
        else:
            item.setText(text)

        item.setTextAlignment(Qt.AlignCenter)
        if is_muted:
            item.setForeground(QColor("#64748B"))
        elif is_bad:
            item.setForeground(QColor("#EF4444"))
        elif is_warn:
            item.setForeground(QColor("#F59E0B"))
        else:
            item.setForeground(QColor("#10B981"))

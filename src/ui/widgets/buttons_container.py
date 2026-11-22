"""
Buttons View Container Widget
Combines the detailed Buttons Table and the interactive Gamepad Diagram in sub-tabs.
"""

from typing import Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from .buttons_table import ButtonsTableWidget
from .buttons_diagram_widget import ButtonsDiagramWidget
from ...analysis.buttons import ButtonsAnalyzer
from ...analysis.sticks import StickAnalyzer
from ...analysis.triggers import TriggersAnalyzer
from ...i18n import tr


class ButtonsViewWidget(QWidget):
    """Container hosting both the Buttons Data Table and the Gamepad Diagram."""

    def __init__(
        self,
        buttons_analyzer: ButtonsAnalyzer,
        left_stick_analyzer: StickAnalyzer,
        right_stick_analyzer: StickAnalyzer,
        triggers_analyzer: TriggersAnalyzer,
        profile_getter: Callable[[], str],
        parent=None
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.sub_tabs = QTabWidget()

        # Subtab 0: Table
        self.w_table = ButtonsTableWidget(buttons_analyzer)
        self.sub_tabs.addTab(self.w_table, tr("tab_buttons_table"))

        # Subtab 1: Diagram
        self.w_diagram = ButtonsDiagramWidget(
            buttons_analyzer=buttons_analyzer,
            left_stick_analyzer=left_stick_analyzer,
            right_stick_analyzer=right_stick_analyzer,
            triggers_analyzer=triggers_analyzer,
            profile_getter=profile_getter
        )
        self.sub_tabs.addTab(self.w_diagram, tr("tab_buttons_diagram"))

        # When table clear is clicked, also reset diagram tested states
        self.w_table.btn_clear.clicked.connect(self.w_diagram.reset_tested)

        layout.addWidget(self.sub_tabs)

    def retranslate_ui(self):
        """Retranslates sub-tab titles and child widgets."""
        self.sub_tabs.setTabText(0, tr("tab_buttons_table"))
        self.sub_tabs.setTabText(1, tr("tab_buttons_diagram"))
        self.w_table.retranslate_ui()
        self.w_diagram.retranslate_ui()

    def clear_data(self):
        """Clears both table and diagram data."""
        self.w_table.clear_data()
        self.w_diagram.reset_tested()

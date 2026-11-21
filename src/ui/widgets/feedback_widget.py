"""
Force Feedback & LED Control Widget
Provides sliders for vibration intensity, hardware support detection,
informative compatibility list, and separated controllers for Sony RGB Lightbar
and Microsoft Xbox Ring of Light patterns.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QGroupBox, QTabWidget, QFrame, QTextEdit
)
from PySide6.QtCore import Qt

from ...core.device import GamepadDevice
from ...feedback.rumble import RumbleController
from ...feedback.leds import LedController
from ...i18n import tr


class FeedbackWidget(QWidget):
    """Panel for vibration actuators and separated Sony vs Xbox LED controls."""

    def __init__(self, rumble_ctrl: RumbleController, led_ctrl: LedController, parent=None):
        super().__init__(parent)
        self.rumble_ctrl = rumble_ctrl
        self.led_ctrl = led_ctrl
        self.current_device: Optional[GamepadDevice] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # ======================================================================
        # 1. Rumble GroupBox (Force Feedback / Vibration)
        # ======================================================================
        self.grp_rumble = QGroupBox(tr("rumble_group_title"))
        l_rumble = QVBoxLayout(self.grp_rumble)
        l_rumble.setContentsMargins(10, 14, 10, 10)
        l_rumble.setSpacing(8)

        # Force Feedback Support Status Banner
        self.lbl_ff_status = QLabel()
        self.lbl_ff_status.setWordWrap(True)
        l_rumble.addWidget(self.lbl_ff_status)

        # Left Motor (Heavy / Low Freq)
        row_left = QHBoxLayout()
        self.lbl_l = QLabel(tr("lbl_left_motor"))
        self.lbl_l.setMinimumWidth(210)
        row_left.addWidget(self.lbl_l)
        self.slider_left = QSlider(Qt.Horizontal)
        self.slider_left.setRange(0, 100)
        self.slider_left.setValue(100)
        self.lbl_left = QLabel("100%")
        self.lbl_left.setFixedWidth(45)
        self.slider_left.valueChanged.connect(lambda v: self.lbl_left.setText(f"{v}%"))
        row_left.addWidget(self.slider_left)
        row_left.addWidget(self.lbl_left)
        l_rumble.addLayout(row_left)

        # Right Motor (Light / High Freq)
        row_right = QHBoxLayout()
        self.lbl_r = QLabel(tr("lbl_right_motor"))
        self.lbl_r.setMinimumWidth(210)
        row_right.addWidget(self.lbl_r)
        self.slider_right = QSlider(Qt.Horizontal)
        self.slider_right.setRange(0, 100)
        self.slider_right.setValue(100)
        self.lbl_right = QLabel("100%")
        self.lbl_right.setFixedWidth(45)
        self.slider_right.valueChanged.connect(lambda v: self.lbl_right.setText(f"{v}%"))
        row_right.addWidget(self.slider_right)
        row_right.addWidget(self.lbl_right)
        l_rumble.addLayout(row_right)

        # Pulse Buttons
        btn_box = QHBoxLayout()
        self.btn_pulse_l = QPushButton(tr("btn_pulse_left"))
        self.btn_pulse_l.setMinimumWidth(170)
        self.btn_pulse_l.clicked.connect(self._pulse_left)
        btn_box.addWidget(self.btn_pulse_l)

        self.btn_pulse_r = QPushButton(tr("btn_pulse_right"))
        self.btn_pulse_r.setMinimumWidth(170)
        self.btn_pulse_r.clicked.connect(self._pulse_right)
        btn_box.addWidget(self.btn_pulse_r)

        self.btn_pulse_both = QPushButton(tr("btn_pulse_both"))
        self.btn_pulse_both.setMinimumWidth(170)
        self.btn_pulse_both.clicked.connect(self._pulse_both)
        btn_box.addWidget(self.btn_pulse_both)

        self.btn_stop = QPushButton(tr("btn_stop_rumble"))
        self.btn_stop.setMinimumWidth(100)
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.clicked.connect(self.rumble_ctrl.stop)
        btn_box.addWidget(self.btn_stop)
        l_rumble.addLayout(btn_box)

        layout.addWidget(self.grp_rumble, stretch=0)

        # ======================================================================
        # 2. Separated LED Controls (3 Tabs: Info, Sony, Xbox)
        # ======================================================================
        self.grp_led = QGroupBox(tr("led_group_title"))
        l_led = QVBoxLayout(self.grp_led)
        l_led.setContentsMargins(10, 14, 10, 10)
        l_led.setSpacing(6)

        self.led_tabs = QTabWidget()

        # Tab 0: Information & Hardware Compatibility
        tab_info = QWidget()
        l_info = QVBoxLayout(tab_info)
        l_info.setContentsMargins(4, 4, 4, 4)

        self.txt_info = QTextEdit()
        self.txt_info.setReadOnly(True)
        self.txt_info.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #F8FAFC;
                padding: 10px;
                font-family: 'Segoe UI', 'Ubuntu', 'Roboto', 'DejaVu Sans', sans-serif;
            }
        """)
        self.txt_info.setHtml(tr("led_info_html"))
        l_info.addWidget(self.txt_info)
        self.led_tabs.addTab(tab_info, tr("tab_led_info"))

        # Tab 1: Sony PlayStation
        tab_sony = QWidget()
        l_sony = QVBoxLayout(tab_sony)
        l_sony.setContentsMargins(10, 10, 10, 10)
        l_sony.setSpacing(10)

        self.lbl_sony_desc = QLabel(tr("lbl_sony_desc"))
        self.lbl_sony_desc.setStyleSheet("color: #38BDF8; font-size: 13px;")
        l_sony.addWidget(self.lbl_sony_desc)

        row_presets = QHBoxLayout()
        self.lbl_presets = QLabel(tr("lbl_presets"))
        row_presets.addWidget(self.lbl_presets)
        for name, rgb in LedController.COLOR_PRESETS.items():
            btn = QPushButton(name)
            btn.setMinimumWidth(75)
            btn.clicked.connect(lambda _, c=rgb: self._apply_sony_color(*c))
            row_presets.addWidget(btn)
        l_sony.addLayout(row_presets)

        row_rgb = QHBoxLayout()
        self.preview_box = QFrame()
        self.preview_box.setFixedSize(54, 54)
        self.preview_box.setStyleSheet("background-color: #38BDF8; border: 2px solid #64748B; border-radius: 6px;")
        row_rgb.addWidget(self.preview_box)

        sliders_col = QVBoxLayout()
        r_box = QHBoxLayout()
        r_box.addWidget(QLabel("R:"))
        self.sl_r = QSlider(Qt.Horizontal)
        self.sl_r.setRange(0, 255)
        self.sl_r.setValue(56)
        r_box.addWidget(self.sl_r)
        sliders_col.addLayout(r_box)

        g_box = QHBoxLayout()
        g_box.addWidget(QLabel("G:"))
        self.sl_g = QSlider(Qt.Horizontal)
        self.sl_g.setRange(0, 255)
        self.sl_g.setValue(189)
        g_box.addWidget(self.sl_g)
        sliders_col.addLayout(g_box)

        b_box = QHBoxLayout()
        b_box.addWidget(QLabel("B:"))
        self.sl_b = QSlider(Qt.Horizontal)
        self.sl_b.setRange(0, 255)
        self.sl_b.setValue(248)
        b_box.addWidget(self.sl_b)
        sliders_col.addLayout(b_box)
        row_rgb.addLayout(sliders_col)

        self.btn_apply_rgb = QPushButton(tr("btn_apply_rgb"))
        self.btn_apply_rgb.setMinimumWidth(130)
        self.btn_apply_rgb.clicked.connect(self._on_custom_rgb)
        row_rgb.addWidget(self.btn_apply_rgb)

        l_sony.addLayout(row_rgb)
        l_sony.addStretch(1)
        self.led_tabs.addTab(tab_sony, tr("tab_led_sony"))

        # Tab 2: Microsoft Xbox
        tab_xbox = QWidget()
        l_xbox = QVBoxLayout(tab_xbox)
        l_xbox.setContentsMargins(10, 10, 10, 10)
        l_xbox.setSpacing(10)

        self.lbl_xbox_desc = QLabel(tr("lbl_xbox_desc"))
        self.lbl_xbox_desc.setStyleSheet("color: #10B981; font-size: 13px;")
        l_xbox.addWidget(self.lbl_xbox_desc)

        row_players = QHBoxLayout()
        self.lbl_players = QLabel(tr("lbl_players"))
        row_players.addWidget(self.lbl_players)
        self.player_buttons = []
        player_defs = [("player_1", 2), ("player_2", 3), ("player_3", 4), ("player_4", 5), ("player_off", 0)]
        for p_key, pat_id in player_defs:
            btn = QPushButton(tr(p_key))
            btn.setMinimumWidth(90)
            btn.clicked.connect(lambda _, pid=pat_id: self._send_xbox_pattern(pid))
            row_players.addWidget(btn)
            self.player_buttons.append((btn, p_key))
        l_xbox.addLayout(row_players)

        row_patterns = QHBoxLayout()
        self.lbl_modes = QLabel(tr("lbl_modes"))
        row_patterns.addWidget(self.lbl_modes)
        self.mode_buttons = []
        mode_defs = [("mode_rotate", 10), ("mode_fast_blink", 11), ("mode_slow_blink", 12), ("mode_alternating", 13)]
        for m_key, pat_id in mode_defs:
            btn = QPushButton(tr(m_key))
            btn.setMinimumWidth(110)
            btn.clicked.connect(lambda _, pid=pat_id: self._send_xbox_pattern(pid))
            row_patterns.addWidget(btn)
            self.mode_buttons.append((btn, m_key))
        l_xbox.addLayout(row_patterns)

        self.lbl_xbox_status = QLabel(tr("lbl_xbox_root_notice"))
        self.lbl_xbox_status.setWordWrap(True)
        self.lbl_xbox_status.setStyleSheet(
            "font-size: 11px; color: #F59E0B; background-color: #1E293B; "
            "border: 1px solid #334155; border-radius: 6px; padding: 10px 12px; line-height: 1.4;"
        )
        l_xbox.addWidget(self.lbl_xbox_status)
        l_xbox.addStretch(1)

        self.led_tabs.addTab(tab_xbox, tr("tab_led_xbox"))

        l_led.addWidget(self.led_tabs)
        layout.addWidget(self.grp_led, stretch=1)

        # Initialize rumble state
        self._update_rumble_support()

    def retranslate_ui(self):
        """Retranslates all text elements to active language."""
        self.grp_rumble.setTitle(tr("rumble_group_title"))
        self.lbl_l.setText(tr("lbl_left_motor"))
        self.lbl_r.setText(tr("lbl_right_motor"))
        self.btn_pulse_l.setText(tr("btn_pulse_left"))
        self.btn_pulse_r.setText(tr("btn_pulse_right"))
        self.btn_pulse_both.setText(tr("btn_pulse_both"))
        self.btn_stop.setText(tr("btn_stop_rumble"))
        self._update_rumble_support()

        self.grp_led.setTitle(tr("led_group_title"))
        self.led_tabs.setTabText(0, tr("tab_led_info"))
        self.led_tabs.setTabText(1, tr("tab_led_sony"))
        self.led_tabs.setTabText(2, tr("tab_led_xbox"))
        self.txt_info.setHtml(tr("led_info_html"))

        self.lbl_sony_desc.setText(tr("lbl_sony_desc"))
        self.lbl_presets.setText(tr("lbl_presets"))
        self.btn_apply_rgb.setText(tr("btn_apply_rgb"))

        self.lbl_xbox_desc.setText(tr("lbl_xbox_desc"))
        self.lbl_players.setText(tr("lbl_players"))
        self.lbl_modes.setText(tr("lbl_modes"))
        for btn, p_key in self.player_buttons:
            btn.setText(tr(p_key))
        for btn, m_key in self.mode_buttons:
            btn.setText(tr(m_key))
        self.lbl_xbox_status.setText(tr("lbl_xbox_root_notice"))

    def set_current_device(self, device: Optional[GamepadDevice]):
        """Sets active device and updates hardware support status."""
        self.current_device = device
        self.rumble_ctrl.set_device(device)
        self.led_ctrl.set_device(device)
        self._update_rumble_support()
        if self.isVisible():
            self.auto_select_tab()

    def auto_select_tab(self):
        """Automatically selects appropriate LED subtab based on connected controller."""
        if not self.current_device:
            self.led_tabs.setCurrentIndex(0)
            return

        dev = self.current_device
        # 1. Sony (DualSense or DualShock 4)
        if (dev.is_dualsense or dev.is_ds4 or dev.vendor_id == 0x054C or
                dev.layout_flavor in ("dualsense", "ds4")):
            self.led_tabs.setCurrentIndex(1)
        # 2. Xbox (Xbox 360 with Ring of Light or sysfs LED)
        elif (dev.is_xbox or dev.vendor_id == 0x045E or
              "xbox" in dev.name.lower() or "x-box" in dev.name.lower() or
              bool(dev.sysfs_led_path) or dev.layout_flavor == "xbox"):
            self.led_tabs.setCurrentIndex(2)
        # 3. Any other controller (Generic, Switch Pro, etc.)
        else:
            self.led_tabs.setCurrentIndex(0)

    def _update_rumble_support(self):
        """Checks if current device supports Force Feedback and updates UI."""
        has_ff = bool(self.current_device and getattr(self.current_device, 'has_ff', False))

        self.slider_left.setEnabled(has_ff)
        self.slider_right.setEnabled(has_ff)
        self.btn_pulse_l.setEnabled(has_ff)
        self.btn_pulse_r.setEnabled(has_ff)
        self.btn_pulse_both.setEnabled(has_ff)
        self.btn_stop.setEnabled(has_ff)

        if not self.current_device:
            self.lbl_ff_status.setText(tr("ff_no_device"))
            self.lbl_ff_status.setStyleSheet(
                "background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 8px 12px; color: #94A3B8; font-size: 12px;"
            )
            self.lbl_ff_status.setVisible(True)
        elif not has_ff:
            self.lbl_ff_status.setText(tr("ff_unsupported"))
            self.lbl_ff_status.setStyleSheet(
                "background-color: #2D1515; border: 1px solid #7F1D1D; border-radius: 6px; padding: 8px 12px; color: #FCA5A5; font-size: 12px;"
            )
            self.lbl_ff_status.setVisible(True)
        else:
            self.lbl_ff_status.setText("")
            self.lbl_ff_status.setVisible(False)

    def _send_xbox_pattern(self, pid: int):
        ok, msg = self.led_ctrl.set_xpad_pattern(pid)
        if not ok:
            self.lbl_xbox_status.setText(
                f"❌ <b>Error ({msg}):</b> Root required. Run:<br>"
                "<code>sudo chmod 666 /sys/class/leds/xpad*/brightness</code>"
            )

    def _apply_sony_color(self, r: int, g: int, b: int):
        self.sl_r.setValue(r)
        self.sl_g.setValue(g)
        self.sl_b.setValue(b)
        self.preview_box.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 2px solid #64748B; border-radius: 6px;")
        self.led_ctrl.set_rgb(r, g, b)

    def _on_custom_rgb(self):
        r = self.sl_r.value()
        g = self.sl_g.value()
        b = self.sl_b.value()
        self.preview_box.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 2px solid #64748B; border-radius: 6px;")
        self.led_ctrl.set_rgb(r, g, b)

    def _pulse_left(self):
        self.rumble_ctrl.pulse_left(intensity_pct=self.slider_left.value())

    def _pulse_right(self):
        self.rumble_ctrl.pulse_right(intensity_pct=self.slider_right.value())

    def _pulse_both(self):
        self.rumble_ctrl.pulse_both(
            left_pct=self.slider_left.value(),
            right_pct=self.slider_right.value()
        )

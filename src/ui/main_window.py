"""
Main Application Window for Gamepad Tester
Orchestrates device discovery, high-priority input reader thread, real-time analytics,
and multi-tab graphical visualization.
"""

import sys
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer

from ..core.constants import (
    EV_KEY, EV_ABS, EV_SYN,
    ABS_X, ABS_Y, ABS_RX, ABS_RY, ABS_Z, ABS_RZ, ABS_BRAKE, ABS_GAS,
    ABS_HAT0X, ABS_HAT0Y,
    BTN_DPAD_UP, BTN_DPAD_DOWN, BTN_DPAD_LEFT, BTN_DPAD_RIGHT
)
from ..core.device import GamepadDevice
from ..core.discovery import discover_gamepads
from ..core.reader import InputReader, RawInputEvent
from ..core.profiles import PROFILES, get_button_info, get_axis_info

from ..analysis.polling import PollingAnalyzer
from ..analysis.buttons import ButtonsAnalyzer
from ..analysis.sticks import StickAnalyzer
from ..analysis.triggers import TriggersAnalyzer
from ..feedback.rumble import RumbleController
from ..feedback.leds import LedController

from ..i18n import i18n, tr

from .style import DARK_THEME_QSS
from .widgets.stick_widget import StickWidget
from .widgets.snapback_widget import StickOscilloscopeWidget
from .widgets.stick_anomalies_widget import StickAnomaliesWidget
from .widgets.trigger_widget import TriggerWidget
from .widgets.buttons_table import ButtonsTableWidget
from .widgets.polling_widget import PollingWidget
from .widgets.feedback_widget import FeedbackWidget
from .widgets.report_widget import ReportWidget


class MainWindow(QMainWindow):
    """Main window hosting all diagnostic tabs and controller interfaces."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.resize(1180, 820)
        self.setStyleSheet(DARK_THEME_QSS)

        # Data & Analysis Engine Instances
        self.devices: List[GamepadDevice] = []
        self.current_device: Optional[GamepadDevice] = None
        self.current_profile_key: str = "xbox"
        self.input_reader: Optional[InputReader] = None

        self.polling_analyzer = PollingAnalyzer()
        self.buttons_analyzer = ButtonsAnalyzer()
        self.left_stick_analyzer = StickAnalyzer(name=tr("stick_left_name"))
        self.right_stick_analyzer = StickAnalyzer(name=tr("stick_right_name"))
        self.triggers_analyzer = TriggersAnalyzer()
        self.rumble_controller = RumbleController()
        self.led_controller = LedController()

        # Previous state for Hat Switch (D-Pad)
        self._prev_hat_x: int = 0
        self._prev_hat_y: int = 0

        # Build UI layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Top Control Bar (Language Selector, Device Selection, Profile, Battery, Refresh)
        top_bar = QHBoxLayout()

        # Compact 2-letter language switcher (RU, EN) before controller selector
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["RU", "EN"])
        self.combo_lang.setFixedWidth(55)
        self.combo_lang.setStyleSheet("QComboBox { font-weight: bold; }")
        idx_lang = self.combo_lang.findText(i18n.current_lang)
        if idx_lang >= 0:
            self.combo_lang.setCurrentIndex(idx_lang)
        self.combo_lang.currentTextChanged.connect(self._on_lang_changed)
        top_bar.addWidget(self.combo_lang)

        top_bar.addSpacing(6)
        self.lbl_controller = QLabel(tr("lbl_controller"))
        top_bar.addWidget(self.lbl_controller)

        self.combo_devices = QComboBox()
        self.combo_devices.setMinimumWidth(280)
        self.combo_devices.currentIndexChanged.connect(self._on_device_selected)
        top_bar.addWidget(self.combo_devices)

        self.btn_rescan = QPushButton(tr("btn_rescan"))
        self.btn_rescan.setMinimumWidth(140)
        self.btn_rescan.clicked.connect(self.rescan_devices)
        top_bar.addWidget(self.btn_rescan)

        top_bar.addSpacing(16)
        self.lbl_layout = QLabel(tr("lbl_layout"))
        top_bar.addWidget(self.lbl_layout)

        self.combo_profiles = QComboBox()
        self.combo_profiles.setMinimumWidth(180)
        for pkey, pval in PROFILES.items():
            self.combo_profiles.addItem(pval["name"], pkey)
        self.combo_profiles.currentIndexChanged.connect(self._on_profile_changed)
        top_bar.addWidget(self.combo_profiles)

        top_bar.addStretch(1)
        self.lbl_battery = QLabel(tr("lbl_battery_unknown"))
        self.lbl_battery.setStyleSheet("color: #34D399; font-weight: bold;")
        top_bar.addWidget(self.lbl_battery)

        main_layout.addLayout(top_bar)

        # Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ======================================================================
        # Tab 1: Redesigned Sticks & Triggers
        # ======================================================================
        tab_sticks = QWidget()
        l_sticks = QVBoxLayout(tab_sticks)
        l_sticks.setContentsMargins(6, 6, 6, 6)
        l_sticks.setSpacing(6)

        # Top Row: [Left Stick 2D] [Vertical Triggers] [Right Stick 2D] [Anomalies Table]
        top_row = QHBoxLayout()

        self.w_stick_left = StickWidget(self.left_stick_analyzer, title="Левый стик (LS)", title_key="stick_left_name")
        top_row.addWidget(self.w_stick_left, stretch=3)

        self.w_triggers = TriggerWidget(self.triggers_analyzer)
        top_row.addWidget(self.w_triggers, stretch=0)

        self.w_stick_right = StickWidget(self.right_stick_analyzer, title="Правый стик (RS)", title_key="stick_right_name")
        top_row.addWidget(self.w_stick_right, stretch=3)

        # Synchronize stage mode selection between Left and Right sticks
        self.w_stick_left.stage_changed.connect(self.w_stick_right.set_stage)
        self.w_stick_right.stage_changed.connect(self.w_stick_left.set_stage)

        self.w_anomalies = StickAnomaliesWidget(self.left_stick_analyzer, self.right_stick_analyzer)
        top_row.addWidget(self.w_anomalies, stretch=4)

        l_sticks.addLayout(top_row, stretch=5)

        # Bottom Row: Two separate oscilloscopes in ms (Left Stick and Right Stick)
        bot_row = QHBoxLayout()
        self.w_snapback_left = StickOscilloscopeWidget(self.left_stick_analyzer, title="Левый стик (LS)", title_key="stick_left_name")
        bot_row.addWidget(self.w_snapback_left, stretch=1)

        self.w_snapback_right = StickOscilloscopeWidget(self.right_stick_analyzer, title="Правый стик (RS)", title_key="stick_right_name")
        bot_row.addWidget(self.w_snapback_right, stretch=1)

        l_sticks.addLayout(bot_row, stretch=4)

        self.tabs.addTab(tab_sticks, tr("tab_sticks"))

        # Tab 2: Buttons & Chatter
        self.w_buttons = ButtonsTableWidget(self.buttons_analyzer)
        self.tabs.addTab(self.w_buttons, tr("tab_buttons"))

        # Tab 3: Polling Rate
        self.w_polling = PollingWidget(self.polling_analyzer)
        self.tabs.addTab(self.w_polling, tr("tab_polling"))

        # Tab 4: Feedback & LEDs
        self.w_feedback = FeedbackWidget(self.rumble_controller, self.led_controller)
        self.tabs.addTab(self.w_feedback, tr("tab_feedback"))

        # Tab 5: Diagnostic Report & PDF Export
        self.w_report = ReportWidget(self)
        self.tabs.addTab(self.w_report, tr("tab_report"))

        # Tab navigation listener
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Polling Timer for triggers and battery update (30 FPS)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_gui_tick)
        self.update_timer.start(33)

        # Initial device discovery
        self.rescan_devices()

    def _on_lang_changed(self, lang: str):
        """Called when user switches the 2-letter language selector."""
        i18n.set_language(lang)
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslates all main window elements and child widgets."""
        self.setWindowTitle(tr("app_title"))
        self.lbl_controller.setText(tr("lbl_controller"))
        self.btn_rescan.setText(tr("btn_rescan"))
        self.lbl_layout.setText(tr("lbl_layout"))

        self.tabs.setTabText(0, tr("tab_sticks"))
        self.tabs.setTabText(1, tr("tab_buttons"))
        self.tabs.setTabText(2, tr("tab_polling"))
        self.tabs.setTabText(3, tr("tab_feedback"))
        self.tabs.setTabText(4, tr("tab_report"))

        if not self.devices and self.combo_devices.count() > 0:
            self.combo_devices.setItemText(0, tr("no_controllers_found"))

        self._update_battery_label()

        # Retranslate child widgets
        self.w_stick_left.retranslate_ui()
        self.w_triggers.retranslate_ui()
        self.w_stick_right.retranslate_ui()
        self.w_anomalies.retranslate_ui()
        self.w_snapback_left.retranslate_ui()
        self.w_snapback_right.retranslate_ui()
        self.w_buttons.retranslate_ui()
        self.w_polling.retranslate_ui()
        self.w_feedback.retranslate_ui()
        self.w_report.retranslate_ui()

    def _on_tab_changed(self, index: int):
        """Called when user switches tabs in main window."""
        if self.tabs.widget(index) == self.w_feedback:
            self.w_feedback.auto_select_tab()

    def rescan_devices(self):
        """Discovers connected controllers and updates device combo."""
        if self.input_reader:
            self.input_reader.stop()
            self.input_reader = None

        for d in self.devices:
            d.close()

        self.devices = discover_gamepads()
        self.combo_devices.clear()

        if not self.devices:
            self.combo_devices.addItem(tr("no_controllers_found"))
            self.current_device = None
            self.rumble_controller.set_device(None)
            self.led_controller.set_device(None)
            self.w_feedback.set_current_device(None)
            return

        for idx, dev in enumerate(self.devices):
            tag = f"[{dev.layout_flavor.upper()}] " if dev.layout_flavor else ""
            self.combo_devices.addItem(f"{tag}{dev.name} ({dev.event_path or dev.hidraw_path})", idx)

        self.combo_devices.setCurrentIndex(0)

    def _on_device_selected(self, index: int):
        if index < 0 or index >= len(self.devices):
            return

        dev = self.devices[index]
        self.current_device = dev
        self.rumble_controller.set_device(dev)
        self.led_controller.set_device(dev)
        self.w_feedback.set_current_device(dev)

        idx = self.combo_profiles.findData(dev.layout_flavor)
        if idx >= 0:
            self.combo_profiles.setCurrentIndex(idx)
        self.current_profile_key = dev.layout_flavor

        # Reset states and analyzers
        self._prev_hat_x = 0
        self._prev_hat_y = 0
        self.polling_analyzer.is_wireless = getattr(dev, 'is_wireless', False)
        self.polling_analyzer.reset()
        self.buttons_analyzer.reset()
        self.left_stick_analyzer.reset()
        self.right_stick_analyzer.reset()
        self.triggers_analyzer.reset()

        self.w_snapback_left.clear_plot()
        self.w_snapback_right.clear_plot()

        # Configure physical axis ranges for Left and Right sticks
        has_rx = dev.has_axis(ABS_RX)
        rs_x_code = ABS_RX if has_rx else ABS_Z
        rs_y_code = ABS_RY if has_rx else ABS_RZ

        min_lx, max_lx = dev.get_axis_range(ABS_X, default=(-32768, 32767))
        min_ly, max_ly = dev.get_axis_range(ABS_Y, default=(-32768, 32767))
        self.left_stick_analyzer.set_raw_ranges(min_lx, max_lx, min_ly, max_ly)

        min_rx, max_rx = dev.get_axis_range(rs_x_code, default=(-32768, 32767))
        min_ry, max_ry = dev.get_axis_range(rs_y_code, default=(-32768, 32767))
        self.right_stick_analyzer.set_raw_ranges(min_rx, max_rx, min_ry, max_ry)

        if self.input_reader:
            self.input_reader.stop()
            self.input_reader = None

        if dev.event_path:
            self.input_reader = InputReader(dev.event_path, event_callback=self._on_input_event)
            self.input_reader.start()

    def _on_profile_changed(self, index: int):
        self.current_profile_key = self.combo_profiles.currentData()

    def _on_input_event(self, event: RawInputEvent):
        """Callback invoked from high-priority background reader thread."""
        # 1. Measure polling rate strictly on EV_SYN
        if event.ev_type == EV_SYN:
            self.polling_analyzer.record_packet(event.timestamp)
            return

        # 2. Key events (Buttons)
        if event.ev_type == EV_KEY:
            is_pressed = (event.value == 1)
            btn_name, btn_desc = get_button_info(self.current_profile_key, event.code)
            self.buttons_analyzer.process_button_event(
                code=event.code,
                is_pressed=is_pressed,
                timestamp=event.timestamp,
                name=btn_name,
                desc=btn_desc
            )

            # Bridge digital triggers to trigger gauge bars (e.g. Switch ZL/ZR or GP2040)
            btn_low = btn_name.lower()
            if "zl" in btn_low or "lt (digital)" in btn_low or "l2 (digital)" in btn_low or "4k" in btn_low:
                self.triggers_analyzer.update_digital_trigger(is_left=True, is_pressed=is_pressed)
            elif "zr" in btn_low or "rt (digital)" in btn_low or "r2 (digital)" in btn_low or "3k" in btn_low:
                self.triggers_analyzer.update_digital_trigger(is_left=False, is_pressed=is_pressed)

        # 3. Absolute axis events (Sticks, Triggers, D-Pad Hat)
        elif event.ev_type == EV_ABS:
            code = event.code
            val = event.value

            # D-Pad Hat Switch (ABS_HAT0X, ABS_HAT0Y)
            if code == ABS_HAT0X:
                if val != self._prev_hat_x:
                    if self._prev_hat_x == -1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_LEFT, False, event.timestamp, "D-Pad Left", "Left")
                    elif self._prev_hat_x == 1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_RIGHT, False, event.timestamp, "D-Pad Right", "Right")
                    if val == -1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_LEFT, True, event.timestamp, "D-Pad Left", "Left")
                    elif val == 1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_RIGHT, True, event.timestamp, "D-Pad Right", "Right")
                    self._prev_hat_x = val
                return

            elif code == ABS_HAT0Y:
                if val != self._prev_hat_y:
                    if self._prev_hat_y == -1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_UP, False, event.timestamp, "D-Pad Up", "Up")
                    elif self._prev_hat_y == 1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_DOWN, False, event.timestamp, "D-Pad Down", "Down")
                    if val == -1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_UP, True, event.timestamp, "D-Pad Up", "Up")
                    elif val == 1:
                        self.buttons_analyzer.process_button_event(BTN_DPAD_DOWN, True, event.timestamp, "D-Pad Down", "Down")
                    self._prev_hat_y = val
                return

            # Left Stick (X, Y)
            if code == ABS_X:
                self.left_stick_analyzer.update_axis(code, val, event.timestamp, is_x=True)
                return
            elif code == ABS_Y:
                self.left_stick_analyzer.update_axis(code, val, event.timestamp, is_x=False)
                return

            # Right Stick (RX, RY or Z, RZ if mapped to Right Stick)
            has_rx = self.current_device and self.current_device.has_axis(ABS_RX)
            is_rs_x = (code == ABS_RX) or (not has_rx and code == ABS_Z and self.current_profile_key in ("switch", "switch_pro", "dinput_pc", "gp2040"))
            is_rs_y = (code == ABS_RY) or (not has_rx and code == ABS_RZ and self.current_profile_key in ("switch", "switch_pro", "dinput_pc", "gp2040"))

            if is_rs_x:
                self.right_stick_analyzer.update_axis(code, val, event.timestamp, is_x=True)
            elif is_rs_y:
                self.right_stick_analyzer.update_axis(code, val, event.timestamp, is_x=False)

            # Analog Triggers (only if not used for Right Stick!)
            elif code in (ABS_BRAKE, ABS_GAS) or (code in (ABS_Z, ABS_RZ) and not (is_rs_x or is_rs_y)):
                trig_name = get_axis_info(self.current_profile_key, code)
                self.triggers_analyzer.update_trigger(code, val, name=trig_name)

    def _on_gui_tick(self):
        """Periodic tick on Qt main thread for widgets that update smoothly."""
        self.w_triggers.update_values()
        self._update_battery_label()

    def _update_battery_label(self):
        if self.current_device:
            cap, stat = self.current_device.get_battery_info()
            if cap is not None:
                if stat == "Charging":
                    self.lbl_battery.setText(tr("lbl_battery_charging", cap=cap))
                elif stat == "Full":
                    self.lbl_battery.setText(tr("lbl_battery_full", cap=cap))
                elif stat == "Discharging":
                    self.lbl_battery.setText(tr("lbl_battery_discharging", cap=cap))
                else:
                    self.lbl_battery.setText(tr("lbl_battery_unknown", cap=cap))
            else:
                self.lbl_battery.setText(tr("lbl_power_usb"))
        else:
            self.lbl_battery.setText(tr("lbl_power_usb"))

    def closeEvent(self, event):
        """Clean shutdown of threads and actuators."""
        if self.input_reader:
            self.input_reader.stop()
        for d in self.devices:
            d.close()
        event.accept()

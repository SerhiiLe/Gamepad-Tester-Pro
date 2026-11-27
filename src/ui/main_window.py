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
    ABS_MT_SLOT, ABS_MT_POSITION_X, ABS_MT_POSITION_Y, ABS_MT_TRACKING_ID,
    BTN_DPAD_UP, BTN_DPAD_DOWN, BTN_DPAD_LEFT, BTN_DPAD_RIGHT,
    BTN_LEFT, BTN_TOUCH
)
from ..core.device import GamepadDevice
from ..core.discovery import discover_gamepads
from ..core.reader import InputReader, RawInputEvent
from ..core.profiles import PROFILES, get_button_info, get_axis_info

from ..analysis.polling import PollingAnalyzer
from ..analysis.buttons import ButtonsAnalyzer
from ..analysis.sticks import StickAnalyzer
from ..analysis.triggers import TriggersAnalyzer
from ..analysis.touchpad import TouchpadAnalyzer
from ..analysis.motion import MotionAnalyzer
from ..feedback.rumble import RumbleController
from ..feedback.leds import LedController

from ..i18n import i18n, tr

from .style import DARK_THEME_QSS
from .widgets.stick_widget import StickWidget
from .widgets.snapback_widget import StickOscilloscopeWidget
from .widgets.stick_anomalies_widget import StickAnomaliesWidget
from .widgets.trigger_widget import TriggerWidget
from .widgets.buttons_container import ButtonsViewWidget
from .widgets.polling_widget import PollingWidget
from .widgets.feedback_widget import FeedbackWidget
from .widgets.touchpad_motion_widget import TouchpadMotionWidget
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
        self.current_profile_key: str = "standard"
        self.input_reader: Optional[InputReader] = None
        self.touchpad_reader: Optional[InputReader] = None
        self.motion_reader: Optional[InputReader] = None

        self.polling_analyzer = PollingAnalyzer()
        self.buttons_analyzer = ButtonsAnalyzer()
        self.left_stick_analyzer = StickAnalyzer(name=tr("stick_left_name"))
        self.right_stick_analyzer = StickAnalyzer(name=tr("stick_right_name"))
        self.triggers_analyzer = TriggersAnalyzer()
        self.touchpad_analyzer = TouchpadAnalyzer()
        self.motion_analyzer = MotionAnalyzer()
        self.rumble_controller = RumbleController()
        self.led_controller = LedController()

        # Previous state for Hat Switch (D-Pad)
        self._prev_hat_x: int = 0
        self._prev_hat_y: int = 0

        # Axis mapping codes
        self._ls_x_axis: int = ABS_X
        self._ls_y_axis: int = ABS_Y
        self._rs_x_axis: int = ABS_RX
        self._rs_y_axis: int = ABS_RY
        self._trig_l_axis: int = ABS_Z
        self._trig_r_axis: int = ABS_RZ
        self._update_axis_mappings()

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

        self.w_triggers = TriggerWidget(self.triggers_analyzer)
        bot_row.addWidget(self.w_triggers, stretch=0)

        l_sticks.addLayout(bot_row, stretch=4)

        self.tabs.addTab(tab_sticks, tr("tab_sticks"))

        # Tab 2: Buttons & Chatter (Table + Diagram Sub-tabs)
        self.w_buttons = ButtonsViewWidget(
            buttons_analyzer=self.buttons_analyzer,
            left_stick_analyzer=self.left_stick_analyzer,
            right_stick_analyzer=self.right_stick_analyzer,
            triggers_analyzer=self.triggers_analyzer,
            profile_getter=lambda: self.current_profile_key
        )
        self.tabs.addTab(self.w_buttons, tr("tab_buttons"))

        # Tab 3: Polling Rate
        self.w_polling = PollingWidget(self.polling_analyzer)
        self.tabs.addTab(self.w_polling, tr("tab_polling"))

        # Tab 4: Feedback & LEDs
        self.w_feedback = FeedbackWidget(self.rumble_controller, self.led_controller)
        self.tabs.addTab(self.w_feedback, tr("tab_feedback"))

        # Tab 5: Touchpad & Gyroscope / IMU
        self.w_touchpad_motion = TouchpadMotionWidget(self.touchpad_analyzer, self.motion_analyzer)
        self.tabs.addTab(self.w_touchpad_motion, tr("tab_touchpad_gyro"))

        # Tab 6: Diagnostic Report & PDF Export
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
        self.tabs.setTabText(4, tr("tab_touchpad_gyro"))
        self.tabs.setTabText(5, tr("tab_report"))

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
        self.w_touchpad_motion.retranslate_ui()
        self.w_report.retranslate_ui()

    def _on_tab_changed(self, index: int):
        """Called when user switches tabs in main window."""
        if self.tabs.widget(index) == self.w_feedback:
            self.w_feedback.auto_select_tab()

    def _stop_readers(self):
        """Stops all active background input reader threads."""
        for attr in ("input_reader", "touchpad_reader", "motion_reader"):
            reader = getattr(self, attr, None)
            if reader:
                reader.stop()
                setattr(self, attr, None)

    def rescan_devices(self):
        """Discovers connected controllers and updates device combo."""
        self._stop_readers()

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
            self.w_touchpad_motion.set_current_device(None)
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
        self.w_touchpad_motion.set_current_device(dev)

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
        self.touchpad_analyzer.reset()
        self.motion_analyzer.reset()

        self.w_snapback_left.clear_plot()
        self.w_snapback_right.clear_plot()

        # Configure physical axis ranges and mappings for Left and Right sticks and triggers
        self._update_axis_mappings()

        # Configure touchpad and motion sensor bounds
        tp_info = getattr(dev, 'touchpad_abs_info', {})
        if ABS_MT_POSITION_X in tp_info and ABS_MT_POSITION_Y in tp_info:
            min_x, max_x, _ = tp_info[ABS_MT_POSITION_X]
            min_y, max_y, _ = tp_info[ABS_MT_POSITION_Y]
            self.touchpad_analyzer.set_raw_ranges(min_x, max_x, min_y, max_y)
        elif ABS_X in tp_info and ABS_Y in tp_info:
            min_x, max_x, _ = tp_info[ABS_X]
            min_y, max_y, _ = tp_info[ABS_Y]
            self.touchpad_analyzer.set_raw_ranges(min_x, max_x, min_y, max_y)

        motion_info = getattr(dev, 'motion_abs_info', {})
        if motion_info:
            self.motion_analyzer.configure_axes(motion_info)

        self._stop_readers()

        if dev.event_path:
            self.input_reader = InputReader(dev.event_path, event_callback=self._on_input_event)
            self.input_reader.start()

        tp_path = getattr(dev, 'touchpad_event_path', None)
        if tp_path and tp_path != dev.event_path:
            self.touchpad_reader = InputReader(tp_path, event_callback=self._on_touchpad_event)
            self.touchpad_reader.start()

        motion_path = getattr(dev, 'motion_event_path', None)
        if motion_path and motion_path not in (dev.event_path, tp_path):
            self.motion_reader = InputReader(motion_path, event_callback=self._on_motion_event)
            self.motion_reader.start()

    def _update_axis_mappings(self):
        """Resolves axis codes for Left/Right sticks and Triggers from active profile and device."""
        profile = PROFILES.get(self.current_profile_key, PROFILES.get("standard", {}))
        axes_cfg = profile.get("axes", {})

        self._ls_x_axis = ABS_X
        self._ls_y_axis = ABS_Y
        self._rs_x_axis = ABS_RX
        self._rs_y_axis = ABS_RY
        self._trig_l_axis = ABS_Z
        self._trig_r_axis = ABS_RZ

        for code, name in axes_cfg.items():
            name_low = name.lower()
            if "left stick x" in name_low or (name_low.startswith("stick x")):
                self._ls_x_axis = code
            elif "left stick y" in name_low or (name_low.startswith("stick y")):
                self._ls_y_axis = code
            elif "right stick x" in name_low or "x rotation" in name_low:
                self._rs_x_axis = code
            elif "right stick y" in name_low or "y rotation" in name_low or "z rotation" in name_low:
                self._rs_y_axis = code
            elif "l2 trigger" in name_low or "lt trigger" in name_low or "left trigger" in name_low or "brake" in name_low or "throttle" in name_low:
                self._trig_l_axis = code
            elif "r2 trigger" in name_low or "rt trigger" in name_low or "right trigger" in name_low or "gas" in name_low:
                self._trig_r_axis = code

        # Hardware fallback & dynamic topology resolution
        if self.current_device:
            # 1. Left Stick validation
            if not self.current_device.has_axis(self._ls_x_axis):
                if self.current_device.has_axis(ABS_X):
                    self._ls_x_axis = ABS_X
            if not self.current_device.has_axis(self._ls_y_axis):
                if self.current_device.has_axis(ABS_Y):
                    self._ls_y_axis = ABS_Y

            # 2. Right Stick validation & topology detection
            has_z = self.current_device.has_axis(ABS_Z)
            has_rx = self.current_device.has_axis(ABS_RX)
            has_ry = self.current_device.has_axis(ABS_RY)
            has_rz = self.current_device.has_axis(ABS_RZ)

            if has_z and has_rx and not has_ry and not has_rz:
                # 4-axis sequential desktop HID descriptor (e.g. Hori Pokken, generic USB gamepad, Switch HID):
                # ABS_Z is Right Stick X, ABS_RX is Right Stick Y
                self._rs_x_axis = ABS_Z
                self._rs_y_axis = ABS_RX
            else:
                # Validate RS X
                if not self.current_device.has_axis(self._rs_x_axis):
                    if has_rx:
                        self._rs_x_axis = ABS_RX
                    elif has_z:
                        self._rs_x_axis = ABS_Z

                # Validate RS Y
                if not self.current_device.has_axis(self._rs_y_axis) or self._rs_y_axis == self._rs_x_axis:
                    if self._rs_x_axis == ABS_Z:
                        for cand in (ABS_RZ, ABS_RX, ABS_RY):
                            if self.current_device.has_axis(cand):
                                self._rs_y_axis = cand
                                break
                    else:
                        for cand in (ABS_RY, ABS_RZ, ABS_Z):
                            if self.current_device.has_axis(cand):
                                self._rs_y_axis = cand
                                break

            # 3. Triggers validation & collision prevention with Right Stick
            rs_axes = {self._rs_x_axis, self._rs_y_axis}
            if (self._trig_l_axis in rs_axes or
                self._trig_r_axis in rs_axes or
                not self.current_device.has_axis(self._trig_l_axis)):
                if self.current_device.has_axis(ABS_BRAKE) and self.current_device.has_axis(ABS_GAS):
                    self._trig_l_axis = ABS_BRAKE
                    self._trig_r_axis = ABS_GAS
                elif has_z and has_rz and ABS_Z not in rs_axes and ABS_RZ not in rs_axes:
                    self._trig_l_axis = ABS_Z
                    self._trig_r_axis = ABS_RZ
                elif has_rx and has_ry and ABS_RX not in rs_axes and ABS_RY not in rs_axes:
                    self._trig_l_axis = ABS_RX
                    self._trig_r_axis = ABS_RY
                else:
                    # Device has no independent analog trigger axes (e.g. digital ZL/ZR only).
                    # Use non-colliding virtual IDs so digital trigger bridge doesn't conflict with sticks.
                    self._trig_l_axis = 0x20
                    self._trig_r_axis = 0x21

            min_lx, max_lx = self.current_device.get_axis_range(self._ls_x_axis, default=(-32768, 32767))
            min_ly, max_ly = self.current_device.get_axis_range(self._ls_y_axis, default=(-32768, 32767))
            self.left_stick_analyzer.set_raw_ranges(min_lx, max_lx, min_ly, max_ly)

            min_rx, max_rx = self.current_device.get_axis_range(self._rs_x_axis, default=(-32768, 32767))
            min_ry, max_ry = self.current_device.get_axis_range(self._rs_y_axis, default=(-32768, 32767))
            self.right_stick_analyzer.set_raw_ranges(min_rx, max_rx, min_ry, max_ry)
        else:
            self.left_stick_analyzer.set_raw_ranges(-32768, 32767, -32768, 32767)
            self.right_stick_analyzer.set_raw_ranges(-32768, 32767, -32768, 32767)

    def _on_profile_changed(self, index: int):
        self.current_profile_key = self.combo_profiles.currentData()
        self._update_axis_mappings()
        for code, btn in self.buttons_analyzer.buttons.items():
            btn.name, btn.description = get_button_info(self.current_profile_key, code)

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

            # Bridge digital triggers to trigger gauge bars (e.g. Switch ZL/ZR or standard LT/RT digital)
            btn_tokens = set(btn_name.lower().replace('/', ' ').replace('(', ' ').replace(')', ' ').split())
            if any(k in btn_tokens for k in ("zl", "lt", "l2", "4k")) or "left trigger" in btn_name.lower():
                self.triggers_analyzer.update_digital_trigger(is_left=True, is_pressed=is_pressed, code=self._trig_l_axis, name=btn_name)
            elif any(k in btn_tokens for k in ("zr", "rt", "r2", "3k")) or "right trigger" in btn_name.lower():
                self.triggers_analyzer.update_digital_trigger(is_left=False, is_pressed=is_pressed, code=self._trig_r_axis, name=btn_name)

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
            if code == self._ls_x_axis:
                self.left_stick_analyzer.update_axis(code, val, event.timestamp, is_x=True)
                return
            elif code == self._ls_y_axis:
                self.left_stick_analyzer.update_axis(code, val, event.timestamp, is_x=False)
                return

            # Right Stick (X, Y)
            if code == self._rs_x_axis:
                self.right_stick_analyzer.update_axis(code, val, event.timestamp, is_x=True)
                return
            elif code == self._rs_y_axis:
                self.right_stick_analyzer.update_axis(code, val, event.timestamp, is_x=False)
                return

            # Analog Triggers
            elif code in (self._trig_l_axis, self._trig_r_axis, ABS_BRAKE, ABS_GAS):
                trig_name = get_axis_info(self.current_profile_key, code)
                self.triggers_analyzer.update_trigger(code, val, name=trig_name)
                return

            # Inline multitouch touchpad axes if exposed on primary event node
            if code in (ABS_MT_SLOT, ABS_MT_POSITION_X, ABS_MT_POSITION_Y, ABS_MT_TRACKING_ID):
                self.touchpad_analyzer.process_event(event.ev_type, code, val)

        # Inline touchpad click/touch forwarding if exposed on primary node
        if (event.ev_type == EV_KEY and event.code in (BTN_LEFT, BTN_TOUCH) and
                self.current_device and self.current_device.touchpad_event_path == self.current_device.event_path):
            self.touchpad_analyzer.process_event(event.ev_type, event.code, event.value)

    def _on_touchpad_event(self, event: RawInputEvent):
        """Callback invoked from companion touchpad InputReader thread."""
        self.touchpad_analyzer.process_event(event.ev_type, event.code, event.value)

    def _on_motion_event(self, event: RawInputEvent):
        """Callback invoked from companion motion-sensor InputReader thread."""
        self.motion_analyzer.process_event(event.ev_type, event.code, event.value, event.timestamp)

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
        self._stop_readers()
        for d in self.devices:
            d.close()
        event.accept()

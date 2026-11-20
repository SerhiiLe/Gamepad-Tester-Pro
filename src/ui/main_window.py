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
        self.setWindowTitle("Gamepad Tester Pro — Комплексная диагностика игровых контроллеров")
        self.resize(1180, 820)
        self.setStyleSheet(DARK_THEME_QSS)

        # Data & Analysis Engine Instances
        self.devices: List[GamepadDevice] = []
        self.current_device: Optional[GamepadDevice] = None
        self.current_profile_key: str = "xbox"
        self.input_reader: Optional[InputReader] = None

        self.polling_analyzer = PollingAnalyzer()
        self.buttons_analyzer = ButtonsAnalyzer()
        self.left_stick_analyzer = StickAnalyzer(name="Левый стик (LS)")
        self.right_stick_analyzer = StickAnalyzer(name="Правый стик (RS)")
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

        # Top Control Bar (Device Selection, Profile, Battery, Refresh)
        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("<b>Контроллер:</b>"))
        self.combo_devices = QComboBox()
        self.combo_devices.setMinimumWidth(280)
        self.combo_devices.currentIndexChanged.connect(self._on_device_selected)
        top_bar.addWidget(self.combo_devices)

        btn_rescan = QPushButton("↻ Поиск устройств")
        btn_rescan.setMinimumWidth(140)
        btn_rescan.clicked.connect(self.rescan_devices)
        top_bar.addWidget(btn_rescan)

        top_bar.addSpacing(16)
        top_bar.addWidget(QLabel("<b>Раскладка:</b>"))
        self.combo_profiles = QComboBox()
        self.combo_profiles.setMinimumWidth(180)
        for pkey, pval in PROFILES.items():
            self.combo_profiles.addItem(pval["name"], pkey)
        self.combo_profiles.currentIndexChanged.connect(self._on_profile_changed)
        top_bar.addWidget(self.combo_profiles)

        top_bar.addStretch(1)
        self.lbl_battery = QLabel("🔋 Батарея: —")
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

        self.w_stick_left = StickWidget(self.left_stick_analyzer, title="Левый стик (LS)")
        top_row.addWidget(self.w_stick_left, stretch=3)

        self.w_triggers = TriggerWidget(self.triggers_analyzer)
        top_row.addWidget(self.w_triggers, stretch=0)

        self.w_stick_right = StickWidget(self.right_stick_analyzer, title="Правый стик (RS)")
        top_row.addWidget(self.w_stick_right, stretch=3)

        self.w_anomalies = StickAnomaliesWidget(self.left_stick_analyzer, self.right_stick_analyzer)
        top_row.addWidget(self.w_anomalies, stretch=4)

        l_sticks.addLayout(top_row, stretch=5)

        # Bottom Row: Two separate oscilloscopes in ms (Left Stick and Right Stick)
        bot_row = QHBoxLayout()
        self.w_snapback_left = StickOscilloscopeWidget(self.left_stick_analyzer, title="Левый стик (LS)")
        bot_row.addWidget(self.w_snapback_left, stretch=1)

        self.w_snapback_right = StickOscilloscopeWidget(self.right_stick_analyzer, title="Правый стик (RS)")
        bot_row.addWidget(self.w_snapback_right, stretch=1)

        l_sticks.addLayout(bot_row, stretch=4)

        self.tabs.addTab(tab_sticks, "🎯 Стики и курки")

        # Tab 2: Buttons & Chatter
        self.w_buttons = ButtonsTableWidget(self.buttons_analyzer)
        self.tabs.addTab(self.w_buttons, "🔘 Кнопки и дребезг (<7мс)")

        # Tab 3: Polling Rate
        self.w_polling = PollingWidget(self.polling_analyzer)
        self.tabs.addTab(self.w_polling, "⚡ Частота опроса (Hz)")

        # Tab 4: Feedback & LEDs
        self.w_feedback = FeedbackWidget(self.rumble_controller, self.led_controller)
        self.tabs.addTab(self.w_feedback, "📳 Вибрация и подсветка")

        # Tab 5: Diagnostic Report & PDF Export
        self.w_report = ReportWidget(self)
        self.tabs.addTab(self.w_report, "📋 Паспорт / Отчёт")

        # Polling Timer for triggers and battery update (30 FPS)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_gui_tick)
        self.update_timer.start(33)

        # Initial device discovery
        self.rescan_devices()

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
            self.combo_devices.addItem("Контроллеры не обнаружены")
            self.current_device = None
            self.rumble_controller.set_device(None)
            self.led_controller.set_device(None)
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
            elif code == ABS_Y:
                self.left_stick_analyzer.update_axis(code, val, event.timestamp, is_x=False)

            # Right Stick (RX, RY or Z, RZ)
            elif code in (ABS_RX, ABS_Z) and self.current_profile_key != "dinput_pc":
                self.right_stick_analyzer.update_axis(code, val, event.timestamp, is_x=True)
            elif code in (ABS_RY, ABS_RZ) and self.current_profile_key != "dinput_pc":
                self.right_stick_analyzer.update_axis(code, val, event.timestamp, is_x=False)

            # Analog Triggers (L2/R2, LT/RT, BRAKE/GAS)
            if code in (ABS_BRAKE, ABS_GAS, ABS_Z, ABS_RZ):
                trig_name = get_axis_info(self.current_profile_key, code)
                self.triggers_analyzer.update_trigger(code, val, name=trig_name)

    def _on_gui_tick(self):
        """Periodic tick on Qt main thread for widgets that update smoothly."""
        self.w_triggers.update_values()

        if self.current_device:
            cap, stat = self.current_device.get_battery_info()
            if cap is not None:
                self.lbl_battery.setText(f"🔋 Батарея: {cap}% ({stat})")
            else:
                self.lbl_battery.setText("🔌 Питание: USB (провод)")

    def closeEvent(self, event):
        """Clean shutdown of threads and actuators."""
        if self.input_reader:
            self.input_reader.stop()
        for d in self.devices:
            d.close()
        event.accept()

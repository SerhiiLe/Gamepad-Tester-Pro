"""
Force Feedback & LED Control Widget
Provides sliders for vibration intensity and separated controllers
for Sony DualSense/DS4 RGB Lightbar and Microsoft Xbox Ring of Light patterns.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QGroupBox, QComboBox, QTabWidget, QFrame
)
from PySide6.QtCore import Qt

from ...feedback.rumble import RumbleController
from ...feedback.leds import LedController


class FeedbackWidget(QWidget):
    """Panel for vibration actuators and separated Sony vs Xbox LED controls."""

    def __init__(self, rumble_ctrl: RumbleController, led_ctrl: LedController, parent=None):
        super().__init__(parent)
        self.rumble_ctrl = rumble_ctrl
        self.led_ctrl = led_ctrl

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Rumble GroupBox (Force Feedback)
        grp_rumble = QGroupBox("Тестирование вибромоторов (Force Feedback / Rumble)")
        l_rumble = QVBoxLayout(grp_rumble)

        # Left Motor (Heavy / Low Freq)
        row_left = QHBoxLayout()
        lbl_l = QLabel("Левый мотор (Тяжёлый / НЧ):")
        lbl_l.setMinimumWidth(210)
        row_left.addWidget(lbl_l)
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
        lbl_r = QLabel("Правый мотор (Лёгкий / ВЧ):")
        lbl_r.setMinimumWidth(210)
        row_right.addWidget(lbl_r)
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
        btn_pulse_l = QPushButton("🔴 Импульс Левый (1с)")
        btn_pulse_l.setMinimumWidth(170)
        btn_pulse_l.clicked.connect(self._pulse_left)
        btn_box.addWidget(btn_pulse_l)

        btn_pulse_r = QPushButton("🔵 Импульс Правый (1с)")
        btn_pulse_r.setMinimumWidth(170)
        btn_pulse_r.clicked.connect(self._pulse_right)
        btn_box.addWidget(btn_pulse_r)

        btn_pulse_both = QPushButton("🟣 Импульс Оба (1с)")
        btn_pulse_both.setMinimumWidth(170)
        btn_pulse_both.clicked.connect(self._pulse_both)
        btn_box.addWidget(btn_pulse_both)

        btn_stop = QPushButton("⏹ Стоп")
        btn_stop.setMinimumWidth(100)
        btn_stop.setObjectName("btn_danger")
        btn_stop.clicked.connect(self.rumble_ctrl.stop)
        btn_box.addWidget(btn_stop)
        l_rumble.addLayout(btn_box)

        layout.addWidget(grp_rumble)

        # 2. Separated LED Controls (Sony vs Xbox tabs)
        grp_led = QGroupBox("Управление индикацией и светодиодами (Раздельные команды)")
        l_led = QVBoxLayout(grp_led)

        self.led_tabs = QTabWidget()

        # Tab: Sony PlayStation
        tab_sony = QWidget()
        l_sony = QVBoxLayout(tab_sony)

        lbl_sony_desc = QLabel("<b>Подсветка Sony DualSense (PS5) & DualShock 4 (PS4) Lightbar:</b>")
        lbl_sony_desc.setStyleSheet("color: #38BDF8;")
        l_sony.addWidget(lbl_sony_desc)

        # Presets row
        row_presets = QHBoxLayout()
        row_presets.addWidget(QLabel("Пресеты:"))
        for name, rgb in LedController.COLOR_PRESETS.items():
            btn = QPushButton(name)
            btn.setMinimumWidth(75)
            btn.clicked.connect(lambda _, c=rgb: self._apply_sony_color(*c))
            row_presets.addWidget(btn)
        l_sony.addLayout(row_presets)

        # Custom RGB Sliders
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

        btn_apply_rgb = QPushButton("Применить RGB")
        btn_apply_rgb.setMinimumWidth(130)
        btn_apply_rgb.clicked.connect(self._on_custom_rgb)
        row_rgb.addWidget(btn_apply_rgb)

        l_sony.addLayout(row_rgb)
        self.led_tabs.addTab(tab_sony, "🎮 Sony PlayStation (RGB Lightbar)")

        # Tab: Microsoft Xbox
        tab_xbox = QWidget()
        l_xbox = QVBoxLayout(tab_xbox)

        lbl_xbox_desc = QLabel("<b>Светодиодное кольцо Microsoft Xbox 360 (Ring of Light):</b>")
        lbl_xbox_desc.setStyleSheet("color: #10B981;")
        l_xbox.addWidget(lbl_xbox_desc)

        # Player shortcuts
        row_players = QHBoxLayout()
        row_players.addWidget(QLabel("Игроки:"))
        for p_num, pat_id in [("1️⃣ Игрок 1", 2), ("2️⃣ Игрок 2", 3), ("3️⃣ Игрок 3", 4), ("4️⃣ Игрок 4", 5), ("⚫ Откл", 0)]:
            btn = QPushButton(p_num)
            btn.setMinimumWidth(90)
            btn.clicked.connect(lambda _, pid=pat_id: self._send_xbox_pattern(pid))
            row_players.addWidget(btn)
        l_xbox.addLayout(row_players)

        # Animated patterns
        row_patterns = QHBoxLayout()
        row_patterns.addWidget(QLabel("Режимы:"))
        for m_name, pat_id in [("🔄 Вращение", 10), ("⚡ Быстрое мигание", 11), ("⏳ Медленно", 12), ("🔀 Чередование", 13)]:
            btn = QPushButton(m_name)
            btn.setMinimumWidth(110)
            btn.clicked.connect(lambda _, pid=pat_id: self._send_xbox_pattern(pid))
            row_patterns.addWidget(btn)
        l_xbox.addLayout(row_patterns)

        # Elevated privileges notice
        self.lbl_xbox_status = QLabel(
            "⚠️ <b>Внимание (Права доступа):</b> Управление кольцом светодиодов xpad осуществляется через системный узел sysfs "
            "(<code>/sys/class/leds/xpad*/brightness</code>). В Linux для записи в этот узел по умолчанию требуются <b>повышенные права (root)</b>.<br>"
            "Если контроллер не реагирует на команды, запустите утилиту с <code>sudo</code>, либо разрешите запись командой:<br>"
            "<code>sudo chmod 666 /sys/class/leds/xpad*/brightness</code>"
        )
        self.lbl_xbox_status.setWordWrap(True)
        self.lbl_xbox_status.setStyleSheet("font-size: 11px; color: #F59E0B; background-color: #1E293B; border: 1px solid #334155; border-radius: 4px; padding: 6px;")
        l_xbox.addWidget(self.lbl_xbox_status)

        self.led_tabs.addTab(tab_xbox, "🎮 Microsoft Xbox (Ring of Light)")

        l_led.addWidget(self.led_tabs)
        layout.addWidget(grp_led)
        layout.addStretch(1)

    def _send_xbox_pattern(self, pid: int):
        ok, msg = self.led_ctrl.set_xpad_pattern(pid)
        if not ok:
            self.lbl_xbox_status.setText(
                f"❌ <b>Ошибка записи ({msg}):</b> Требуются права root. Выполните в терминале:<br>"
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

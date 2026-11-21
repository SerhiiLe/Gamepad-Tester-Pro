"""
Force Feedback & LED Control Widget
Provides sliders for vibration intensity, hardware support detection,
informative compatibility list, and separated controllers for Sony RGB Lightbar
and Microsoft Xbox Ring of Light patterns.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QGroupBox, QTabWidget, QFrame, QTextEdit
)
from PySide6.QtCore import Qt

from ...core.device import GamepadDevice
from ...feedback.rumble import RumbleController
from ...feedback.leds import LedController


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
        grp_rumble = QGroupBox("Тестирование вибромоторов (Force Feedback / Rumble)")
        l_rumble = QVBoxLayout(grp_rumble)
        l_rumble.setContentsMargins(10, 14, 10, 10)
        l_rumble.setSpacing(8)

        # Force Feedback Support Status Banner
        self.lbl_ff_status = QLabel()
        self.lbl_ff_status.setWordWrap(True)
        l_rumble.addWidget(self.lbl_ff_status)

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
        self.btn_pulse_l = QPushButton("🔴 Импульс Левый (1с)")
        self.btn_pulse_l.setMinimumWidth(170)
        self.btn_pulse_l.clicked.connect(self._pulse_left)
        btn_box.addWidget(self.btn_pulse_l)

        self.btn_pulse_r = QPushButton("🔵 Импульс Правый (1с)")
        self.btn_pulse_r.setMinimumWidth(170)
        self.btn_pulse_r.clicked.connect(self._pulse_right)
        btn_box.addWidget(self.btn_pulse_r)

        self.btn_pulse_both = QPushButton("🟣 Импульс Оба (1с)")
        self.btn_pulse_both.setMinimumWidth(170)
        self.btn_pulse_both.clicked.connect(self._pulse_both)
        btn_box.addWidget(self.btn_pulse_both)

        self.btn_stop = QPushButton("⏹ Стоп")
        self.btn_stop.setMinimumWidth(100)
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.clicked.connect(self.rumble_ctrl.stop)
        btn_box.addWidget(self.btn_stop)
        l_rumble.addLayout(btn_box)

        layout.addWidget(grp_rumble, stretch=0)

        # ======================================================================
        # 2. Separated LED Controls (3 Tabs: Info, Sony, Xbox)
        # ======================================================================
        grp_led = QGroupBox("Управление индикацией и светодиодами (Раздельные команды)")
        l_led = QVBoxLayout(grp_led)
        l_led.setContentsMargins(10, 14, 10, 10)
        l_led.setSpacing(6)

        self.led_tabs = QTabWidget()

        # ----------------------------------------------------------------------
        # Tab 0: Information & Hardware Compatibility (Scrollable Text Block)
        # ----------------------------------------------------------------------
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

        info_html = """
        <div style="font-family: 'Segoe UI', 'Ubuntu', 'Roboto', sans-serif;">
          <h3 style="color: #38BDF8; margin-top: 0px; margin-bottom: 6px;">ℹ️ Аппаратная поддержка световой индикации и подсветки в Linux</h3>
          <p style="color: #CBD5E1; font-size: 13px; line-height: 1.45; margin-bottom: 12px;">
            В отличие от стандартных кнопок и осей, прямое программное управление светодиодами геймпада
            не стандартизировано в базовом USB HID и поддерживается ядром Linux только для специализированных
            фирменных платформ со специфическими системными драйверами:
          </p>

          <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom: 10px; background-color: #1E293B; border: 1px solid #334155; border-radius: 6px;">
            <tr>
              <td>
                <b style="color: #38BDF8; font-size: 13px;">🎮 Sony PlayStation — Полноцветный RGB Lightbar</b><br/>
                <span style="color: #94A3B8; font-size: 12px; line-height: 1.45;">
                  • <b>DualSense (PS5):</b> Индивидуальная RGB-подсветка контура тачпада и индикация игрока (драйвер ядра <code>hid-playstation</code>). Поддерживаются прямые HID output reports (<code>0x02</code> / <code>0x31</code>) и sysfs.<br/>
                  • <b>DualShock 4 (PS4):</b> Световая полоса RGB Lightbar (драйвер <code>hid-sony</code> или <code>hid-playstation</code>).
                </span>
              </td>
            </tr>
          </table>

          <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom: 10px; background-color: #1E293B; border: 1px solid #334155; border-radius: 6px;">
            <tr>
              <td>
                <b style="color: #10B981; font-size: 13px;">🎮 Microsoft Xbox — Светодиодное кольцо (Ring of Light)</b><br/>
                <span style="color: #94A3B8; font-size: 12px; line-height: 1.45;">
                  • <b>Xbox 360 Controller (проводные и беспроводные с ресивером):</b> 4-сегментное кольцо квадрантов игроков и системные анимации (вращение, мигание, чередование) через драйвер <code>xpad</code> в sysfs (<code>/sys/class/leds/xpad*/brightness</code>). <i>Требуются права root или udev-правило.</i><br/>
                  • <b>Xbox One / Series:</b> Кнопка Xbox светится статично белым светом и программно не управляется через открытый драйвер.
                </span>
              </td>
            </tr>
          </table>

          <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom: 6px; background-color: #1E293B; border: 1px solid #334155; border-radius: 6px;">
            <tr>
              <td>
                <b style="color: #F59E0B; font-size: 13px;">❌ Остальные контроллеры (Не поддерживаются ОС)</b><br/>
                <span style="color: #94A3B8; font-size: 12px; line-height: 1.45;">
                  • <b>Nintendo Switch Pro / Joy-Con:</b> Кольцо подсветки кнопки Home требует закрытых вендорных субкоманд <code>hid-nintendo</code>.<br/>
                  • <b>Сторонние геймпады (Flydigi, 8BitDo, Gamesir, Defender, реплики):</b> Декоративная подсветка управляется автономным микроконтроллером на корпусе (комбинациями аппаратных кнопок) и не имеет программного API в ОС.<br/>
                  • <b>Стандартные DInput / Generic USB геймпады:</b> Программное управление светодиодами отсутствует в HID-дескрипторе.
                </span>
              </td>
            </tr>
          </table>
        </div>
        """
        self.txt_info.setHtml(info_html)
        l_info.addWidget(self.txt_info)
        self.led_tabs.addTab(tab_info, "ℹ️ О технологии и совместимости")

        # ----------------------------------------------------------------------
        # Tab 1: Sony PlayStation (DualSense / DS4)
        # ----------------------------------------------------------------------
        tab_sony = QWidget()
        l_sony = QVBoxLayout(tab_sony)
        l_sony.setContentsMargins(10, 10, 10, 10)
        l_sony.setSpacing(10)

        lbl_sony_desc = QLabel("<b>Подсветка Sony DualSense (PS5) & DualShock 4 (PS4) Lightbar:</b>")
        lbl_sony_desc.setStyleSheet("color: #38BDF8; font-size: 13px;")
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
        l_sony.addStretch(1)
        self.led_tabs.addTab(tab_sony, "🎮 Sony PlayStation (RGB Lightbar)")

        # ----------------------------------------------------------------------
        # Tab 2: Microsoft Xbox (Xbox 360 Ring of Light)
        # ----------------------------------------------------------------------
        tab_xbox = QWidget()
        l_xbox = QVBoxLayout(tab_xbox)
        l_xbox.setContentsMargins(10, 10, 10, 10)
        l_xbox.setSpacing(10)

        lbl_xbox_desc = QLabel("<b>Светодиодное кольцо Microsoft Xbox 360 (Ring of Light):</b>")
        lbl_xbox_desc.setStyleSheet("color: #10B981; font-size: 13px;")
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

        # Elevated privileges notice (Generously sized, dynamic layout)
        self.lbl_xbox_status = QLabel(
            "⚠️ <b>Внимание (Права доступа в Linux):</b> Управление кольцом светодиодов xpad осуществляется через системный узел sysfs "
            "(<code>/sys/class/leds/xpad*/brightness</code>). В Linux для записи в этот узел по умолчанию требуются <b>повышенные права (root)</b>.<br><br>"
            "Если контроллер не реагирует на команды переключения квадрантов или анимаций:<br>"
            "• Запустите утилиту с <code>sudo</code>, либо<br>"
            "• Разрешите однократно запись командой в терминале:<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<code>sudo chmod 666 /sys/class/leds/xpad*/brightness</code><br>"
            "• Либо создайте постоянное udev-правило для доступа без root."
        )
        self.lbl_xbox_status.setWordWrap(True)
        self.lbl_xbox_status.setStyleSheet(
            "font-size: 11px; color: #F59E0B; background-color: #1E293B; "
            "border: 1px solid #334155; border-radius: 6px; padding: 10px 12px; line-height: 1.4;"
        )
        l_xbox.addWidget(self.lbl_xbox_status)
        l_xbox.addStretch(1)

        self.led_tabs.addTab(tab_xbox, "🎮 Microsoft Xbox (Ring of Light)")

        l_led.addWidget(self.led_tabs)
        layout.addWidget(grp_led, stretch=1)

        # Initialize rumble state
        self._update_rumble_support()

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
            self.lbl_ff_status.setText(
                "⚠️ <b>Контроллер не выбран:</b> Подключите игровой контроллер для тестирования вибромоторов."
            )
            self.lbl_ff_status.setStyleSheet(
                "background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 8px 12px; color: #94A3B8; font-size: 12px;"
            )
        elif not has_ff:
            self.lbl_ff_status.setText(
                "⚠️ <b>Внимание:</b> Подключенное устройство не поддерживает аппаратную обратную связь "
                "(Force Feedback / виброотклик отсутствует в дескрипторе HID). Команды вибрации недоступны."
            )
            self.lbl_ff_status.setStyleSheet(
                "background-color: #2D1515; border: 1px solid #7F1D1D; border-radius: 6px; padding: 8px 12px; color: #FCA5A5; font-size: 12px;"
            )
        else:
            self.lbl_ff_status.setText(
                "✅ <b>Обратная связь поддерживается:</b> Обнаружен активный драйвер виброотклика (EV_FF / Force Feedback). "
                "Вы можете протестировать раздельно левый (тяжёлый/НЧ) и правый (лёгкий/ВЧ) вибромоторы."
            )
            self.lbl_ff_status.setStyleSheet(
                "background-color: #0E291E; border: 1px solid #065F46; border-radius: 6px; padding: 6px 12px; color: #6EE7B7; font-size: 12px;"
            )

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

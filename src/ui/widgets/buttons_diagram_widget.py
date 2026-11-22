"""
Gamepad Visual Diagram Widget
Interactive schematic diagram of a standard gamepad layout.
Displays 3-state button verification:
  - Untested (empty outline)
  - Currently Pressed (bright vibrant fill)
  - Tested / Previously Pressed (muted fill)
Displays real-time stick deflection and analog trigger fill gauges.
"""

from typing import Callable, Dict, List, Optional, Set, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QLinearGradient
)

from ...analysis.buttons import ButtonsAnalyzer
from ...analysis.sticks import StickAnalyzer
from ...analysis.triggers import TriggersAnalyzer
from ...core.constants import (
    BTN_SOUTH, BTN_EAST, BTN_NORTH, BTN_WEST, BTN_C, BTN_Z,
    BTN_TL, BTN_TR, BTN_TL2, BTN_TR2,
    BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL, BTN_THUMBR, BTN_CAPTURE,
    BTN_DPAD_UP, BTN_DPAD_DOWN, BTN_DPAD_LEFT, BTN_DPAD_RIGHT
)
from ...core.profiles import PROFILES, get_button_info
from ...i18n import tr


# Visual Button States
STATE_UNTESTED = 0  # Empty outline
STATE_PRESSED = 1   # Bright vibrant emerald fill
STATE_TESTED = 2    # Dim muted forest green fill


class GamepadCanvas(QWidget):
    """Interactive vector canvas rendering the schematic gamepad with live states."""

    def __init__(
        self,
        buttons_analyzer: ButtonsAnalyzer,
        left_stick_analyzer: StickAnalyzer,
        right_stick_analyzer: StickAnalyzer,
        triggers_analyzer: TriggersAnalyzer,
        profile_getter: Callable[[], str],
        tested_roles: Set[str],
        parent=None
    ):
        super().__init__(parent)
        self.buttons_analyzer = buttons_analyzer
        self.left_stick_analyzer = left_stick_analyzer
        self.right_stick_analyzer = right_stick_analyzer
        self.triggers_analyzer = triggers_analyzer
        self.profile_getter = profile_getter
        self.tested_roles = tested_roles

        self.setMinimumSize(480, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # Canvas logical dimensions: 760 wide by 460 high
        base_w = 760.0
        base_h = 460.0
        scale = min(w / base_w, h / base_h)
        scale = max(0.4, scale)

        painter.translate(w / 2.0, h / 2.0)
        painter.scale(scale, scale)

        profile_key = self.profile_getter() if self.profile_getter else "standard"
        roles_info = self._resolve_roles(profile_key)

        # 1. Draw Gamepad Chassis Silhouette
        self._draw_chassis(painter)

        # 2. Draw Shoulders (Bumpers & Triggers)
        self._draw_shoulders(painter, roles_info)

        # 3. Draw Center Controls (Back, Guide, Start)
        self._draw_center_controls(painter, roles_info)

        # 4. Draw D-Pad
        self._draw_dpad(painter, roles_info)

        # 5. Draw Action Buttons (ABXY diamond)
        self._draw_action_buttons(painter, roles_info)

        # 6. Draw Analog Sticks (Base + Movable Thumbcap + Click state)
        self._draw_sticks(painter, roles_info)

        # 7. Draw Extra Buttons if present (Touchpad, Capture, C, Z)
        self._draw_extra_buttons(painter, profile_key)

        painter.end()

    def _resolve_roles(self, profile_key: str) -> Dict[str, Dict]:
        """Resolves active button codes, short labels, and live states for each role."""
        prof = PROFILES.get(profile_key, PROFILES.get("standard", {}))
        btn_cfg = prof.get("buttons", {})

        # Default standard codes
        code_map = {
            "dpad_up": BTN_DPAD_UP,
            "dpad_down": BTN_DPAD_DOWN,
            "dpad_left": BTN_DPAD_LEFT,
            "dpad_right": BTN_DPAD_RIGHT,
            "action_south": BTN_SOUTH,
            "action_east": BTN_EAST,
            "action_west": BTN_NORTH,
            "action_north": BTN_WEST,
            "bumper_l": BTN_TL,
            "bumper_r": BTN_TR,
            "trigger_l": BTN_TL2,
            "trigger_r": BTN_TR2,
            "back": BTN_SELECT,
            "start": BTN_START,
            "guide": BTN_MODE,
            "stick_l": BTN_THUMBL,
            "stick_r": BTN_THUMBR,
        }

        # Dynamic profile descriptor matching
        for code, info in btn_cfg.items():
            name, desc = info
            text = f"{name} {desc}".lower()
            tokens = set(text.replace('/', ' ').replace('(', ' ').replace(')', ' ').split())

            if "bottom" in tokens or "south" in tokens:
                code_map["action_south"] = code
            elif "right" in tokens and ("action" in tokens or "circle" in tokens or "east" in tokens):
                code_map["action_east"] = code
            elif "top" in tokens and ("action" in tokens or "triangle" in tokens or "north" in tokens):
                code_map["action_north"] = code
            elif "left" in tokens and ("action" in tokens or "square" in tokens or "west" in tokens):
                code_map["action_west"] = code
            elif any(k in tokens for k in ("l1", "lb", "4p")) or "left bumper" in text:
                code_map["bumper_l"] = code
            elif any(k in tokens for k in ("r1", "rb", "3p")) or "right bumper" in text:
                code_map["bumper_r"] = code
            elif any(k in tokens for k in ("l2", "lt", "zl", "4k")) or "left trigger" in text:
                code_map["trigger_l"] = code
            elif any(k in tokens for k in ("r2", "rt", "zr", "3k")) or "right trigger" in text:
                code_map["trigger_r"] = code
            elif any(k in tokens for k in ("select", "back", "share", "minus", "create", "coin")):
                code_map["back"] = code
            elif any(k in tokens for k in ("start", "options", "menu", "plus")):
                code_map["start"] = code
            elif any(k in tokens for k in ("guide", "home", "mode")) or "ps button" in text:
                code_map["guide"] = code
            elif "l3" in tokens or "left stick click" in text or "ls click" in text:
                code_map["stick_l"] = code
            elif "r3" in tokens or "right stick click" in text or "rs click" in text:
                code_map["stick_r"] = code

        # Resolve short label and state for each role
        l_pct, r_pct = self.triggers_analyzer.get_normalized_values()
        roles: Dict[str, Dict] = {}

        for role, code in code_map.items():
            lbl, _ = get_button_info(profile_key, code)
            short_lbl = self._clean_short_label(role, lbl, profile_key)

            # Determine press state
            btn = self.buttons_analyzer.buttons.get(code)
            is_pressed = bool(btn and btn.is_pressed)
            press_count = btn.press_count if btn else 0

            # Analog trigger deflection bridge
            pct = 0.0
            if role == "trigger_l":
                pct = l_pct
                if l_pct > 12.0:
                    is_pressed = True
            elif role == "trigger_r":
                pct = r_pct
                if r_pct > 12.0:
                    is_pressed = True

            # Register tested state
            if is_pressed or press_count > 0 or (pct > 12.0):
                self.tested_roles.add(role)

            if is_pressed:
                state = STATE_PRESSED
            elif role in self.tested_roles:
                state = STATE_TESTED
            else:
                state = STATE_UNTESTED

            roles[role] = {
                "code": code,
                "label": short_lbl,
                "state": state,
                "pct": pct
            }

        return roles

    def _clean_short_label(self, role: str, full_name: str, profile_key: str) -> str:
        """Converts descriptive profile labels into compact glyphs for the diagram."""
        if role == "dpad_up":
            return "▲"
        elif role == "dpad_down":
            return "▼"
        elif role == "dpad_left":
            return "◀"
        elif role == "dpad_right":
            return "▶"

        # Action Buttons
        if role in ("action_south", "action_east", "action_west", "action_north"):
            # Symbols
            if "✕" in full_name or "cross" in full_name.lower():
                return "✕"
            if "◯" in full_name or "circle" in full_name.lower():
                return "◯"
            if "□" in full_name or "square" in full_name.lower():
                return "□"
            if "△" in full_name or "triangle" in full_name.lower():
                return "△"
            # Single letters
            for char in full_name.split()[0]:
                if char.isalpha():
                    return char

        # Shoulders
        if role == "bumper_l":
            return "L1" if "dualsense" in profile_key or "ps" in profile_key else ("L" if "switch" in profile_key else "LB")
        if role == "bumper_r":
            return "R1" if "dualsense" in profile_key or "ps" in profile_key else ("R" if "switch" in profile_key else "RB")
        if role == "trigger_l":
            return "L2" if "dualsense" in profile_key or "ps" in profile_key else ("ZL" if "switch" in profile_key else "LT")
        if role == "trigger_r":
            return "R2" if "dualsense" in profile_key or "ps" in profile_key else ("ZR" if "switch" in profile_key else "RT")

        # Center
        if role == "back":
            return "Share" if "dualsense" in profile_key or "ps" in profile_key else ("–" if "switch" in profile_key else "Back")
        if role == "start":
            return "Options" if "dualsense" in profile_key or "ps" in profile_key else ("+" if "switch" in profile_key else "Start")
        if role == "guide":
            return "PS" if "dualsense" in profile_key or "ps" in profile_key else "Home"

        # Sticks
        if role == "stick_l":
            return "L3" if "dualsense" in profile_key or "ps" in profile_key else "LS"
        if role == "stick_r":
            return "R3" if "dualsense" in profile_key or "ps" in profile_key else "RS"

        return full_name.split()[0] if full_name else ""

    def _get_colors(self, state: int) -> Tuple[QColor, QColor, QColor, float]:
        """Returns (background_color, border_color, text_color, border_width) for state."""
        if state == STATE_PRESSED:
            return QColor("#10B981"), QColor("#34D399"), QColor("#FFFFFF"), 2.5
        elif state == STATE_TESTED:
            return QColor(6, 78, 59, 210), QColor("#059669"), QColor("#6EE7B7"), 1.8
        else:
            return QColor(30, 41, 59, 140), QColor("#475569"), QColor("#94A3B8"), 1.5

    def _draw_chassis(self, p: QPainter):
        """Draws the dark ergonomic gamepad body silhouette."""
        body = QPainterPath()
        body.moveTo(-250, -85)
        body.quadTo(-280, -80, -290, -40)
        body.cubicTo(-310, 10, -300, 90, -230, 155)
        body.quadTo(-200, 175, -170, 155)
        body.cubicTo(-135, 110, -110, 75, -50, 75)
        body.quadTo(0, 90, 50, 75)
        body.cubicTo(110, 75, 135, 110, 170, 155)
        body.quadTo(200, 175, 230, 155)
        body.cubicTo(300, 90, 310, 10, 290, -40)
        body.quadTo(280, -80, 250, -85)
        body.quadTo(0, -95, -250, -85)
        body.closeSubpath()

        grad = QLinearGradient(0, -95, 0, 175)
        grad.setColorAt(0.0, QColor("#1E293B"))
        grad.setColorAt(0.5, QColor("#131D2E"))
        grad.setColorAt(1.0, QColor("#0B111E"))

        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#334155"), 2.0))
        p.drawPath(body)

        # Grip texture accent arcs
        p.setPen(QPen(QColor(51, 65, 85, 90), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(-275, -10, 90, 130), 40 * 16, 160 * 16)
        p.drawArc(QRectF(185, -10, 90, 130), -20 * 16, 160 * 16)

    def _draw_shoulders(self, p: QPainter, roles: Dict[str, Dict]):
        """Draws Left/Right Bumpers and Triggers (with analog fill gauges)."""
        # LT / L2
        self._draw_trigger_box(p, QRectF(-255, -165, 95, 34), roles.get("trigger_l", {}))
        # LB / L1
        self._draw_bumper_box(p, QRectF(-255, -122, 95, 28), roles.get("bumper_l", {}))
        # RT / R2
        self._draw_trigger_box(p, QRectF(160, -165, 95, 34), roles.get("trigger_r", {}))
        # RB / R1
        self._draw_bumper_box(p, QRectF(160, -122, 95, 28), roles.get("bumper_r", {}))

    def _draw_trigger_box(self, p: QPainter, rect: QRectF, info: Dict):
        state = info.get("state", STATE_UNTESTED)
        label = info.get("label", "LT")
        pct = info.get("pct", 0.0)

        bg, border, text_col, b_w = self._get_colors(state)
        p.setPen(QPen(border, b_w))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(rect, 7, 7)

        # Proportional fill gauge for analog deflection
        if pct > 0:
            fill_w = (rect.width() - 4.0) * (min(100.0, pct) / 100.0)
            fill_rect = QRectF(rect.x() + 2, rect.y() + 2, fill_w, rect.height() - 4)
            p.setPen(Qt.NoPen)
            gauge_grad = QLinearGradient(fill_rect.topLeft(), fill_rect.bottomRight())
            gauge_grad.setColorAt(0.0, QColor(16, 185, 129, 180))
            gauge_grad.setColorAt(1.0, QColor(52, 211, 153, 240))
            p.setBrush(QBrush(gauge_grad))
            p.drawRoundedRect(fill_rect, 5, 5)

        # Label text with percentage
        p.setPen(QPen(text_col))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        display_text = f"{label} {int(pct)}%" if pct > 0 else label
        p.drawText(rect, Qt.AlignCenter, display_text)

    def _draw_bumper_box(self, p: QPainter, rect: QRectF, info: Dict):
        state = info.get("state", STATE_UNTESTED)
        label = info.get("label", "LB")

        bg, border, text_col, b_w = self._get_colors(state)
        p.setPen(QPen(border, b_w))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(rect, 6, 6)

        p.setPen(QPen(text_col))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, label)

    def _draw_center_controls(self, p: QPainter, roles: Dict[str, Dict]):
        """Draws Select/Back, Home/Guide, and Start/Options buttons."""
        # Back / Share / Minus
        self._draw_center_pill(p, QRectF(-85, -45, 52, 24), roles.get("back", {}))
        # Guide / Home
        self._draw_home_circle(p, QPointF(0, -35), 20.0, roles.get("guide", {}))
        # Start / Options / Plus
        self._draw_center_pill(p, QRectF(33, -45, 52, 24), roles.get("start", {}))

    def _draw_center_pill(self, p: QPainter, rect: QRectF, info: Dict):
        state = info.get("state", STATE_UNTESTED)
        label = info.get("label", "Back")

        bg, border, text_col, b_w = self._get_colors(state)
        p.setPen(QPen(border, b_w))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(rect, 6, 6)

        p.setPen(QPen(text_col))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, label)

    def _draw_home_circle(self, p: QPainter, center: QPointF, radius: float, info: Dict):
        state = info.get("state", STATE_UNTESTED)
        label = info.get("label", "Home")

        bg, border, text_col, b_w = self._get_colors(state)
        p.setPen(QPen(border, b_w))
        p.setBrush(QBrush(bg))
        p.drawEllipse(center, radius, radius)

        p.setPen(QPen(text_col))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                   Qt.AlignCenter, label)

    def _draw_dpad(self, p: QPainter, roles: Dict[str, Dict]):
        """Draws the 4-wing D-Pad cross."""
        cx = -180.0
        cy = 25.0
        w = 30.0

        # Draw dark hub connecting the arms
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#0F172A")))
        p.drawRect(QRectF(cx - w / 2, cy - w / 2, w, w))

        # 4 Arms
        self._draw_dpad_wing(p, QRectF(cx - w / 2, cy - w / 2 - w, w, w), roles.get("dpad_up", {}), "▲")
        self._draw_dpad_wing(p, QRectF(cx - w / 2, cy + w / 2, w, w), roles.get("dpad_down", {}), "▼")
        self._draw_dpad_wing(p, QRectF(cx - w / 2 - w, cy - w / 2, w, w), roles.get("dpad_left", {}), "◀")
        self._draw_dpad_wing(p, QRectF(cx + w / 2, cy - w / 2, w, w), roles.get("dpad_right", {}), "▶")

    def _draw_dpad_wing(self, p: QPainter, rect: QRectF, info: Dict, arrow: str):
        state = info.get("state", STATE_UNTESTED)
        bg, border, text_col, b_w = self._get_colors(state)

        p.setPen(QPen(border, b_w))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(rect, 4, 4)

        p.setPen(QPen(text_col))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, arrow)

    def _draw_action_buttons(self, p: QPainter, roles: Dict[str, Dict]):
        """Draws the 4 diamond action buttons (ABXY / Cross-Circle-Square-Triangle)."""
        cx = 180.0
        cy = 25.0
        r = 17.0
        d = 45.0

        # North (Top)
        self._draw_action_circle(p, QPointF(cx, cy - d), r, roles.get("action_north", {}))
        # South (Bottom)
        self._draw_action_circle(p, QPointF(cx, cy + d), r, roles.get("action_south", {}))
        # West (Left)
        self._draw_action_circle(p, QPointF(cx - d, cy), r, roles.get("action_west", {}))
        # East (Right)
        self._draw_action_circle(p, QPointF(cx + d, cy), r, roles.get("action_east", {}))

    def _draw_action_circle(self, p: QPainter, center: QPointF, radius: float, info: Dict):
        state = info.get("state", STATE_UNTESTED)
        label = info.get("label", "A")

        bg, border, text_col, b_w = self._get_colors(state)
        p.setPen(QPen(border, b_w))
        p.setBrush(QBrush(bg))
        p.drawEllipse(center, radius, radius)

        p.setPen(QPen(text_col))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                   Qt.AlignCenter, label)

    def _draw_sticks(self, p: QPainter, roles: Dict[str, Dict]):
        """Draws Left and Right sticks: base bezel + crosshair + real-time moving thumbcap."""
        # Left Stick at (-85, 95)
        self._draw_single_stick(
            p,
            base_center=QPointF(-85.0, 95.0),
            curr_x=self.left_stick_analyzer.curr_x,
            curr_y=self.left_stick_analyzer.curr_y,
            info=roles.get("stick_l", {}),
            default_label="LS"
        )

        # Right Stick at (85, 95)
        self._draw_single_stick(
            p,
            base_center=QPointF(85.0, 95.0),
            curr_x=self.right_stick_analyzer.curr_x,
            curr_y=self.right_stick_analyzer.curr_y,
            info=roles.get("stick_r", {}),
            default_label="RS"
        )

    def _draw_single_stick(
        self,
        p: QPainter,
        base_center: QPointF,
        curr_x: float,
        curr_y: float,
        info: Dict,
        default_label: str
    ):
        base_radius = 38.0
        cap_radius = 21.0
        max_travel = base_radius - cap_radius  # 17.0 px

        # 1. Base Bezel
        p.setPen(QPen(QColor("#334155"), 1.8))
        p.setBrush(QBrush(QColor("#0F172A")))
        p.drawEllipse(base_center, base_radius, base_radius)

        # Crosshair lines marking center
        p.setPen(QPen(QColor(71, 85, 105, 100), 1.0, Qt.DashLine))
        p.drawLine(QPointF(base_center.x() - base_radius + 4, base_center.y()),
                   QPointF(base_center.x() + base_radius - 4, base_center.y()))
        p.drawLine(QPointF(base_center.x(), base_center.y() - base_radius + 4),
                   QPointF(base_center.x(), base_center.y() + base_radius - 4))

        # 2. Moving Thumbstick Cap
        cap_cx = base_center.x() + (curr_x * max_travel)
        cap_cy = base_center.y() - (curr_y * max_travel)  # Qt inverted Y
        cap_center = QPointF(cap_cx, cap_cy)

        state = info.get("state", STATE_UNTESTED)
        label = info.get("label", default_label)

        bg, border, text_col, b_w = self._get_colors(state)
        p.setPen(QPen(border, b_w))
        p.setBrush(QBrush(bg))
        p.drawEllipse(cap_center, cap_radius, cap_radius)

        # Label inside thumbcap (L3/LS or R3/RS)
        p.setPen(QPen(text_col))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(QRectF(cap_center.x() - cap_radius, cap_center.y() - cap_radius,
                          cap_radius * 2, cap_radius * 2),
                   Qt.AlignCenter, label)

        # 3. Coordinate label below base
        p.setPen(QPen(QColor("#64748B")))
        p.setFont(QFont("Segoe UI", 8))
        coord_rect = QRectF(base_center.x() - 60, base_center.y() + base_radius + 4, 120, 16)
        p.drawText(coord_rect, Qt.AlignCenter, f"X:{curr_x:+.2f} Y:{curr_y:+.2f}")

    def _draw_extra_buttons(self, p: QPainter, profile_key: str):
        """Draws badges for extra buttons (Touchpad, Capture, C, Z) if detected on device."""
        extra_codes = [BTN_C, BTN_Z, BTN_CAPTURE]
        detected = [c for c in extra_codes if c in self.buttons_analyzer.buttons]

        if not detected:
            return

        x = -120.0
        y = 158.0
        w = 60.0
        h = 20.0

        for code in detected:
            btn = self.buttons_analyzer.buttons[code]
            state = STATE_PRESSED if btn.is_pressed else (STATE_TESTED if btn.press_count > 0 else STATE_UNTESTED)
            bg, border, text_col, b_w = self._get_colors(state)

            rect = QRectF(x, y, w, h)
            p.setPen(QPen(border, b_w))
            p.setBrush(QBrush(bg))
            p.drawRoundedRect(rect, 4, 4)

            p.setPen(QPen(text_col))
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            lbl, _ = get_button_info(profile_key, code)
            p.drawText(rect, Qt.AlignCenter, lbl.split()[0])

            x += w + 8


class ButtonsDiagramWidget(QWidget):
    """
    Complete visual button and stick testing page.
    Includes live progress counters, legend, reset button, and real-time canvas.
    """

    PRIMARY_ROLES = [
        "dpad_up", "dpad_down", "dpad_left", "dpad_right",
        "action_south", "action_east", "action_west", "action_north",
        "bumper_l", "bumper_r", "trigger_l", "trigger_r",
        "back", "start", "guide", "stick_l", "stick_r"
    ]

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
        self.buttons_analyzer = buttons_analyzer
        self.left_stick_analyzer = left_stick_analyzer
        self.right_stick_analyzer = right_stick_analyzer
        self.triggers_analyzer = triggers_analyzer
        self.profile_getter = profile_getter

        self.tested_roles: Set[str] = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Top Header Bar: Title, Progress, Reset Button
        header = QHBoxLayout()
        self.lbl_title = QLabel(tr("diagram_title"))
        self.lbl_title.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 13px;")
        header.addWidget(self.lbl_title)

        header.addStretch(1)

        self.lbl_progress = QLabel()
        self.lbl_progress.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: bold;")
        header.addWidget(self.lbl_progress)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.PRIMARY_ROLES))
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(130)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 3px;
            }
        """)
        header.addWidget(self.progress_bar)

        self.btn_reset = QPushButton(tr("btn_reset_diagram"))
        self.btn_reset.setMinimumWidth(140)
        self.btn_reset.clicked.connect(self.reset_tested)
        header.addWidget(self.btn_reset)

        layout.addLayout(header)

        # 2. Legend Row
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        self.legend_untested = QLabel(f"⚪ {tr('legend_untested')}")
        self.legend_untested.setStyleSheet("color: #94A3B8; font-size: 11px;")
        legend_layout.addWidget(self.legend_untested)

        self.legend_pressed = QLabel(f"🟢 {tr('legend_pressed')}")
        self.legend_pressed.setStyleSheet("color: #34D399; font-size: 11px; font-weight: bold;")
        legend_layout.addWidget(self.legend_pressed)

        self.legend_tested = QLabel(f"🟩 {tr('legend_tested')}")
        self.legend_tested.setStyleSheet("color: #6EE7B7; font-size: 11px;")
        legend_layout.addWidget(self.legend_tested)

        self.lbl_all_done = QLabel(tr("diagram_all_tested"))
        self.lbl_all_done.setStyleSheet("color: #34D399; font-weight: bold; font-size: 11px;")
        self.lbl_all_done.setVisible(False)
        legend_layout.addWidget(self.lbl_all_done)

        legend_layout.addStretch(1)
        layout.addLayout(legend_layout)

        # 3. Canvas
        self.canvas = GamepadCanvas(
            buttons_analyzer=self.buttons_analyzer,
            left_stick_analyzer=self.left_stick_analyzer,
            right_stick_analyzer=self.right_stick_analyzer,
            triggers_analyzer=self.triggers_analyzer,
            profile_getter=self.profile_getter,
            tested_roles=self.tested_roles,
            parent=self
        )
        layout.addWidget(self.canvas, stretch=1)

        # 4. Bottom Status & Telemetry Bar
        self.lbl_telemetry = QLabel()
        self.lbl_telemetry.setStyleSheet(
            "background-color: #0F172A; border: 1px solid #1E293B; border-radius: 5px; "
            "padding: 5px 10px; color: #94A3B8; font-size: 11px;"
        )
        layout.addWidget(self.lbl_telemetry)

        # Real-time UI refresh timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(33)

        self._last_pressed_name = ""
        self._update_progress_ui()

    def reset_tested(self):
        """Clears all tested badges and resets progress."""
        self.tested_roles.clear()
        self._last_pressed_name = ""
        self.canvas.update()
        self._update_progress_ui()

    def retranslate_ui(self):
        """Retranslates all text labels."""
        self.lbl_title.setText(tr("diagram_title"))
        self.btn_reset.setText(tr("btn_reset_diagram"))
        self.legend_untested.setText(f"⚪ {tr('legend_untested')}")
        self.legend_pressed.setText(f"🟢 {tr('legend_pressed')}")
        self.legend_tested.setText(f"🟩 {tr('legend_tested')}")
        self.lbl_all_done.setText(tr("diagram_all_tested"))
        self._update_progress_ui()

    def _on_tick(self):
        """Periodic 30 FPS tick to update sticks, triggers, and telemetry."""
        self.canvas.update()

        # Check for newly pressed button for telemetry
        for code, btn in self.buttons_analyzer.buttons.items():
            if btn.is_pressed:
                self._last_pressed_name = f"{btn.name} (0x{code:03X})"

        self._update_progress_ui()

    def _update_progress_ui(self):
        tested_count = sum(1 for r in self.PRIMARY_ROLES if r in self.tested_roles)
        total = len(self.PRIMARY_ROLES)
        pct = int((tested_count / float(total)) * 100.0)

        self.progress_bar.setValue(tested_count)
        self.lbl_progress.setText(tr("diagram_tested_count", tested=tested_count, total=total, pct=pct))
        self.lbl_all_done.setVisible(tested_count == total)

        # Telemetry string
        lx = self.left_stick_analyzer.curr_x
        ly = self.left_stick_analyzer.curr_y
        rx = self.right_stick_analyzer.curr_x
        ry = self.right_stick_analyzer.curr_y
        l_pct, r_pct = self.triggers_analyzer.get_normalized_values()

        last_str = tr("diagram_last_btn", btn=self._last_pressed_name) if self._last_pressed_name else tr("diagram_no_press")
        telem_str = tr("diagram_telemetry", lx=lx, ly=ly, rx=rx, ry=ry, lt=int(l_pct), rt=int(r_pct))
        self.lbl_telemetry.setText(f"{telem_str}    |    {last_str}")

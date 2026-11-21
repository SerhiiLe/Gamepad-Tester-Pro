"""
Gamepad Profiles & Layout Mappings
Supports DualSense (PS5), DualShock 4 (PS4), Xbox (360/One/Series), Nintendo Switch,
GP2040-CE (Multi-mode), Android AOSP Standard, and PC DirectInput (Legacy 0x120).
"""

from typing import Dict, Optional, Tuple
from .constants import (
    BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z,
    BTN_TL, BTN_TR, BTN_TL2, BTN_TR2,
    BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL, BTN_THUMBR, BTN_CAPTURE,
    BTN_DPAD_UP, BTN_DPAD_DOWN, BTN_DPAD_LEFT, BTN_DPAD_RIGHT,
    BTN_TRIGGER, BTN_THUMB, BTN_THUMB2, BTN_TOP, BTN_TOP2, BTN_PINKIE,
    BTN_BASE, BTN_BASE2, BTN_BASE3, BTN_BASE4, BTN_BASE5, BTN_BASE6,
    KEY_BACK, KEY_HOMEPAGE,
    ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RY, ABS_RZ,
    ABS_HAT0X, ABS_HAT0Y, ABS_BRAKE, ABS_GAS
)


# Standard labels per layout profile
PROFILES: Dict[str, Dict] = {
    "dualsense": {
        "name": "Sony PlayStation (DualSense / DS4)",
        "buttons": {
            BTN_SOUTH:  ("Cross (✕)", "Action Bottom"),
            BTN_EAST:   ("Circle (◯)", "Action Right"),
            BTN_NORTH:  ("Square (□)", "Action Left"),
            BTN_WEST:   ("Triangle (△)", "Action Top"),
            BTN_TL:     ("L1", "Left Bumper"),
            BTN_TR:     ("R1", "Right Bumper"),
            BTN_TL2:    ("L2 (Digital)", "Left Trigger Click"),
            BTN_TR2:    ("R2 (Digital)", "Right Trigger Click"),
            BTN_SELECT: ("Create / Share", "Select"),
            BTN_START:  ("Options", "Start"),
            BTN_MODE:   ("PS Button", "Home"),
            BTN_THUMBL: ("L3", "Left Stick Click"),
            BTN_THUMBR: ("R3", "Right Stick Click"),
            BTN_DPAD_UP:    ("D-Pad Up", "Up"),
            BTN_DPAD_DOWN:  ("D-Pad Down", "Down"),
            BTN_DPAD_LEFT:  ("D-Pad Left", "Left"),
            BTN_DPAD_RIGHT: ("D-Pad Right", "Right"),
        },
        "axes": {
            ABS_X:  "Left Stick X",
            ABS_Y:  "Left Stick Y",
            ABS_RX: "Right Stick X",
            ABS_RY: "Right Stick Y",
            ABS_Z:  "L2 Trigger (Analog)",
            ABS_RZ: "R2 Trigger (Analog)",
            ABS_HAT0X: "D-Pad X (Hat)",
            ABS_HAT0Y: "D-Pad Y (Hat)",
        }
    },
    "xbox": {
        "name": "Microsoft Xbox (XInput / Series / One / 360)",
        "buttons": {
            BTN_SOUTH:  ("A", "Action Bottom (Green)"),
            BTN_EAST:   ("B", "Action Right (Red)"),
            BTN_NORTH:  ("X", "Action Left (Blue)"),
            BTN_WEST:   ("Y", "Action Top (Yellow)"),
            BTN_TL:     ("LB", "Left Bumper"),
            BTN_TR:     ("RB", "Right Bumper"),
            BTN_TL2:    ("LT (Digital)", "Left Trigger Click"),
            BTN_TR2:    ("RT (Digital)", "Right Trigger Click"),
            BTN_SELECT: ("Back / View", "Select"),
            BTN_START:  ("Start / Menu", "Start"),
            BTN_MODE:   ("Xbox Guide", "Home"),
            BTN_THUMBL: ("LS Click", "Left Stick Click"),
            BTN_THUMBR: ("RS Click", "Right Stick Click"),
            BTN_DPAD_UP:    ("D-Pad Up", "Up"),
            BTN_DPAD_DOWN:  ("D-Pad Down", "Down"),
            BTN_DPAD_LEFT:  ("D-Pad Left", "Left"),
            BTN_DPAD_RIGHT: ("D-Pad Right", "Right"),
        },
        "axes": {
            ABS_X:  "Left Stick X",
            ABS_Y:  "Left Stick Y",
            ABS_RX: "Right Stick X",
            ABS_RY: "Right Stick Y",
            ABS_Z:  "LT Trigger (Analog)",
            ABS_RZ: "RT Trigger (Analog)",
            ABS_HAT0X: "D-Pad X (Hat)",
            ABS_HAT0Y: "D-Pad Y (Hat)",
        }
    },
    "gp2040": {
        "name": "GP2040-CE Arcade / Fightstick Controller",
        "buttons": {
            BTN_SOUTH:   ("1K (Cross / B)", "Bottom-1 (Light Kick)"),
            BTN_EAST:    ("2K (Circle / A)", "Bottom-2 (Medium Kick)"),
            BTN_C:       ("3K (R2 / ZR)", "Bottom-3 (Heavy Kick)"),
            BTN_NORTH:   ("1P (Square / Y)", "Top-1 (Light Punch)"),
            BTN_WEST:    ("2P (Triangle / X)", "Top-2 (Medium Punch)"),
            BTN_Z:       ("3P (R1 / R)", "Top-3 (Heavy Punch)"),
            BTN_TL:      ("4P (L1 / L)", "Top-4 (Punch 4 / LB)"),
            BTN_TR:      ("4K (L2 / ZL)", "Bottom-4 (Kick 4 / LT)"),
            BTN_TL2:     ("Select / Coin", "Coin / Back"),
            BTN_TR2:     ("Start", "Start"),
            BTN_SELECT:  ("Select / Coin", "Coin / Back"),
            BTN_START:   ("Start", "Start"),
            BTN_MODE:    ("Home / Guide", "Guide / Home"),
            BTN_THUMBL:  ("L3 (LS)", "Left Stick Click"),
            BTN_THUMBR:  ("R3 (RS)", "Right Stick Click"),
            BTN_CAPTURE: ("Capture", "Capture / Screenshot"),
            BTN_DPAD_UP:    ("Up / Jump", "Direction Up"),
            BTN_DPAD_DOWN:  ("Down / Crouch", "Direction Down"),
            BTN_DPAD_LEFT:  ("Left", "Direction Left"),
            BTN_DPAD_RIGHT: ("Right", "Direction Right"),
        },
        "axes": {
            ABS_X:     "Stick X",
            ABS_Y:     "Stick Y",
            ABS_Z:     "Right Stick X",
            ABS_RZ:    "Right Stick Y",
            ABS_RX:    "Right Stick X",
            ABS_RY:    "Right Stick Y",
            ABS_HAT0X: "D-Pad X (Hat)",
            ABS_HAT0Y: "D-Pad Y (Hat)",
        }
    },
    "switch": {
        "name": "Nintendo Switch (HORI / Pokken / GP2040-CE)",
        "buttons": {
            BTN_SOUTH:   ("Y / 1P", "Action Left (Y)"),
            BTN_EAST:    ("B / 1K", "Action Bottom (B)"),
            BTN_C:       ("A / 2K", "Action Right (A)"),
            BTN_NORTH:   ("X / 2P", "Action Top (X)"),
            BTN_WEST:    ("L / 4P", "Left Bumper (L)"),
            BTN_Z:       ("R / 3P", "Right Bumper (R)"),
            BTN_TL:      ("ZL / 4K", "Left Trigger (ZL)"),
            BTN_TR:      ("ZR / 3K", "Right Trigger (ZR)"),
            BTN_TL2:     ("Minus (-)", "Select / Minus"),
            BTN_TR2:     ("Plus (+)", "Start / Plus"),
            BTN_SELECT:  ("L3 (LS)", "Left Stick Click"),
            BTN_START:   ("R3 (RS)", "Right Stick Click"),
            BTN_MODE:    ("Home", "Home / Guide"),
            BTN_THUMBL:  ("Capture", "Capture / Screenshot"),
            BTN_THUMBR:  ("Extra", "Extra Button"),
            BTN_CAPTURE: ("Capture", "Capture / Screenshot"),
            BTN_DPAD_UP:    ("D-Pad Up", "Up"),
            BTN_DPAD_DOWN:  ("D-Pad Down", "Down"),
            BTN_DPAD_LEFT:  ("D-Pad Left", "Left"),
            BTN_DPAD_RIGHT: ("D-Pad Right", "Right"),
        },
        "axes": {
            ABS_X:     "Left Stick X",
            ABS_Y:     "Left Stick Y",
            ABS_Z:     "Right Stick X",
            ABS_RZ:    "Right Stick Y",
            ABS_RX:    "Right Stick X",
            ABS_RY:    "Right Stick Y",
            ABS_HAT0X: "D-Pad X (Hat)",
            ABS_HAT0Y: "D-Pad Y (Hat)",
        }
    },
    "switch_pro": {
        "name": "Nintendo Switch (Official Pro Controller - hid-nintendo)",
        "buttons": {
            BTN_SOUTH:   ("B", "Action Bottom (B)"),
            BTN_EAST:    ("A", "Action Right (A)"),
            BTN_NORTH:   ("X", "Action Top (X)"),
            BTN_WEST:    ("Y", "Action Left (Y)"),
            BTN_TL:      ("L", "Left Bumper (L)"),
            BTN_TR:      ("R", "Right Bumper (R)"),
            BTN_TL2:     ("ZL", "Left Trigger (ZL)"),
            BTN_TR2:     ("ZR", "Right Trigger (ZR)"),
            BTN_SELECT:  ("Minus (-)", "Select / Minus"),
            BTN_START:   ("Plus (+)", "Start / Plus"),
            BTN_MODE:    ("Home", "Home / Guide"),
            BTN_THUMBL:  ("LS Click", "Left Stick Click"),
            BTN_THUMBR:  ("RS Click", "Right Stick Click"),
            BTN_CAPTURE: ("Capture", "Capture / Screenshot"),
            BTN_DPAD_UP:    ("D-Pad Up", "Up"),
            BTN_DPAD_DOWN:  ("D-Pad Down", "Down"),
            BTN_DPAD_LEFT:  ("D-Pad Left", "Left"),
            BTN_DPAD_RIGHT: ("D-Pad Right", "Right"),
        },
        "axes": {
            ABS_X:     "Left Stick X",
            ABS_Y:     "Left Stick Y",
            ABS_RX:    "Right Stick X",
            ABS_RY:    "Right Stick Y",
            ABS_HAT0X: "D-Pad X (Hat)",
            ABS_HAT0Y: "D-Pad Y (Hat)",
        }
    },
    "android": {
        "name": "Android HID (AOSP Layout)",
        "buttons": {
            BTN_SOUTH:  ("BUTTON_A", "Bottom (Confirm)"),
            BTN_EAST:   ("BUTTON_B", "Right (Cancel)"),
            BTN_NORTH:  ("BUTTON_X", "Left"),
            BTN_WEST:   ("BUTTON_Y", "Top"),
            BTN_TL:     ("BUTTON_L1", "Left Shoulder"),
            BTN_TR:     ("BUTTON_R1", "Right Shoulder"),
            BTN_TL2:    ("BUTTON_L2", "Left Trigger (Digital)"),
            BTN_TR2:    ("BUTTON_R2", "Right Trigger (Digital)"),
            BTN_SELECT: ("BUTTON_SELECT", "Select"),
            BTN_START:  ("BUTTON_START", "Start"),
            BTN_MODE:   ("BUTTON_MODE", "System Home"),
            KEY_BACK:   ("KEYCODE_BACK", "Android Back"),
            KEY_HOMEPAGE: ("KEYCODE_HOME", "Android Home"),
            BTN_THUMBL: ("BUTTON_THUMBL", "Left Thumb"),
            BTN_THUMBR: ("BUTTON_THUMBR", "Right Thumb"),
        },
        "axes": {
            ABS_X:     "AXIS_X (Left Stick X)",
            ABS_Y:     "AXIS_Y (Left Stick Y)",
            ABS_Z:     "AXIS_Z (Right Stick X)",
            ABS_RZ:    "AXIS_RZ (Right Stick Y)",
            ABS_BRAKE: "AXIS_BRAKE (L2 Trigger)",
            ABS_GAS:   "AXIS_GAS (R2 Trigger)",
            ABS_HAT0X: "AXIS_HAT_X (D-Pad X)",
            ABS_HAT0Y: "AXIS_HAT_Y (D-Pad Y)",
        }
    },
    "dinput_pc": {
        "name": "PC DirectInput (Legacy 0x120 Layout)",
        "buttons": {
            BTN_TRIGGER: ("Button 1", "Trigger / Top-Left"),
            BTN_THUMB:   ("Button 2", "Thumb / Top-Right"),
            BTN_THUMB2:  ("Button 3", "Thumb 2 / Bottom-Left"),
            BTN_TOP:     ("Button 4", "Top / Bottom-Right"),
            BTN_TOP2:    ("Button 5", "Top 2 / L1"),
            BTN_PINKIE:  ("Button 6", "Pinkie / R1"),
            BTN_BASE:    ("Button 7", "Base 1 / L2"),
            BTN_BASE2:   ("Button 8", "Base 2 / R2"),
            BTN_BASE3:   ("Button 9", "Base 3 / Select"),
            BTN_BASE4:   ("Button 10", "Base 4 / Start"),
            BTN_BASE5:   ("Button 11", "Base 5 / L3"),
            BTN_BASE6:   ("Button 12", "Base 6 / R3"),
        },
        "axes": {
            ABS_X:  "X Axis",
            ABS_Y:  "Y Axis",
            ABS_Z:  "Z Axis (Throttle / Combined LT-RT)",
            ABS_RX: "X Rotation (Right Stick X)",
            ABS_RY: "Y Rotation (Right Stick Y)",
            ABS_RZ: "Z Rotation (Right Stick / Rudder)",
            ABS_HAT0X: "Point of View Hat X",
            ABS_HAT0Y: "Point of View Hat Y",
        }
    }
}


def detect_layout_flavor(name: str, key_bits: set, abs_bits: set) -> str:
    """
    Heuristically determines whether the device is using:
    - DualSense (PS5) / DS4
    - GP2040-CE
    - Xbox (XInput)
    - Nintendo Switch
    - Android AOSP HID
    - PC DirectInput (Legacy 0x120)
    """
    lower_name = name.lower()

    if "dualsense" in lower_name or "ps5" in lower_name:
        return "dualsense"
    if "sony" in lower_name or "dualshock" in lower_name or "wireless controller" in lower_name:
        return "dualsense"
    if "gp2040" in lower_name or "rp2040" in lower_name or "pico" in lower_name:
        return "gp2040"
    if "switch" in lower_name or "pokken" in lower_name or "hori" in lower_name:
        if BTN_C in key_bits or "pokken" in lower_name or "hori" in lower_name:
            return "switch"
        return "switch_pro"
    if "xbox" in lower_name or "x-box" in lower_name or "microsoft" in lower_name or "xinput" in lower_name:
        return "xbox"

    # Capability heuristics:
    has_android_nav = (KEY_BACK in key_bits or KEY_HOMEPAGE in key_bits)
    has_brake_gas = (ABS_BRAKE in abs_bits and ABS_GAS in abs_bits)
    has_dinput_btns = (BTN_TRIGGER in key_bits and BTN_THUMB in key_bits)
    has_gamepad_btns = (BTN_SOUTH in key_bits or BTN_EAST in key_bits)

    if has_android_nav or (has_brake_gas and has_gamepad_btns):
        return "android"
    if has_dinput_btns and not has_gamepad_btns:
        return "dinput_pc"
    if has_gamepad_btns:
        return "xbox"

    return "xbox"


def get_button_info(profile_key: str, code: int) -> Tuple[str, str]:
    """Returns (Label, Description) for a button code in the given profile."""
    profile = PROFILES.get(profile_key, PROFILES["xbox"])
    if code in profile["buttons"]:
        return profile["buttons"][code]

    # Check fallback across other profiles
    for pk, prof in PROFILES.items():
        if code in prof["buttons"]:
            lbl, desc = prof["buttons"][code]
            return f"{lbl} (?)", desc

    return f"Btn 0x{code:03X} ({code})", "Unknown button"


def get_axis_info(profile_key: str, code: int) -> str:
    """Returns axis name for the given profile."""
    profile = PROFILES.get(profile_key, PROFILES["xbox"])
    if code in profile.get("axes", {}):
        return profile["axes"][code]
    return f"Axis 0x{code:02X} ({code})"


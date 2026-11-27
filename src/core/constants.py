"""
Gamepad Tester Core Constants
Linux input subsystem key and axis codes, ioctl requests, and struct definitions.
"""

# Linux Input Event Types
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04
EV_SW  = 0x05
EV_LED = 0x11
EV_SND = 0x12
EV_REP = 0x14
EV_FF  = 0x15
EV_PWR = 0x16
EV_FF_STATUS = 0x17

# Common Linux Absolute Axes
ABS_X          = 0x00
ABS_Y          = 0x01
ABS_Z          = 0x02
ABS_RX         = 0x03
ABS_RY         = 0x04
ABS_RZ         = 0x05
ABS_THROTTLE   = 0x06
ABS_RUDDER     = 0x07
ABS_WHEEL      = 0x08
ABS_GAS        = 0x09
ABS_BRAKE      = 0x0A
ABS_HAT0X      = 0x10
ABS_HAT0Y      = 0x11
ABS_HAT1X      = 0x12
ABS_HAT1Y      = 0x13

# Linux Multitouch (Touchpad) Axes
ABS_MT_SLOT        = 0x2F
ABS_MT_TOUCH_MAJOR = 0x30
ABS_MT_POSITION_X  = 0x35
ABS_MT_POSITION_Y  = 0x36
ABS_MT_TRACKING_ID = 0x39

# Touchpad & Mouse Click / Touch Keys
BTN_LEFT           = 0x110
BTN_TOOL_FINGER    = 0x145
BTN_TOUCH          = 0x14A
BTN_TOOL_DOUBLETAP = 0x14D

# Misc Event Codes
MSC_TIMESTAMP      = 0x05

# Linux Key / Button Codes
# BTN_MISC / Classic Joystick (DirectInput 0x120-0x12F)
BTN_JOYSTICK   = 0x120
BTN_TRIGGER    = 0x120
BTN_THUMB      = 0x121
BTN_THUMB2     = 0x122
BTN_TOP        = 0x123
BTN_TOP2       = 0x124
BTN_PINKIE     = 0x125
BTN_BASE       = 0x126
BTN_BASE2      = 0x127
BTN_BASE3      = 0x128
BTN_BASE4      = 0x129
BTN_BASE5      = 0x12A
BTN_BASE6      = 0x12B
BTN_DEAD       = 0x12F

# BTN_GAMEPAD (Modern Gamepad / AOSP 0x130-0x13F)
BTN_GAMEPAD    = 0x130
BTN_SOUTH      = 0x130  # A / Cross
BTN_A          = 0x130
BTN_EAST       = 0x131  # B / Circle
BTN_B          = 0x131
BTN_C          = 0x132
BTN_NORTH      = 0x133  # X / Square
BTN_X          = 0x133
BTN_WEST       = 0x134  # Y / Triangle
BTN_Y          = 0x134
BTN_Z          = 0x135
BTN_TL         = 0x136  # L1 / LB
BTN_TR         = 0x137  # R1 / RB
BTN_TL2        = 0x138  # L2 (Digital)
BTN_TR2        = 0x139  # R2 (Digital)
BTN_SELECT     = 0x13A  # Select / Share / Back / View
BTN_START      = 0x13B  # Start / Options / Menu
BTN_MODE       = 0x13C  # PS / Xbox / Home / Guide
BTN_THUMBL     = 0x13D  # L3 (Left stick click)
BTN_THUMBR     = 0x13E  # R3 (Right stick click)
BTN_CAPTURE    = 0x13F  # Switch Capture / Share

# D-Pad discrete buttons
BTN_DPAD_UP    = 0x220
BTN_DPAD_DOWN  = 0x221
BTN_DPAD_LEFT  = 0x222
BTN_DPAD_RIGHT = 0x223

# System & Media Keys (common in Android / Multimedia controllers)
KEY_BACK       = 158
KEY_HOMEPAGE   = 172
KEY_VOLUMEUP   = 115
KEY_VOLUMEDOWN = 114
KEY_MUTE       = 113
KEY_PLAYPAUSE  = 164

# Force Feedback Constants
FF_RUMBLE      = 0x50
FF_PERIODIC    = 0x51
FF_CONSTANT    = 0x52
FF_SPRING      = 0x53
FF_FRICTION    = 0x54
FF_DAMPER      = 0x55
FF_INERTIA     = 0x56
FF_RAMP        = 0x57

# 64-bit Linux ioctl request codes
EVIOCGBIT_EV   = 2 << 30 | 4 << 16 | ord('E') << 8 | 0x20
EVIOCGBIT_KEY  = 2 << 30 | 64 << 16 | ord('E') << 8 | (0x20 + EV_KEY)
EVIOCGBIT_ABS  = 2 << 30 | 8 << 16 | ord('E') << 8 | (0x20 + EV_ABS)
EVIOCGBIT_FF   = 2 << 30 | 16 << 16 | ord('E') << 8 | (0x20 + EV_FF)
EVIOCGNAME     = 2 << 30 | 256 << 16 | ord('E') << 8 | 0x06
EVIOCGID       = 2 << 30 | 8 << 16 | ord('E') << 8 | 0x02
EVIOCSFF       = 1 << 30 | 48 << 16 | ord('E') << 8 | 0x80
HIDIOCGRAWNAME = 2 << 30 | 256 << 16 | ord('H') << 8 | 0x04


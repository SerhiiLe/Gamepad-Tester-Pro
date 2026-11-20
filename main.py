#!/usr/bin/env python3
"""
Gamepad Tester Pro — Diagnostic & Calibration Suite
Entrypoint for launching GUI or CLI diagnostic modes.
"""

import sys
import os
import argparse

# Add src to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.discovery import discover_gamepads
from src.reports.text_report import generate_text_report


def run_cli_diagnostic():
    """Runs a quick CLI diagnostic scan and prints connected controller details."""
    print("=" * 70)
    print("        GAMEPAD TESTER PRO — ДИАГНОСТИЧЕСКАЯ УТИЛИТА (CLI)")
    print("=" * 70)

    devices = discover_gamepads()
    if not devices:
        print("\n[!] Контроллеры не обнаружены!")
        print("    Убедитесь, что геймпад подключен по USB или Bluetooth и распознан Linux.")
        return

    print(f"\nОбнаружено устройств: {len(devices)}")
    for i, dev in enumerate(devices, 1):
        vid_pid = f"VID:0x{dev.vendor_id:04X} PID:0x{dev.product_id:04X}"
        flavor = f"[{dev.layout_flavor.upper()}]"
        print(f"  [{i}] {flavor} {dev.name} ({vid_pid})")
        print(f"      Node: {dev.event_path or 'N/A'}, HID: {dev.hidraw_path or 'N/A'}")
        cap, stat = dev.get_battery_info()
        if cap is not None:
            print(f"      Батарея: {cap}% ({stat})")


def run_gui():
    """Launches the PySide6 Graphical User Interface."""
    from PySide6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow

    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("Gamepad Tester Pro")
    app.setOrganizationName("GamepadTester")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser(description="Gamepad Tester Pro — Diagnostic & Calibration Suite")
    parser.add_argument("--cli", action="store_true", help="Запустить в режиме командной строки (без GUI)")
    parser.add_argument("--list", action="store_true", help="Вывести список найденных геймпадов и выйти")
    args = parser.parse_args()

    if args.list:
        run_cli_diagnostic()
        return

    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    if args.cli or not has_display:
        run_cli_diagnostic()
    else:
        run_gui()


if __name__ == "__main__":
    main()


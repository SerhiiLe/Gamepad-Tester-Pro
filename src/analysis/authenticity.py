"""
Hardware Authenticity and Platform Implementation Analysis Module
Analyzes physical controller architecture against reference platform specifications:
- Aggregates average stick ADC resolution (e.g. 10-bit, 12-bit)
- Aggregates average trigger ADC resolution (e.g. 8-bit, 10-bit)
- Verifies platform completeness (Touchpad, 6-axis IMU, Force Feedback, Lightbar)
- Detects replicas / imitations (e.g., clone DualShock 4 claiming to be Sony but missing touchpad & gyro)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from ..i18n import i18n
except Exception:
    i18n = None


@dataclass
class AuthenticityResult:
    avg_stick_adc_bits: float
    stick_adc_str: str
    avg_trigger_adc_bits: float
    trigger_adc_str: str
    archetype: str
    expected_spec: str
    actual_spec: str
    verdict: str
    comment: str
    is_replica: bool


def analyze_authenticity(device_info: Dict[str, Any],
                         left_stick: Dict[str, Any],
                         right_stick: Dict[str, Any],
                         triggers_data: Dict[str, Any],
                         lang: Optional[str] = None) -> AuthenticityResult:
    """
    Evaluates hardware completeness, average ADC bitness, and authenticity verdict.
    Supports English ('EN') and Russian ('RU') output based on parameter or active i18n locale.
    """
    if lang is None and i18n is not None:
        lang = i18n.current_lang
    is_en = (str(lang).upper() == "EN")

    # 1. Aggregate Stick ADC Resolution
    ls_bits = left_stick.get('adc_bits', 0)
    rs_bits = right_stick.get('adc_bits', 0)
    stick_bits_list = [b for b in (ls_bits, rs_bits) if b > 0]
    if stick_bits_list:
        avg_stick = round(sum(stick_bits_list) / len(stick_bits_list))
        if is_en:
            stick_adc_str = f"~{avg_stick}-bit ({2**avg_stick} quantization steps)"
        else:
            stick_adc_str = f"~{avg_stick} бит ({2**avg_stick} уровней квантования)"
    else:
        avg_stick = 0
        if is_en:
            stick_adc_str = "not measured (rotate sticks in 'Free Run' mode)"
        else:
            stick_adc_str = "не замерена (вращайте стики в 'Свободном' режиме)"

    # 2. Aggregate Trigger ADC Resolution
    trig_bits_list = [t.get('adc_bits', 0) for t in triggers_data.values() if t.get('adc_bits', 0) > 0]
    if trig_bits_list:
        avg_trig = round(sum(trig_bits_list) / len(trig_bits_list))
        if is_en:
            trigger_adc_str = f"~{avg_trig}-bit ({2**avg_trig} quantization steps)"
        else:
            trigger_adc_str = f"~{avg_trig} бит ({2**avg_trig} уровней квантования)"
    else:
        avg_trig = 0
        if is_en:
            trigger_adc_str = "digital or not measured"
        else:
            trigger_adc_str = "цифровые или не замерена"

    vid = device_info.get('vid', 0)
    pid = device_info.get('pid', 0)
    name = device_info.get('name', 'Unknown')
    layout = str(device_info.get('layout', 'standard')).lower()
    has_touchpad = device_info.get('has_touchpad', False)
    has_motion = device_info.get('has_motion', False)
    has_ff = device_info.get('has_ff', False)

    name_l = name.lower()

    # Case A: Sony DualShock 4
    if (vid == 0x054C and pid in (0x05C4, 0x09CC)) or "dualshock" in name_l or ("wireless controller" in name_l and layout == "ds4") or ("sony" in name_l and "ds4" in layout):
        archetype = "Sony DualShock 4 (PlayStation 4)"
        if is_en:
            expected_spec = "Touchpad, 6-axis IMU gyro/accelerometer, RGB Lightbar, ERM rumble, stick ADC 10–12 bit"
            actual_items = [
                f"Touchpad: {'Detected' if has_touchpad else 'ABSENT'}",
                f"Gyroscope/IMU: {'Detected' if has_motion else 'ABSENT'}",
                f"Force Feedback: {'Supported' if has_ff else 'ABSENT'}",
                f"Stick ADC: {stick_adc_str}",
                f"Trigger ADC: {trigger_adc_str}"
            ]
        else:
            expected_spec = "Сенсорная панель (Touchpad), 6-осевой гироскоп/акселерометр (IMU), RGB Lightbar, виброотдача ERM, АЦП стиков 10–12 бит"
            actual_items = [
                f"Тачпад: {'Обнаружен' if has_touchpad else 'ОТСУТСТВУЕТ'}",
                f"Гироскоп/IMU: {'Обнаружен' if has_motion else 'ОТСУТСТВУЕТ'}",
                f"Виброотдача: {'Поддерживается' if has_ff else 'ОТСУТСТВУЕТ'}",
                f"АЦП стиков: {stick_adc_str}",
                f"АЦП курков: {trigger_adc_str}"
            ]
        actual_spec = "; ".join(actual_items)
        if has_touchpad and has_motion:
            verdict = "Genuine / Full Sony DS4 Hardware Implementation" if is_en else "Оригинал / Полная аппаратная реализация Sony DS4"
            comment = ("All official platform modules (touchpad, gyro, vibration) are present and initialized by the system driver."
                       if is_en else "Все фирменные узлы платформы (тачпад, гироскоп, виброотдача) присутствуют и инициализированы системным драйвером.")
            is_replica = False
        else:
            missing = []
            if not has_touchpad:
                missing.append("touchpad" if is_en else "сенсорная панель (Touchpad)")
            if not has_motion:
                missing.append("6-axis gyro (Motion Sensors)" if is_en else "6-осевой гироскоп (Motion Sensors)")
            verdict = "Imitation / Replica (Incomplete DS4 Platform Implementation)" if is_en else "Имитация / Реплика (Неполная реализация платформы DS4)"
            comment = (f"Device identifies as DualShock 4, but hardware only implements basic gamepad. Missing: {', '.join(missing)}."
                       if is_en else f"Устройство заявляет себя как DualShock 4, но аппаратно реализован лишь базовый геймпад. Отсутствуют: {', '.join(missing)}.")
            is_replica = True

    # Case B: Sony DualSense (PS5)
    elif (vid == 0x054C and pid in (0x0CE6, 0x0DF2)) or "dualsense" in name_l:
        archetype = "Sony DualSense (PlayStation 5)"
        if is_en:
            expected_spec = "Multitouch Touchpad, 6-axis IMU gyro/accelerometer, Haptic Feedback, RGB Lightbar, 12-bit ADC"
            actual_items = [
                f"Touchpad: {'Detected' if has_touchpad else 'ABSENT'}",
                f"Gyroscope/IMU: {'Detected' if has_motion else 'ABSENT'}",
                f"Force Feedback: {'Supported' if has_ff else 'ABSENT'}",
                f"Stick ADC: {stick_adc_str}"
            ]
        else:
            expected_spec = "Сенсорная панель Multitouch, 6-осевой IMU гироскоп/акселерометр, тактильные приводы Haptic Feedback, RGB Lightbar, АЦП 12 бит"
            actual_items = [
                f"Тачпад: {'Обнаружен' if has_touchpad else 'ОТСУТСТВУЕТ'}",
                f"Гироскоп/IMU: {'Обнаружен' if has_motion else 'ОТСУТСТВУЕТ'}",
                f"Виброотдача: {'Поддерживается' if has_ff else 'ОТСУТСТВУЕТ'}",
                f"АЦП стиков: {stick_adc_str}"
            ]
        actual_spec = "; ".join(actual_items)
        if has_touchpad and has_motion:
            verdict = "Genuine / Full Sony DualSense Implementation" if is_en else "Оригинал / Полная аппаратная реализация Sony DualSense"
            comment = ("All official DualSense subsystems are detected and active."
                       if is_en else "Все фирменные подсистемы DualSense обнаружены и активны.")
            is_replica = False
        else:
            missing = []
            if not has_touchpad:
                missing.append("touchpad" if is_en else "сенсорная панель (Touchpad)")
            if not has_motion:
                missing.append("motion sensors" if is_en else "датчики движения (Motion Sensors)")
            verdict = "Imitation / Replica (Incomplete DualSense Implementation)" if is_en else "Имитация / Реплика (Неполная реализация DualSense)"
            comment = (f"Device imitates DualSense, but sensor subsystems are missing ({', '.join(missing)})."
                       if is_en else f"Устройство имитирует DualSense, но сенсорные подсистемы отсутствуют ({', '.join(missing)}).")
            is_replica = True

    # Case C: Microsoft Xbox 360 / Xbox One / Series
    elif vid == 0x045E or "xbox" in name_l or "x-box" in name_l:
        is_x360 = (pid in (0x028E, 0x028F) or "360" in name_l)
        if is_x360:
            archetype = "Microsoft Xbox 360 Controller (XInput)"
            if is_en:
                expected_spec = "Microsoft XInput protocol, Force Feedback Rumble, analog triggers (8-10 bit), stick ADC 10–12 bit"
            else:
                expected_spec = "Протокол Microsoft XInput, Force Feedback Rumble, аналоговые курки (8-10 бит), АЦП стиков 10–12 бит"
        else:
            archetype = "Microsoft Xbox One / Series X|S (XInput)"
            if is_en:
                expected_spec = "Microsoft XInput / GIP protocol, 4 rumble motors (including Impulse Triggers), 10-bit analog triggers, 12-bit ADC"
            else:
                expected_spec = "Протокол Microsoft XInput / GIP, 4 вибромотора (включая Impulse Triggers), аналоговые курки 10 бит, АЦП 12 бит"

        if is_en:
            actual_items = [
                f"Protocol: {'Genuine Microsoft (0x045E)' if vid == 0x045E else f'Compatible XInput (VID: 0x{vid:04X})'}",
                f"Rumble Motors: {'Supported (Force Feedback)' if has_ff else 'ABSENT'}",
                f"Stick ADC: {stick_adc_str}",
                f"Trigger ADC: {trigger_adc_str}"
            ]
        else:
            actual_items = [
                f"Протокол: {'Оригинальный Microsoft (0x045E)' if vid == 0x045E else f'Совместимый XInput (VID: 0x{vid:04X})'}",
                f"Вибромоторы: {'Поддерживаются (Force Feedback)' if has_ff else 'ОТСУТСТВУЮТ'}",
                f"АЦП стиков: {stick_adc_str}",
                f"АЦП курков: {trigger_adc_str}"
            ]
        actual_spec = "; ".join(actual_items)
        if vid == 0x045E and has_ff:
            verdict = "Genuine Xbox Hardware Architecture" if is_en else "Оригинальная аппаратная архитектура Xbox"
            comment = ("Device fully complies with reference Microsoft Xbox controller specifications."
                       if is_en else "Устройство полностью соответствует эталонной спецификации контроллеров Microsoft Xbox.")
            is_replica = False
        else:
            verdict = "Compatible Replica / Xbox Clone" if is_en else "Совместимая реплика / аналог Xbox"
            comment = ("Device operates via compatible protocol, but differs from genuine Microsoft platform."
                       if is_en else "Устройство функционирует через совместимый протокол, но имеет отличия от оригинальной платформы Microsoft.")
            is_replica = (vid != 0x045E or not has_ff)

    # Case D: Nintendo Switch Pro
    elif vid == 0x057E or "switch" in name_l:
        archetype = "Nintendo Switch Pro Controller"
        if is_en:
            expected_spec = "6-axis IMU gyro/accelerometer, HD Rumble (LRA), NFC, digital triggers ZL/ZR"
            actual_items = [
                f"Gyroscope/IMU: {'Detected' if has_motion else 'ABSENT'}",
                f"Force Feedback: {'Supported' if has_ff else 'ABSENT'}",
                f"Stick ADC: {stick_adc_str}"
            ]
        else:
            expected_spec = "6-осевой гироскоп/акселерометр IMU, виброприводы HD Rumble (LRA), NFC, цифровые курки ZL/ZR"
            actual_items = [
                f"Гироскоп/IMU: {'Обнаружен' if has_motion else 'ОТСУТСТВУЕТ'}",
                f"Виброотдача: {'Поддерживается' if has_ff else 'ОТСУТСТВУЕТ'}",
                f"АЦП стиков: {stick_adc_str}"
            ]
        actual_spec = "; ".join(actual_items)
        if has_motion:
            verdict = "Genuine / Full Nintendo Switch Pro Implementation" if is_en else "Оригинал / Полная реализация Nintendo Switch Pro"
            comment = ("Motion IMU sensors and Switch Pro protocol are active."
                       if is_en else "Датчики движения IMU и протокол Switch Pro активны.")
            is_replica = False
        else:
            verdict = "Imitation / Switch Pro Replica" if is_en else "Имитация / Реплика Switch Pro"
            comment = ("Official Nintendo Switch platform IMU motion sensors are absent."
                       if is_en else "Отсутствуют фирменные датчики движения IMU платформы Nintendo Switch.")
            is_replica = True

    # Case E: Generic / Universal Gamepad
    else:
        if is_en:
            archetype = "Universal Standard Controller (DInput / Generic HID)"
            expected_spec = "Standard control set (D-Pad, buttons, bumpers), analog sticks (8–12 bit)"
            actual_spec = f"Stick ADC: {stick_adc_str}; Triggers: {trigger_adc_str}; Force Feedback: {'Supported' if has_ff else 'ABSENT'}"
            verdict = "Standard Gamepad Implementation"
            comment = "Operates as a standard general-purpose game controller without platform-specific extensions."
        else:
            archetype = "Универсальный стандартный контроллер (DInput / Generic HID)"
            expected_spec = "Базовый набор органов управления (D-Pad, кнопки, бамперы), аналоговые стики (8–12 бит)"
            actual_spec = f"АЦП стиков: {stick_adc_str}; Курки: {trigger_adc_str}; Виброотдача: {'Поддерживается' if has_ff else 'ОТСУТСТВУЕТ'}"
            verdict = "Стандартная реализация геймпада"
            comment = "Функционирует как стандартный игровой контроллер общего назначения без платформенных расширений."
        is_replica = False

    return AuthenticityResult(
        avg_stick_adc_bits=float(avg_stick),
        stick_adc_str=stick_adc_str,
        avg_trigger_adc_bits=float(avg_trig),
        trigger_adc_str=trigger_adc_str,
        archetype=archetype,
        expected_spec=expected_spec,
        actual_spec=actual_spec,
        verdict=verdict,
        comment=comment,
        is_replica=is_replica
    )

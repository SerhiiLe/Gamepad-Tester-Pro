"""
Diagnostic Text Report Generator
Generates a structured plain-text report of gamepad health and test findings.
"""

import time
from typing import Dict, Any
from ..analysis.authenticity import analyze_authenticity


def generate_text_report(device_info: Dict[str, Any],
                         polling_data: Dict[str, Any],
                         buttons_data: Dict[str, Any],
                         left_stick: Dict[str, Any],
                         right_stick: Dict[str, Any],
                         triggers_data: Dict[str, Any]) -> str:
    """Generates a complete diagnostic report in human-readable plain text format."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # Authenticity & hardware profile analysis
    auth = analyze_authenticity(device_info, left_stick, right_stick, triggers_data)

    # Global status calculation
    issues = []
    if buttons_data.get("status") != "PASS":
        issues.append(f"Дребезг контактов: обнаружено {buttons_data.get('total_chatter_events', 0)} событий (< 7 мс)")
    if left_stick.get("status") != "PASS":
        issues.extend([f"Левый стик: {iss}" for iss in left_stick.get("issues", [])])
    if right_stick.get("status") != "PASS":
        issues.extend([f"Правый стик: {iss}" for iss in right_stick.get("issues", [])])
    if polling_data.get("status") != "PASS":
        issues.append("Нестабильная частота опроса шины")
    if auth.is_replica:
        issues.append(f"Неполная аппаратная реализация платформы ({auth.verdict})")

    global_verdict = "✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ (НОРМА)" if not issues else "⚠️ ОБНАРУЖЕНЫ ДЕФЕКТЫ / ОТКЛОНЕНИЯ"

    lines = [
        "=" * 70,
        "          ПАСПОРТ ТЕХНИЧЕСКОГО СОСТОЯНИЯ ГЕЙМПАДА",
        "=" * 70,
        f"Дата проверки:       {now_str}",
        f"Устройство:          {device_info.get('name', 'Unknown')}",
        f"Идентификатор:       VID:0x{device_info.get('vid', 0):04X} PID:0x{device_info.get('pid', 0):04X}",
        f"Интерфейс:           {device_info.get('event_path', 'N/A')}",
        f"Определенная схема:  {device_info.get('layout', 'Standard')}",
        "-" * 70,
        f"ИТОГОВОЕ ЗАКЛЮЧЕНИЕ: {global_verdict}",
        "-" * 70,
        "",
        "1. ЧАСТОТА ОПРОСА И СТАБИЛЬНОСТЬ ШИНЫ (POLLING RATE)",
        f"  - Текущая частота:        {polling_data.get('current_hz', 0)} Гц (Номинал: {polling_data.get('nominal_target_hz', 0)} Гц)",
        f"  - Средний интервал dt:    {polling_data.get('avg_interval_ms', 0)} мс",
        f"  - Разброс интервалов:     min: {polling_data.get('min_interval_ms', 0)} мс, max: {polling_data.get('max_interval_ms', 0)} мс",
        f"  - Джиттер шины (StdDev):  {polling_data.get('jitter_stddev_ms', 0)} мс",
        f"  - Пропущенные пакеты:     {polling_data.get('dropped_packets', 0)} из {polling_data.get('total_packets', 0)}",
        "",
        "2. КНОПКИ И ДРЕБЕЗГ КОНТАКТОВ (DEBOUNCE / CHATTER)",
        f"  - Проверено кнопок:       {buttons_data.get('total_buttons_tested', 0)}",
        f"  - Событий дребезга (<7мс):{buttons_data.get('total_chatter_events', 0)}",
    ]

    faulty = buttons_data.get("faulty_buttons", [])
    if faulty:
        lines.append(f"  - ⚠️ Кнопки с дребезгом:   {', '.join(faulty)}")
    else:
        lines.append("  - Статус кнопок:          ОК (ложных срабатываний и дребезга не выявлено)")

    ls_gate = left_stick.get('gate_shape', '')
    ls_bezel_tag = " (без безеля)" if ("без безеля" in ls_gate.lower() or "квадрат" in ls_gate.lower()) else ""

    rs_gate = right_stick.get('gate_shape', '')
    rs_bezel_tag = " (без безеля)" if ("без безеля" in rs_gate.lower() or "квадрат" in rs_gate.lower()) else ""

    lines.extend([
        "",
        "3. ЛЕВЫЙ АНАЛОГОВЫЙ СТИК",
        f"  - Ошибка геометрии:       {left_stick.get('circularity_error_pct', 0):.2f}%{ls_bezel_tag} (допуск < 8.0%)",
        f"  - Максимальный вылет:     {left_stick.get('max_reach', 0):.3f}",
        f"  - Джиттер / Шум:          удержание: {left_stick.get('peak_jitter_pct', 0):.2f}%, в движении: {left_stick.get('motion_jitter_pct', 0):.2f}%",
        f"  - Snapback по оси X:      вероятность: {left_stick.get('snapback_rate_x_pct', 0):.0f}% ({left_stick.get('snapback_flicks_x', 0)} из {left_stick.get('total_flicks_x', 0)}), макс. вылет: {left_stick.get('max_snapback_x_pct', 0):.1f}% (допуск < 5.0%)",
        f"  - Snapback по оси Y:      вероятность: {left_stick.get('snapback_rate_y_pct', 0):.0f}% ({left_stick.get('snapback_flicks_y', 0)} из {left_stick.get('total_flicks_y', 0)}), макс. вылет: {left_stick.get('max_snapback_y_pct', 0):.1f}% (допуск < 5.0%)",
        "",
        "4. ПРАВЫЙ АНАЛОГОВЫЙ СТИК",
        f"  - Ошибка геометрии:       {right_stick.get('circularity_error_pct', 0):.2f}%{rs_bezel_tag} (допуск < 8.0%)",
        f"  - Максимальный вылет:     {right_stick.get('max_reach', 0):.3f}",
        f"  - Джиттер / Шум:          удержание: {right_stick.get('peak_jitter_pct', 0):.2f}%, в движении: {right_stick.get('motion_jitter_pct', 0):.2f}%",
        f"  - Snapback по оси X:      вероятность: {right_stick.get('snapback_rate_x_pct', 0):.0f}% ({right_stick.get('snapback_flicks_x', 0)} из {right_stick.get('total_flicks_x', 0)}), макс. вылет: {right_stick.get('max_snapback_x_pct', 0):.1f}% (допуск < 5.0%)",
        f"  - Snapback по оси Y:      вероятность: {right_stick.get('snapback_rate_y_pct', 0):.0f}% ({right_stick.get('snapback_flicks_y', 0)} из {right_stick.get('total_flicks_y', 0)}), макс. вылет: {right_stick.get('max_snapback_y_pct', 0):.1f}% (допуск < 5.0%)",
        "",
        "5. АНАЛОГОВЫЕ ТРИГГЕРЫ (КУРКИ)",
    ])

    for name, tdata in triggers_data.items():
        lines.append(f"  - {name}: ход 0..{tdata.get('raw_max', 255)} (текущее: {tdata.get('current_val_pct', 0):.1f}%)")

    lines.extend([
        "",
        "6. ПРЕДПОЛАГАЕМЫЕ ХАРАКТЕРИСТИКИ И ПОДЛИННОСТЬ УСТРОЙСТВА",
        f"  - Разрядность АЦП стиков:     {auth.stick_adc_str}",
        f"  - Разрядность АЦП триггеров:  {auth.trigger_adc_str}",
        f"  - Платформенный профиль:      {auth.archetype}",
        f"  - Ожидается по спецификации:  {auth.expected_spec}",
        f"  - Фактически обнаружено:      {auth.actual_spec}",
        f"  - Заключение о подлинности:   {auth.verdict}",
        f"  - Экспертный вывод:           {auth.comment}",
    ])

    if issues:
        lines.extend([
            "",
            "7. ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ И РЕКОМЕНДАЦИИ:",
            *[f"  * {iss}" for iss in issues]
        ])

    lines.append("\n" + "=" * 70 + "\n")
    return "\n".join(lines)


"""
Russian Localization Dictionary for Gamepad Tester Pro
"""

TRANSLATIONS = {
    # -------------------------------------------------------------------------
    # Main Window & Navigation
    # -------------------------------------------------------------------------
    "app_title": "Gamepad Tester Pro — Комплексная диагностика игровых контроллеров",
    "lbl_controller": "<b>Контроллер:</b>",
    "btn_rescan": "↻ Поиск устройств",
    "lbl_layout": "<b>Раскладка:</b>",
    "lbl_battery_charging": "🔋 Батарея: {cap}% (Зарядка)",
    "lbl_battery_discharging": "🔋 Батарея: {cap}% (Разрядка)",
    "lbl_battery_full": "🔋 Батарея: {cap}% (Полный)",
    "lbl_battery_unknown": "🔋 Батарея: —",
    "lbl_power_usb": "🔌 Питание: USB (провод)",
    "no_controllers_found": "Контроллеры не обнаружены",

    # Tabs
    "tab_sticks": "🎯 Стики и курки",
    "tab_buttons": "🔘 Кнопки и дребезг",
    "tab_polling": "⚡ Частота опроса (Hz)",
    "tab_feedback": "📳 Вибрация и подсветка",
    "tab_touchpad_gyro": "🧭 Тачпад и гироскоп",
    "tab_report": "📋 Паспорт / Отчёт",

    # -------------------------------------------------------------------------
    # Sticks & Oscilloscope
    # -------------------------------------------------------------------------
    "stick_left_name": "Левый стик (LS)",
    "stick_right_name": "Правый стик (RS)",
    "stage_free": "Свободный",
    "stage_center": "1: Центр",
    "stage_circle": "2: Окружность",
    "stage_targets": "3: В кружки (Шум)",
    "stage_snapback": "4: Snapback",
    "btn_reset": "Сброс",

    "hint_free": "💡 Свободный ход (замер АЦП)",
    "hint_center": "🎯 Отпустите стик в центр",
    "hint_center_done": "✅ Тест пройден (дрейф: {drift:.1f}%)",
    "hint_circle": "🔄 Опишите полный круг по упору",
    "hint_circle_done": "✅ Тест пройден (ошибка: {circ:.1f}%)",
    "hint_targets": "💡 Удерживайте стик внутри кружка",
    "hint_targets_move": "🎯 Направьте в кружок: {zone}",
    "hint_targets_settling": "⏳ Фиксация: {zone}",
    "hint_targets_measuring": "🎯 Замер: {zone}",
    "hint_targets_done": "✅ Тест пройден (шум: {noise:.2f}%)",
    "hint_snapback_x": "⚡ 1. Отведите по горизонтали и отпустите",
    "hint_snapback_y": "⚡ 2. Отведите по вертикали и отпустите",
    "hint_snapback_done": "✅ Тест пройден (Snapback: X {x_rate}%, Y {y_rate}%)",

    "metric_adc": "АЦП",
    "metric_bit": "бит",
    "metric_step": "шаг",
    "metric_adc_hint": "вращайте стик...",
    "metric_center": "Центр",
    "metric_coverage": "Охват",
    "metric_error": "Ошибка",
    "metric_noise": "Шум",
    "metric_flicks": "Сбросы",
    "metric_peak": "Пик",

    "zone_north": "Север (Вверх)",
    "zone_east": "Восток (Вправо)",
    "zone_south": "Юг (Вниз)",
    "zone_west": "Запад (Влево)",

    "snapback_box_title": "Осциллограмма движения: {title} (~100 мс)",
    "snapback_peak_label": "Пик отскока: <b>{peak:.1f}%</b>",
    "snapback_axis_y": "Коорд.",
    "snapback_axis_x": "Время (~100 мс / точки)",

    # -------------------------------------------------------------------------
    # Anomalies Summary Table
    # -------------------------------------------------------------------------
    "anomalies_box_title": "Сводка аномалий и дефектов стиков (по осям X/Y)",
    "col_param_check": "Параметр проверки",
    "col_ls_left": "LS (Левый)",
    "col_rs_right": "RS (Правый)",
    "col_tolerance": "Допуск",

    "cell_not_tested": "Не тестир.",
    "cell_waiting_tests": "Ожидание тестов",
    "cell_pass": "✅ НОРМА",
    "cell_defect": "⚠️ ДЕФЕКТ",

    # Row definitions (name, tol, tooltip)
    "anom_row0_name": "Дрейф центра (Ось X)",
    "anom_row0_tol": "< 5.0%",
    "anom_row0_tip": "<b>Дрейф нуля по горизонтальной оси X:</b><br>Смещение стика влево/вправо в положении покоя.<br><i>Допуск:</i> менее 5.0%.<br><i>Замеряется в:</i> Этап 1 (Центр).<br><b>Причина:</b> износ резистивного слоя потенциометра X либо сбитая калибровка нуля АЦП.",

    "anom_row1_name": "Дрейф центра (Ось Y)",
    "anom_row1_tol": "< 5.0%",
    "anom_row1_tip": "<b>Дрейф нуля по вертикальной оси Y:</b><br>Смещение стика вверх/вниз в положении покоя.<br><i>Допуск:</i> менее 5.0%.<br><i>Замеряется в:</i> Этап 1 (Центр).<br><b>Причина:</b> износ резистивного слоя потенциометра Y либо сбитая калибровка нуля АЦП.",

    "anom_row2_name": "Ошибка круга (360°)",
    "anom_row2_tol": "< 8.0%",
    "anom_row2_tip": "<b>Ошибка окружности (Circularity Error):</b><br>Отклонение внешней границы хода стика от идеальной окружности (R=1.0).<br><i>Допуск (с безелем):</i> менее 8.0%.<br><i>Для гейта без безеля (квадратного):</i> норма ~18–22%.<br><i>Замеряется в:</i> Этап 2 (Окружность).",

    "anom_row3_name": "Шум потенциометра X",
    "anom_row3_tol": "< 1.50%",
    "anom_row3_tip": "<b>Амплитуда шума и дрожания по оси X:</b><br>Флуктуации сигнала датчика Холла или износ резистивной дорожки X при удержании стика.<br><i>Допуск:</i> менее 1.50%.<br><i>Замеряется в:</i> Этап 3 (Попадите в кружки).",

    "anom_row4_name": "Шум потенциометра Y",
    "anom_row4_tol": "< 1.50%",
    "anom_row4_tip": "<b>Амплитуда шума и дрожания по оси Y:</b><br>Флуктуации сигнала датчика Холла или износ резистивной дорожки Y при удержании стика.<br><i>Допуск:</i> менее 1.50%.<br><i>Замеряется в:</i> Этап 3 (Попадите в кружки).",

    "anom_row5_name": "Snapback (Ось X)",
    "anom_row5_tol": "< 5.0%",
    "anom_row5_tip": "<b>Амплитуда отскока по горизонтали (Snapback X):</b><br>Пролёт нуля вправо/влево при резком отпускании горизонтального упора.<br><i>Допуск:</i> менее 5.0%.<br><i>Замеряется в:</i> Этап 4 (Snapback).",

    "anom_row6_name": "Snapback (Ось Y)",
    "anom_row6_tol": "< 5.0%",
    "anom_row6_tip": "<b>Амплитуда отскока по вертикали (Snapback Y):</b><br>Пролёт нуля вверх/вниз при резком отпускании вертикального упора.<br><i>Допуск:</i> менее 5.0%.<br><i>Замеряется в:</i> Этап 4 (Snapback).",

    "anom_row7_name": "Вероятность отскока",
    "anom_row7_tol": "< 10.0%",
    "anom_row7_tip": "<b>Вероятность отскока (Snapback Rate):</b><br>Доля резких сбросов стика, приведших к паразитному перелёту нуля (> 5.0%).<br><i>Допуск:</i> до 10.0% (норма: 0%).",

    "anom_row8_name": "Итоговый вердикт",
    "anom_row8_tol": "—",
    "anom_row8_tip": "<b>Комплексная оценка исправности узла:</b><br>Выносится по результатам всех этапов проверки.",

    # -------------------------------------------------------------------------
    # Triggers
    # -------------------------------------------------------------------------
    "triggers_box_title": "Курки",
    "trigger_lt_name": "<b>LT/L2</b>",
    "trigger_rt_name": "<b>RT/R2</b>",

    # -------------------------------------------------------------------------
    # Buttons & Debounce Table
    # -------------------------------------------------------------------------
    "buttons_title": "<b>Тестирование кнопок, крестовины (D-Pad) и детектор дребезга контактов</b>",
    "btn_clear_counters": "Сбросить счётчики",
    "col_btn_code": "Код (Hex / Dec)",
    "col_btn_name": "Назначение кнопки",
    "col_btn_state": "Состояние",
    "col_btn_presses": "Нажатий",
    "col_btn_chatter": "Дребезг",
    "col_btn_min_dt": "Мин. интервал",
    "chatter_log_title": "<b>Журнал событий дребезга (Ложные / повторные срабатывания &lt; 7 мс):</b>",

    "state_pressed": "Нажата",
    "state_released": "Отпущена",
    "btn_ok": "ОК",
    "btn_chatter_detected": "Дребезг!",

    # -------------------------------------------------------------------------
    # Polling Rate & Bus Stability
    # -------------------------------------------------------------------------
    "polling_title": "<b>Частота опроса (Polling Rate) и стабильность шины</b>",
    "btn_reset_stats": "Сбросить статистику",
    "axis_polling_dt": "Интервал Δt между пакетами (мс)",
    "axis_polling_idx": "Индекс пакета опроса (история шины)",
    "polling_stats_fmt": "Интервал dt: {dt:.2f} мс | Джиттер (StdDev): {jitter:.3f} мс | Пакетов: {packets}",
    "polling_bus": "Шина:",
    "polling_jitter": "Джиттер:",
    "polling_channel": "Канал:",
    "polling_conn_wireless": "Беспроводной",
    "polling_conn_wired": "Проводной USB",
    "polling_dedup": "Отсечено дублей:",
    "polling_drops_excluded": "Потери исключены",
    "polling_drops": "Потерь:",
    "polling_note": "ℹ️ <b>Стабильность шины:</b> Вращайте стики по кругу для замера частоты. Для проводных геймпадов отсечение одинаковых пакетов драйвером Linux является штатным (не потеря кадров). Осциллограф отображает выровненный интервал шины и реальный аппаратный джиттер.",

    # -------------------------------------------------------------------------
    # Rumble & Actuators
    # -------------------------------------------------------------------------
    "rumble_group_title": "Тестирование вибромоторов (Force Feedback / Rumble)",
    "lbl_left_motor": "Левый мотор (Тяжёлый / НЧ):",
    "lbl_right_motor": "Правый мотор (Лёгкий / ВЧ):",
    "btn_pulse_left": "🔴 Импульс Левый (1с)",
    "btn_pulse_right": "🔵 Импульс Правый (1с)",
    "btn_pulse_both": "🟣 Импульс Оба (1с)",
    "btn_stop_rumble": "⏹ Стоп",

    "ff_no_device": "⚠️ <b>Контроллер не выбран:</b> Подключите игровой контроллер для тестирования вибромоторов.",
    "ff_unsupported": "⚠️ <b>Внимание:</b> Подключенное устройство не поддерживает аппаратную обратную связь (Force Feedback / виброотклик отсутствует в дескрипторе HID). Команды вибрации недоступны.",
    "ff_supported": "✅ <b>Обратная связь поддерживается:</b> Обнаружен активный драйвер виброотклика (EV_FF / Force Feedback). Вы можете протестировать раздельно левый (тяжёлый/НЧ) и правый (лёгкий/ВЧ) вибромоторы.",

    # -------------------------------------------------------------------------
    # LED & Indication
    # -------------------------------------------------------------------------
    "led_group_title": "Управление индикацией и светодиодами (Раздельные команды)",
    "tab_led_info": "ℹ️ О технологии и совместимости",
    "tab_led_sony": "🎮 Sony PlayStation (RGB Lightbar)",
    "tab_led_xbox": "🎮 Microsoft Xbox (Ring of Light)",

    "lbl_sony_desc": "<b>Подсветка Sony DualSense (PS5) & DualShock 4 (PS4) Lightbar:</b>",
    "lbl_presets": "Пресеты:",
    "btn_apply_rgb": "Применить RGB",

    "lbl_xbox_desc": "<b>Светодиодное кольцо Microsoft Xbox 360 (Ring of Light):</b>",
    "lbl_players": "Игроки:",
    "lbl_modes": "Режимы:",
    "player_1": "1️⃣ Игрок 1",
    "player_2": "2️⃣ Игрок 2",
    "player_3": "3️⃣ Игрок 3",
    "player_4": "4️⃣ Игрок 4",
    "player_off": "⚫ Откл",
    "mode_rotate": "🔄 Вращение",
    "mode_fast_blink": "⚡ Быстрое мигание",
    "mode_slow_blink": "⏳ Медленно",
    "mode_alternating": "🔀 Чередование",

    "lbl_xbox_root_notice": (
        "⚠️ <b>Внимание (Права доступа в Linux):</b> Управление кольцом светодиодов xpad осуществляется через системный узел sysfs "
        "(<code>/sys/class/leds/xpad*/brightness</code>). В Linux для записи в этот узел по умолчанию требуются <b>повышенные права (root)</b>.<br><br>"
        "Если контроллер не реагирует на команды переключения квадрантов или анимаций:<br>"
        "• Запустите утилиту с <code>sudo</code>, либо<br>"
        "• Разрешите однократно запись командой в терминале:<br>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<code>sudo chmod 666 /sys/class/leds/xpad*/brightness</code><br>"
        "• Либо создайте постоянное udev-правило для доступа без root."
    ),

    "led_info_html": """
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
    """,

    # -------------------------------------------------------------------------
    # Diagnostic Report & Passport (UI, Text & PDF)
    # -------------------------------------------------------------------------
    "report_header_title": "<b>Паспорт технического состояния и диагностический отчёт</b>",
    "btn_refresh_report": "Обновить данные",
    "btn_copy_clipboard": "Копировать в буфер",
    "btn_export_pdf": "📄 Экспорт в PDF",
    "btn_export_txt": "💾 Сохранить .txt",
    "pdf_export_success": "PDF-паспорт успешно сохранён в файл:\n{path}",
    "txt_export_success": "Текстовый отчёт успешно сохранён в файл:\n{path}",
    "pdf_export_error": "Ошибка при формировании PDF-отчёта:\n{err}",
    "report_copied_notice": "Отчёт успешно скопирован в буфер обмена!",

    # Report Sections & Fields
    "pdf_doc_title": "🎮 Паспорт технического состояния геймпада",
    "pdf_doc_subtitle": "Дата проверки: {date} | Комплекс: Gamepad Tester Pro 2.0",
    "sec_device_info": "Параметры устройства",
    "sec_node_results": "Результаты измерений по узлам",
    "sec_authenticity": "Предполагаемые характеристики и аппаратная подлинность",
    "param_label": "Параметр",
    "value_label": "Значение",
    "node_label": "Узел / Тест",
    "metrics_label": "Измеренные параметры",
    "verdict_label": "Вердикт",

    "dev_model": "Модель устройства",
    "dev_vid_pid": "Идентификатор (VID / PID)",
    "dev_interface": "Интерфейс подключения",
    "dev_layout": "Профиль раскладки",

    "verdict_global_pass": "ИТОГОВЫЙ СТАТУС: ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО (НОРМА)",
    "verdict_global_fail": "ИТОГОВЫЙ СТАТУС: ОБНАРУЖЕНЫ ДЕФЕКТЫ ИЛИ ОТКЛОНЕНИЯ",

    "node_polling": "Шина и опрос",
    "node_buttons": "Кнопки (Дребезг)",
    "node_stick_l": "Левый стик",
    "node_stick_r": "Правый стик",
    "node_triggers": "Триггеры (Курки)",

    "polling_line_pdf": "Частота: <b>{hz} Гц</b> (номинал ~{target_hz} Гц) | Джиттер: <b>{jitter} мс</b><br/>Тип: {conn} | {drops} | Отсечено дублей ядра: {dedup}",
    "buttons_line_pdf_pass": "Проверено: {total} | Дребезг (&lt; 7 мс): <b>0</b> (не выявлен)",
    "buttons_line_pdf_fail": "Проверено: {total} | Дребезг (&lt; 7 мс): <b>{chatter}</b><br/><font color='#DC2626'>⚠️ <b>Кнопки с дребезгом:</b> {buttons}</font>",
    "stick_line_pdf": "Ошибка круга: <b>{circ:.1f}%</b>{bezel} | Шум: <b>{jitter:.2f}%</b><br/>Snapback X: <b>{rate_x:.0f}%</b> ({flicks_x}/{total_x}, вылет {reach_x:.1f}%) | Snapback Y: <b>{rate_y:.0f}%</b> ({flicks_y}/{total_y}, вылет {reach_y:.1f}%)",

    "pdf_footer_note": "Отчёт сформирован программным комплексом Gamepad Tester Pro. Предназначен для контроля качества, ремонта и верификации датчиков Холла, потенциометров и аппаратных платформ.",

    # Authenticity Labels
    "auth_param": "Параметр платформы",
    "auth_result": "Характеристика и результат верификации",
    "auth_stick_adc": "Предполагаемый АЦП стиков",
    "auth_trigger_adc": "Предполагаемый АЦП курков",
    "auth_profile": "Платформенный профиль",
    "auth_expected": "Ожидается по спецификации",
    "auth_actual": "Фактически обнаружено",
    "auth_verdict": "Заключение о подлинности",
    "auth_conclusion": "Экспертный вывод",

    # Text report headers
    "txt_rep_title": "ПАСПОРТ ТЕХНИЧЕСКОГО СОСТОЯНИЯ ГЕЙМПАДА",
    "txt_rep_date": "Дата проверки:",
    "txt_rep_dev": "Устройство:",
    "txt_rep_id": "Идентификатор:",
    "txt_rep_iface": "Интерфейс:",
    "txt_rep_layout": "Определенная схема:",
    "txt_rep_verdict": "ИТОГОВОЕ ЗАКЛЮЧЕНИЕ:",
    "txt_rep_verdict_pass": "✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ (НОРМА)",
    "txt_rep_verdict_fail": "⚠️ ОБНАРУЖЕНЫ ДЕФЕКТЫ / ОТКЛОНЕНИЯ",
    "txt_rep_sec1": "1. ЧАСТОТА ОПРОСА И СТАБИЛЬНОСТЬ ШИНЫ (POLLING RATE)",
    "txt_rep_sec2": "2. КНОПКИ И ДРЕБЕЗГ КОНТАКТОВ (DEBOUNCE / CHATTER)",
    "txt_rep_sec3": "3. ЛЕВЫЙ АНАЛОГОВЫЙ СТИК",
    "txt_rep_sec4": "4. ПРАВЫЙ АНАЛОГОВЫЙ СТИК",
    "txt_rep_sec5": "5. АНАЛОГОВЫЕ ТРИГГЕРЫ (КУРКИ)",
    "txt_rep_sec6": "6. ПРЕДПОЛАГАЕМЫЕ ХАРАКТЕРИСТИКИ И ПОДЛИННОСТЬ УСТРОЙСТВА",
    "txt_rep_sec7": "7. ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ И РЕКОМЕНДАЦИИ:",

    # Buttons visual diagram
    "tab_buttons_table": "📋 Таблица",
    "tab_buttons_diagram": "🎮 Схема",
    "diagram_title": "Визуальная проверка кнопок и стиков",
    "diagram_tested_count": "Проверено: {tested} из {total} ({pct}%)",
    "diagram_all_tested": "✅ Все основные кнопки проверены!",
    "btn_reset_diagram": "Сбросить проверку",
    "legend_untested": "Не проверена",
    "legend_pressed": "Нажата сейчас",
    "legend_tested": "Проверена",
    "diagram_telemetry": "LS: X:{lx:+.2f} Y:{ly:+.2f}  |  RS: X:{rx:+.2f} Y:{ry:+.2f}  |  LT: {lt}%  RT: {rt}%",
    "diagram_last_btn": "Последняя: {btn}",
    "diagram_no_press": "Ожидание ввода...",

    # Touchpad & Gyroscope / IMU
    "touchpad_group_title": "Сенсорная панель (Touchpad)",
    "tp_no_device": "Контроллер не выбран.",
    "tp_unsupported": "⚠️ Тачпад не обнаружен на текущем контроллере (или отсутствует в дескрипторе).",
    "tp_coords_fmt": "Палец 1: {f1}  |  Палец 2: {f2}\nКлик панели: {click} ({clicks})  |  Касаний: {touches}",
    "gyro_group_title": "Гироскоп и Акселерометр (IMU)",
    "gyro_no_device": "Контроллер не выбран.",
    "gyro_unsupported": "⚠️ Гироскоп / IMU не обнаружен на текущем контроллере (или не поддерживается драйвером).",
    "gyro_rot_title": "Поворот (Углы / Скорость)",
    "gyro_shift_title": "Смещение (Δg / Акселерометр)",
    "btn_gyro_recenter": "🎯 Центр / Калибр.",
    "gyro_plot_axis_y": "Угол (°)",
    "gyro_plot_axis_x": "Время (с)",
    "unit_deg_s": "°/с",
}

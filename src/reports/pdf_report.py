"""
Diagnostic PDF Report Generator
Generates a styled PDF report using ReportLab with full Cyrillic Unicode support
by registering system TrueType fonts (DejaVuSans / LiberationSans / NotoSans).
"""

import os
import time
import html
from typing import Dict, Any, Optional
from ..analysis.authenticity import analyze_authenticity

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# Font paths to search for Cyrillic support (Arch, Debian, Ubuntu, Fedora, openSUSE)
CYRILLIC_FONT_CANDIDATES = [
    ("/usr/share/fonts/TTF/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ("/usr/share/fonts/noto/NotoSans-Regular.ttf", "/usr/share/fonts/noto/NotoSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
]

_FONT_REGISTERED = False
_REG_FONT_NAME = "Helvetica"
_REG_FONT_BOLD = "Helvetica-Bold"

LAST_PDF_ERROR: str = ""


def get_last_pdf_error() -> str:
    """Returns the most recent PDF generation error message."""
    global LAST_PDF_ERROR
    return LAST_PDF_ERROR


def _setup_cyrillic_font():
    """Finds and registers a TrueType font with Cyrillic support in ReportLab."""
    global _FONT_REGISTERED, _REG_FONT_NAME, _REG_FONT_BOLD
    if _FONT_REGISTERED or not REPORTLAB_AVAILABLE:
        return

    for regular_path, bold_path in CYRILLIC_FONT_CANDIDATES:
        if os.path.isfile(regular_path):
            try:
                pdfmetrics.registerFont(TTFont("CustomCyrillic", regular_path))
                _REG_FONT_NAME = "CustomCyrillic"

                if os.path.isfile(bold_path):
                    pdfmetrics.registerFont(TTFont("CustomCyrillic-Bold", bold_path))
                    _REG_FONT_BOLD = "CustomCyrillic-Bold"
                else:
                    _REG_FONT_BOLD = "CustomCyrillic"

                _FONT_REGISTERED = True
                return
            except Exception as e:
                print(f"[PDF] Font registration failed for {regular_path}: {e}")

    _FONT_REGISTERED = True


def generate_pdf_report(output_filepath: str,
                         device_info: Dict[str, Any],
                         polling_data: Dict[str, Any],
                         buttons_data: Dict[str, Any],
                         left_stick: Dict[str, Any],
                         right_stick: Dict[str, Any],
                         triggers_data: Dict[str, Any]) -> bool:
    """Generates a professional diagnostic PDF report with full Cyrillic support."""
    global LAST_PDF_ERROR
    LAST_PDF_ERROR = ""

    if not REPORTLAB_AVAILABLE:
        LAST_PDF_ERROR = "Библиотека 'reportlab' не установлена в системе (установите: pip install reportlab)."
        print(f"[PDF] {LAST_PDF_ERROR}")
        return False

    # Check write access to destination path before building document
    try:
        # If file exists, try appending/opening for write to ensure not locked by another process
        with open(output_filepath, 'a' if os.path.exists(output_filepath) else 'w') as test_f:
            pass
    except PermissionError:
        LAST_PDF_ERROR = (
            f"Отказано в доступе к файлу:\n{output_filepath}\n\n"
            "Возможные причины:\n"
            "• Файл открыт в другой программе (просмотрщике PDF: Okular, Evince, Браузере);\n"
            "• У вас нет прав на запись в эту папку или перезапись файла."
        )
        print(f"[PDF] {LAST_PDF_ERROR}")
        return False
    except Exception as e:
        LAST_PDF_ERROR = f"Не удалось открыть файл для записи: {e}"
        print(f"[PDF] {LAST_PDF_ERROR}")
        return False

    _setup_cyrillic_font()

    try:
        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            fontName=_REG_FONT_BOLD,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            fontName=_REG_FONT_NAME,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=12
        )
        h2_style = ParagraphStyle(
            'H2Style',
            fontName=_REG_FONT_BOLD,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            fontName=_REG_FONT_NAME,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )
        bold_style = ParagraphStyle(
            'Bold',
            fontName=_REG_FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0F172A')
        )

        elements = []

        # Header
        elements.append(Paragraph("🎮 Паспорт технического состояния геймпада", title_style))
        elements.append(Paragraph(f"Дата проверки: {time.strftime('%Y-%m-%d %H:%M:%S')} | Комплекс: Gamepad Tester Pro 2.0", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceAfter=10))

        # Device Info Table (escaped safely)
        dev_name = html.escape(str(device_info.get('name', 'Unknown')))
        dev_path = html.escape(str(device_info.get('event_path', 'N/A')))
        dev_layout = html.escape(str(device_info.get('layout', 'Standard')))

        dev_table_data = [
            [Paragraph("Параметр", bold_style), Paragraph("Значение", bold_style)],
            [Paragraph("Модель устройства", body_style), Paragraph(dev_name, body_style)],
            [Paragraph("Идентификатор (VID / PID)", body_style), Paragraph(f"0x{device_info.get('vid', 0):04X} : 0x{device_info.get('pid', 0):04X}", body_style)],
            [Paragraph("Интерфейс подключения", body_style), Paragraph(dev_path, body_style)],
            [Paragraph("Профиль раскладки", body_style), Paragraph(dev_layout, body_style)],
        ]
        t_dev = Table(dev_table_data, colWidths=[160, 360])
        t_dev.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_dev)
        elements.append(Spacer(1, 10))

        # Authenticity & Hardware Profile Analysis
        auth = analyze_authenticity(device_info, left_stick, right_stick, triggers_data)

        # Overall Status Verdict
        has_chatter = buttons_data.get("status") != "PASS"
        has_snapback = (left_stick.get("snapback_flicks", 0) > 0 or right_stick.get("snapback_flicks", 0) > 0 or
                        left_stick.get("snapback_count", 0) > 0 or right_stick.get("snapback_count", 0) > 0)
        has_circ_err = (left_stick.get("circularity_error_pct", 0) > 8.0 or right_stick.get("circularity_error_pct", 0) > 8.0)

        if not has_chatter and not has_snapback and not has_circ_err and not auth.is_replica:
            verdict_text = "ИТОГОВЫЙ СТАТУС: ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО (НОРМА)"
            bg_color = colors.HexColor('#DCFCE7')
            border_color = colors.HexColor('#16A34A')
            text_color = colors.HexColor('#166534')
        else:
            verdict_text = "ИТОГОВЫЙ СТАТУС: ОБНАРУЖЕНЫ ДЕФЕКТЫ ИЛИ ОТКЛОНЕНИЯ"
            bg_color = colors.HexColor('#FEF3C7')
            border_color = colors.HexColor('#D97706')
            text_color = colors.HexColor('#92400E')

        v_style = ParagraphStyle(
            'Verdict',
            fontName=_REG_FONT_BOLD,
            fontSize=10,
            leading=14,
            textColor=text_color
        )
        verdict_table = Table([[Paragraph(verdict_text, v_style)]], colWidths=[520])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(verdict_table)
        elements.append(Spacer(1, 10))

        ls_gate = left_stick.get('gate_shape', '')
        ls_bezel_tag = " (без безеля)" if ("без безеля" in ls_gate.lower() or "квадрат" in ls_gate.lower()) else ""

        rs_gate = right_stick.get('gate_shape', '')
        rs_bezel_tag = " (без безеля)" if ("без безеля" in rs_gate.lower() or "квадрат" in rs_gate.lower()) else ""

        # Triggers summary line
        trig_strs = []
        for name, t in triggers_data.items():
            trig_strs.append(f"<b>{name}:</b> ход 0..{t.get('raw_max', 255)} ({t.get('current_val_pct', 0):.1f}%)")
        trig_display = " | ".join(trig_strs) if trig_strs else "Не тестировались"

        # Detailed Test Results Table
        elements.append(Paragraph("Результаты измерений по узлам", h2_style))
        results_data = [
            [Paragraph("Узел / Тест", bold_style), Paragraph("Измеренные параметры", bold_style), Paragraph("Вердикт", bold_style)],
            [
                Paragraph("Шина и опрос", bold_style),
                Paragraph(f"Частота: <b>{polling_data.get('current_hz', 0)} Гц</b> | Джиттер dt: <b>{polling_data.get('jitter_stddev_ms', 0)} мс</b> | Пропусков: {polling_data.get('dropped_packets', 0)}", body_style),
                Paragraph("Норма" if polling_data.get("status") == "PASS" else "Высокий джиттер", body_style)
            ],
            [
                Paragraph("Кнопки (Дребезг)", bold_style),
                Paragraph(f"Проверено: {buttons_data.get('total_buttons_tested', 0)} | Событий &lt; 7 мс: <b>{buttons_data.get('total_chatter_events', 0)}</b>", body_style),
                Paragraph("Без дребезга" if not has_chatter else "Дребезг!", body_style)
            ],
            [
                Paragraph("Левый стик", bold_style),
                Paragraph(
                    f"Ошибка круга: <b>{left_stick.get('circularity_error_pct', 0):.1f}%</b>{ls_bezel_tag} | Шум: <b>{left_stick.get('peak_jitter_pct', 0):.2f}%</b><br/>"
                    f"Snapback X: <b>{left_stick.get('snapback_rate_x_pct', 0):.0f}%</b> ({left_stick.get('snapback_flicks_x', 0)}/{left_stick.get('total_flicks_x', 0)}, вылет {left_stick.get('max_snapback_x_pct', 0):.1f}%) | "
                    f"Snapback Y: <b>{left_stick.get('snapback_rate_y_pct', 0):.0f}%</b> ({left_stick.get('snapback_flicks_y', 0)}/{left_stick.get('total_flicks_y', 0)}, вылет {left_stick.get('max_snapback_y_pct', 0):.1f}%)",
                    body_style
                ),
                Paragraph("Норма" if left_stick.get("status") == "PASS" else "Отклонение", body_style)
            ],
            [
                Paragraph("Правый стик", bold_style),
                Paragraph(
                    f"Ошибка круга: <b>{right_stick.get('circularity_error_pct', 0):.1f}%</b>{rs_bezel_tag} | Шум: <b>{right_stick.get('peak_jitter_pct', 0):.2f}%</b><br/>"
                    f"Snapback X: <b>{right_stick.get('snapback_rate_x_pct', 0):.0f}%</b> ({right_stick.get('snapback_flicks_x', 0)}/{right_stick.get('total_flicks_x', 0)}, вылет {right_stick.get('max_snapback_x_pct', 0):.1f}%) | "
                    f"Snapback Y: <b>{right_stick.get('snapback_rate_y_pct', 0):.0f}%</b> ({right_stick.get('snapback_flicks_y', 0)}/{right_stick.get('total_flicks_y', 0)}, вылет {right_stick.get('max_snapback_y_pct', 0):.1f}%)",
                    body_style
                ),
                Paragraph("Норма" if right_stick.get("status") == "PASS" else "Отклонение", body_style)
            ],
            [
                Paragraph("Триггеры (Курки)", bold_style),
                Paragraph(trig_display, body_style),
                Paragraph("Норма", body_style)
            ],
        ]

        t_res = Table(results_data, colWidths=[120, 310, 90])
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_res)

        # Hardware Architecture & Authenticity Section
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Предполагаемые характеристики и аппаратная подлинность", h2_style))

        badge_bg = colors.HexColor('#FEF3C7') if auth.is_replica else colors.HexColor('#DCFCE7')
        badge_text_color = colors.HexColor('#92400E') if auth.is_replica else colors.HexColor('#166534')

        verdict_badge_style = ParagraphStyle(
            'VerdictBadge',
            fontName=_REG_FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=badge_text_color
        )

        arch_table_data = [
            [Paragraph("Параметр платформы", bold_style), Paragraph("Характеристика и результат верификации", bold_style)],
            [Paragraph("Предполагаемый АЦП стиков", body_style), Paragraph(f"<b>{auth.stick_adc_str}</b>", body_style)],
            [Paragraph("Предполагаемый АЦП курков", body_style), Paragraph(f"<b>{auth.trigger_adc_str}</b>", body_style)],
            [Paragraph("Платформенный профиль", body_style), Paragraph(f"<b>{auth.archetype}</b>", body_style)],
            [Paragraph("Ожидается по спецификации", body_style), Paragraph(auth.expected_spec, body_style)],
            [Paragraph("Фактически обнаружено", body_style), Paragraph(auth.actual_spec, body_style)],
            [Paragraph("Заключение о подлинности", bold_style), Paragraph(auth.verdict, verdict_badge_style)],
            [Paragraph("Экспертный вывод", body_style), Paragraph(auth.comment, body_style)],
        ]

        t_arch = Table(arch_table_data, colWidths=[150, 370])
        t_arch.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (1, 6), (1, 6), badge_bg),
        ]))
        elements.append(t_arch)

        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Отчёт сформирован программным комплексом Gamepad Tester Pro. Предназначен для контроля качества, ремонта и верификации датчиков Холла, потенциометров и аппаратных платформ.", subtitle_style))

        doc.build(elements)
        return True
    except Exception as e:
        LAST_PDF_ERROR = f"{type(e).__name__}: {str(e)}"
        print(f"[PDF] Generation error: {LAST_PDF_ERROR}")
        return False

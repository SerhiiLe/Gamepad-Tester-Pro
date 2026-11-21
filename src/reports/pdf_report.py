"""
Diagnostic PDF Report Generator
Generates a styled PDF report using ReportLab with full Cyrillic and Latin Unicode support
by registering system TrueType fonts (DejaVuSans / LiberationSans / NotoSans).
Strictly fits on a single A4 page. Supports bilingual Russian (RU) and English (EN) generation.
"""

import os
import time
import html
from typing import Dict, Any, Optional
from ..analysis.authenticity import analyze_authenticity

try:
    from ..i18n import i18n
except Exception:
    i18n = None

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
                         triggers_data: Dict[str, Any],
                         lang: Optional[str] = None) -> bool:
    """Generates a professional diagnostic PDF report strictly fitted onto a single A4 page in RU or EN."""
    global LAST_PDF_ERROR
    LAST_PDF_ERROR = ""

    if lang is None and i18n is not None:
        lang = i18n.current_lang
    is_en = (str(lang).upper() == "EN")

    def t(key: str, **kwargs) -> str:
        if i18n is not None:
            # If lang is explicitly requested and different from i18n.current_lang
            if lang and lang.upper() in i18n._bundles:
                text = i18n._bundles[lang.upper()].get(key, key)
                if kwargs:
                    try:
                        return text.format(**kwargs)
                    except Exception:
                        return text
                return text
            return i18n.tr(key, **kwargs)
        return key

    if not REPORTLAB_AVAILABLE:
        LAST_PDF_ERROR = "ReportLab is not installed (install via: pip install reportlab)." if is_en else "Библиотека 'reportlab' не установлена в системе (установите: pip install reportlab)."
        print(f"[PDF] {LAST_PDF_ERROR}")
        return False

    # Check write access to destination path before building document
    try:
        with open(output_filepath, 'a' if os.path.exists(output_filepath) else 'w') as test_f:
            pass
    except PermissionError:
        LAST_PDF_ERROR = (
            f"Permission denied to file:\n{output_filepath}\n\n"
            "Possible causes:\n"
            "• File is open in another PDF viewer (Okular, Evince, Browser);\n"
            "• You do not have write permissions for this folder."
            if is_en else
            f"Отказано в доступе к файлу:\n{output_filepath}\n\n"
            "Возможные причины:\n"
            "• Файл открыт в другой программе (просмотрщике PDF: Okular, Evince, Браузере);\n"
            "• У вас нет прав на запись в эту папку или перезапись файла."
        )
        print(f"[PDF] {LAST_PDF_ERROR}")
        return False
    except Exception as e:
        LAST_PDF_ERROR = f"Cannot open file for writing: {e}" if is_en else f"Не удалось открыть файл для записи: {e}"
        print(f"[PDF] {LAST_PDF_ERROR}")
        return False

    _setup_cyrillic_font()

    try:
        # Standard comfortable margins: 36 pt (12.7 mm) left/right, 34 pt top/bottom
        margin_x = 36
        margin_y = 34
        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            leftMargin=margin_x,
            rightMargin=margin_x,
            topMargin=margin_y,
            bottomMargin=margin_y
        )
        avail_w = 595.27 - 2 * margin_x  # ~523.27 pt

        # 1. Header Styles
        title_style = ParagraphStyle(
            'TitleStyle',
            fontName=_REG_FONT_BOLD,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            fontName=_REG_FONT_NAME,
            fontSize=9.0,
            leading=12,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=4
        )

        # 2. Section Headings (H2)
        h2_style = ParagraphStyle(
            'H2Style',
            fontName=_REG_FONT_BOLD,
            fontSize=11.0,
            leading=14,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=4,
            spaceAfter=2
        )

        # 3. Base Table Typography (9.0 pt)
        body_style = ParagraphStyle(
            'Body',
            fontName=_REG_FONT_NAME,
            fontSize=9.0,
            leading=11.5,
            textColor=colors.HexColor('#334155')
        )
        bold_style = ParagraphStyle(
            'Bold',
            fontName=_REG_FONT_BOLD,
            fontSize=9.0,
            leading=11.5,
            textColor=colors.HexColor('#0F172A')
        )

        # 4. Footer Note (7.5 pt)
        footer_style = ParagraphStyle(
            'Footer',
            fontName=_REG_FONT_NAME,
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#64748B')
        )

        elements = []

        # Header
        elements.append(Paragraph(t("pdf_doc_title"), title_style))
        elements.append(Paragraph(t("pdf_doc_subtitle", date=time.strftime('%Y-%m-%d %H:%M:%S')), subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#0284C7'), spaceAfter=4))

        # Device Info Table
        dev_name = html.escape(str(device_info.get('name', 'Unknown')))
        dev_path = html.escape(str(device_info.get('event_path', 'N/A')))
        dev_layout = html.escape(str(device_info.get('layout', 'Standard')))

        dev_table_data = [
            [Paragraph(t("param_label"), bold_style), Paragraph(t("value_label"), bold_style)],
            [Paragraph(t("dev_model"), body_style), Paragraph(dev_name, body_style)],
            [Paragraph(t("dev_vid_pid"), body_style), Paragraph(f"0x{device_info.get('vid', 0):04X} : 0x{device_info.get('pid', 0):04X}", body_style)],
            [Paragraph(t("dev_interface"), body_style), Paragraph(dev_path, body_style)],
            [Paragraph(t("dev_layout"), body_style), Paragraph(dev_layout, body_style)],
        ]
        t_dev = Table(dev_table_data, colWidths=[140, avail_w - 140])
        t_dev.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        elements.append(t_dev)
        elements.append(Spacer(1, 4))

        # Authenticity & Hardware Profile Analysis
        auth = analyze_authenticity(device_info, left_stick, right_stick, triggers_data, lang=lang)

        # Overall Status Verdict
        has_chatter = buttons_data.get("status") != "PASS"
        has_snapback = (left_stick.get("snapback_flicks_x", 0) > 0 or left_stick.get("snapback_flicks_y", 0) > 0 or
                        right_stick.get("snapback_flicks_x", 0) > 0 or right_stick.get("snapback_flicks_y", 0) > 0 or
                        left_stick.get("snapback_count", 0) > 0 or right_stick.get("snapback_count", 0) > 0)
        has_circ_err = (left_stick.get("circularity_error_pct", 0) > 8.0 or right_stick.get("circularity_error_pct", 0) > 8.0)

        if not has_chatter and not has_snapback and not has_circ_err and not auth.is_replica:
            verdict_text = t("verdict_global_pass")
            bg_color = colors.HexColor('#DCFCE7')
            border_color = colors.HexColor('#16A34A')
            text_color = colors.HexColor('#166534')
        else:
            verdict_text = t("verdict_global_fail")
            bg_color = colors.HexColor('#FEF3C7')
            border_color = colors.HexColor('#D97706')
            text_color = colors.HexColor('#92400E')

        v_style = ParagraphStyle(
            'Verdict',
            fontName=_REG_FONT_BOLD,
            fontSize=10.0,
            leading=13,
            textColor=text_color
        )
        verdict_table = Table([[Paragraph(verdict_text, v_style)]], colWidths=[avail_w])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ]))
        elements.append(verdict_table)
        elements.append(Spacer(1, 4))

        ls_gate = left_stick.get('gate_shape', '')
        is_ls_no_bezel = ("без безеля" in ls_gate.lower() or "квадрат" in ls_gate.lower() or "no bezel" in ls_gate.lower() or "square" in ls_gate.lower())
        ls_bezel_tag = (" (no bezel)" if is_en else " (без безеля)") if is_ls_no_bezel else ""

        rs_gate = right_stick.get('gate_shape', '')
        is_rs_no_bezel = ("без безеля" in rs_gate.lower() or "квадрат" in rs_gate.lower() or "no bezel" in rs_gate.lower() or "square" in rs_gate.lower())
        rs_bezel_tag = (" (no bezel)" if is_en else " (без безеля)") if is_rs_no_bezel else ""

        # Triggers summary line
        trig_strs = []
        for name, tr_item in triggers_data.items():
            trig_strs.append(f"<b>{name}:</b> {tr_item.get('raw_max', 255)} ({tr_item.get('current_val_pct', 0):.1f}%)")
        trig_display = " | ".join(trig_strs) if trig_strs else ("Not tested" if is_en else "Не тестировались")

        # Polling rate formatting
        is_wireless = polling_data.get('is_wireless', False)
        conn_str = t("polling_conn_wireless") if is_wireless else t("polling_conn_wired")
        drops_cnt = polling_data.get('dropped_packets', 0)
        drops_str = f"{t('polling_drops')} <b>{drops_cnt}</b>" if is_wireless else t("polling_drops_excluded")
        poll_details = t(
            "polling_line_pdf",
            hz=polling_data.get('current_hz', 0),
            target_hz=polling_data.get('nominal_target_hz', 0),
            jitter=f"{polling_data.get('jitter_stddev_ms', 0):.3f}",
            conn=conn_str,
            drops=drops_str,
            dedup=polling_data.get('dedup_packets', 0)
        )
        poll_verdict = t("btn_ok") if polling_data.get("status") == "PASS" else ("<font color='#DC2626'><b>Jitter</b></font>" if is_en else "<font color='#DC2626'><b>Джиттер</b></font>")

        # Buttons chatter & faulty buttons formatting
        faulty = buttons_data.get("faulty_buttons", [])
        if faulty:
            btn_details = t(
                "buttons_line_pdf_fail",
                total=buttons_data.get('total_buttons_tested', 0),
                chatter=buttons_data.get('total_chatter_events', 0),
                buttons=html.escape(', '.join(faulty))
            )
            btn_verdict = "<font color='#DC2626'><b>" + t("btn_chatter_detected") + "</b></font>"
        else:
            btn_details = t(
                "buttons_line_pdf_pass",
                total=buttons_data.get('total_buttons_tested', 0)
            )
            btn_verdict = t("btn_ok")

        # Detailed Test Results Table
        elements.append(Paragraph(t("sec_node_results"), h2_style))
        pass_text = t("btn_ok")
        defect_text = "<font color='#DC2626'><b>" + ("Defect" if is_en else "Отклонение") + "</b></font>"

        results_data = [
            [Paragraph(t("node_label"), bold_style), Paragraph(t("metrics_label"), bold_style), Paragraph(t("verdict_label"), bold_style)],
            [
                Paragraph(t("node_polling"), bold_style),
                Paragraph(poll_details, body_style),
                Paragraph(poll_verdict, body_style)
            ],
            [
                Paragraph(t("node_buttons"), bold_style),
                Paragraph(btn_details, body_style),
                Paragraph(btn_verdict, body_style)
            ],
            [
                Paragraph(t("node_stick_l"), bold_style),
                Paragraph(
                    t("stick_line_pdf",
                      circ=left_stick.get('circularity_error_pct', 0),
                      bezel=ls_bezel_tag,
                      jitter=left_stick.get('peak_jitter_pct', 0),
                      rate_x=left_stick.get('snapback_rate_x_pct', 0),
                      flicks_x=left_stick.get('snapback_flicks_x', 0),
                      total_x=left_stick.get('total_flicks_x', 0),
                      reach_x=left_stick.get('max_snapback_x_pct', 0),
                      rate_y=left_stick.get('snapback_rate_y_pct', 0),
                      flicks_y=left_stick.get('snapback_flicks_y', 0),
                      total_y=left_stick.get('total_flicks_y', 0),
                      reach_y=left_stick.get('max_snapback_y_pct', 0)),
                    body_style
                ),
                Paragraph(pass_text if left_stick.get("status") == "PASS" else defect_text, body_style)
            ],
            [
                Paragraph(t("node_stick_r"), bold_style),
                Paragraph(
                    t("stick_line_pdf",
                      circ=right_stick.get('circularity_error_pct', 0),
                      bezel=rs_bezel_tag,
                      jitter=right_stick.get('peak_jitter_pct', 0),
                      rate_x=right_stick.get('snapback_rate_x_pct', 0),
                      flicks_x=right_stick.get('snapback_flicks_x', 0),
                      total_x=right_stick.get('total_flicks_x', 0),
                      reach_x=right_stick.get('max_snapback_x_pct', 0),
                      rate_y=right_stick.get('snapback_rate_y_pct', 0),
                      flicks_y=right_stick.get('snapback_flicks_y', 0),
                      total_y=right_stick.get('total_flicks_y', 0),
                      reach_y=right_stick.get('max_snapback_y_pct', 0)),
                    body_style
                ),
                Paragraph(pass_text if right_stick.get("status") == "PASS" else defect_text, body_style)
            ],
            [
                Paragraph(t("node_triggers"), bold_style),
                Paragraph(trig_display, body_style),
                Paragraph(pass_text, body_style)
            ],
        ]

        t_res = Table(results_data, colWidths=[115, avail_w - 115 - 85, 85])
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        elements.append(t_res)

        # Hardware Architecture & Authenticity Section
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(t("sec_authenticity"), h2_style))

        badge_bg = colors.HexColor('#FEF3C7') if auth.is_replica else colors.HexColor('#DCFCE7')
        badge_text_color = colors.HexColor('#92400E') if auth.is_replica else colors.HexColor('#166534')

        verdict_badge_style = ParagraphStyle(
            'VerdictBadge',
            fontName=_REG_FONT_BOLD,
            fontSize=9.0,
            leading=11.5,
            textColor=badge_text_color
        )

        arch_table_data = [
            [Paragraph(t("auth_param"), bold_style), Paragraph(t("auth_result"), bold_style)],
            [Paragraph(t("auth_stick_adc"), body_style), Paragraph(f"<b>{auth.stick_adc_str}</b>", body_style)],
            [Paragraph(t("auth_trigger_adc"), body_style), Paragraph(f"<b>{auth.trigger_adc_str}</b>", body_style)],
            [Paragraph(t("auth_profile"), body_style), Paragraph(f"<b>{auth.archetype}</b>", body_style)],
            [Paragraph(t("auth_expected"), body_style), Paragraph(auth.expected_spec, body_style)],
            [Paragraph(t("auth_actual"), body_style), Paragraph(auth.actual_spec, body_style)],
            [Paragraph(t("auth_verdict"), bold_style), Paragraph(auth.verdict, verdict_badge_style)],
            [Paragraph(t("auth_conclusion"), body_style), Paragraph(auth.comment, body_style)],
        ]

        t_arch = Table(arch_table_data, colWidths=[140, avail_w - 140])
        t_arch.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('BACKGROUND', (1, 6), (1, 6), badge_bg),
        ]))
        elements.append(t_arch)

        elements.append(Spacer(1, 4))
        elements.append(Paragraph(t("pdf_footer_note"), footer_style))

        doc.build(elements)
        return True
    except Exception as e:
        LAST_PDF_ERROR = f"{type(e).__name__}: {str(e)}"
        print(f"[PDF] Generation error: {LAST_PDF_ERROR}")
        return False

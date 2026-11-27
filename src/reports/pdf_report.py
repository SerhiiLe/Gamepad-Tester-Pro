"""
Diagnostic PDF Report Generator
Generates a styled single-page A4 PDF report using Qt's native QPdfWriter + QTextDocument
with full Cyrillic, Latin, and symbol Unicode support via system fonts.
Supports bilingual Russian (RU) and English (EN) generation.
"""

import os
import time
import html
from typing import Dict, Any, Optional

from PySide6.QtGui import (
    QGuiApplication, QPdfWriter, QPageSize, QPageLayout, QTextDocument, QFont
)
from PySide6.QtCore import QMarginsF, QSizeF

from ..analysis.authenticity import analyze_authenticity

try:
    from ..i18n import i18n
except Exception:
    i18n = None


_FALLBACK_QT_APP: Optional[QGuiApplication] = None
LAST_PDF_ERROR: str = ""


def get_last_pdf_error() -> str:
    """Returns the most recent PDF generation error message."""
    global LAST_PDF_ERROR
    return LAST_PDF_ERROR


def _ensure_qt_app():
    """Ensures a QGuiApplication instance exists for QTextDocument font metrics."""
    global _FALLBACK_QT_APP
    if QGuiApplication.instance() is None:
        if (not os.environ.get("QT_QPA_PLATFORM")
                and not os.environ.get("DISPLAY")
                and not os.environ.get("WAYLAND_DISPLAY")):
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        _FALLBACK_QT_APP = QGuiApplication([])


def _build_report_html(
    t,
    is_en: bool,
    device_info: Dict[str, Any],
    polling_data: Dict[str, Any],
    buttons_data: Dict[str, Any],
    left_stick: Dict[str, Any],
    right_stick: Dict[str, Any],
    triggers_data: Dict[str, Any],
    auth,
    base_pt: float = 8.5,
) -> str:
    """Builds styled HTML for single-page A4 QTextDocument rendering."""
    h2_pt = base_pt + 2.0
    title_pt = base_pt + 7.0
    sub_pt = max(7.5, base_pt - 0.5)
    footer_pt = max(6.8, base_pt - 1.3)
    cell_pad = 3 if base_pt >= 8.0 else 2

    dev_name = html.escape(str(device_info.get('name', 'Unknown')))
    dev_path = html.escape(str(device_info.get('event_path', 'N/A')))
    dev_layout = html.escape(str(device_info.get('layout', 'Standard')))
    vid_pid = f"0x{device_info.get('vid', 0):04X} : 0x{device_info.get('pid', 0):04X}"

    # Overall Status Verdict
    has_chatter = buttons_data.get("status") != "PASS"
    has_snapback = (
        left_stick.get("snapback_flicks_x", 0) > 0
        or left_stick.get("snapback_flicks_y", 0) > 0
        or right_stick.get("snapback_flicks_x", 0) > 0
        or right_stick.get("snapback_flicks_y", 0) > 0
        or left_stick.get("snapback_count", 0) > 0
        or right_stick.get("snapback_count", 0) > 0
    )
    has_circ_err = (
        left_stick.get("circularity_error_pct", 0) > 8.0
        or right_stick.get("circularity_error_pct", 0) > 8.0
    )

    if not has_chatter and not has_snapback and not has_circ_err and not auth.is_replica:
        verdict_text = t("verdict_global_pass")
        bg_color = "#DCFCE7"
        border_color = "#16A34A"
        text_color = "#166534"
    else:
        verdict_text = t("verdict_global_fail")
        bg_color = "#FEF3C7"
        border_color = "#D97706"
        text_color = "#92400E"

    ls_gate = left_stick.get('gate_shape', '')
    is_ls_no_bezel = (
        "без безеля" in ls_gate.lower()
        or "квадрат" in ls_gate.lower()
        or "no bezel" in ls_gate.lower()
        or "square" in ls_gate.lower()
    )
    ls_bezel_tag = (" (no bezel)" if is_en else " (без безеля)") if is_ls_no_bezel else ""

    rs_gate = right_stick.get('gate_shape', '')
    is_rs_no_bezel = (
        "без безеля" in rs_gate.lower()
        or "квадрат" in rs_gate.lower()
        or "no bezel" in rs_gate.lower()
        or "square" in rs_gate.lower()
    )
    rs_bezel_tag = (" (no bezel)" if is_en else " (без безеля)") if is_rs_no_bezel else ""

    # Triggers summary line
    trig_strs = []
    for name, tr_item in triggers_data.items():
        safe_name = html.escape(str(name))
        trig_strs.append(
            f"<b>{safe_name}:</b> {tr_item.get('raw_max', 255)} ({tr_item.get('current_val_pct', 0):.1f}%)"
        )
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
        dedup=polling_data.get('dedup_packets', 0),
    )
    poll_verdict = (
        t("btn_ok")
        if polling_data.get("status") == "PASS"
        else ("<font color='#DC2626'><b>Jitter</b></font>" if is_en else "<font color='#DC2626'><b>Джиттер</b></font>")
    )

    # Buttons chatter & faulty buttons formatting
    faulty = buttons_data.get("faulty_buttons", [])
    if faulty:
        btn_details = t(
            "buttons_line_pdf_fail",
            total=buttons_data.get('total_buttons_tested', 0),
            chatter=buttons_data.get('total_chatter_events', 0),
            buttons=html.escape(', '.join(faulty)),
        )
        btn_verdict = f"<font color='#DC2626'><b>{t('btn_chatter_detected')}</b></font>"
    else:
        btn_details = t(
            "buttons_line_pdf_pass",
            total=buttons_data.get('total_buttons_tested', 0),
        )
        btn_verdict = t("btn_ok")

    pass_text = t("btn_ok")
    defect_text = "<font color='#DC2626'><b>" + ("Defect" if is_en else "Отклонение") + "</b></font>"

    ls_details = t(
        "stick_line_pdf",
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
        reach_y=left_stick.get('max_snapback_y_pct', 0),
    )
    rs_details = t(
        "stick_line_pdf",
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
        reach_y=right_stick.get('max_snapback_y_pct', 0),
    )

    badge_bg = "#FEF3C7" if auth.is_replica else "#DCFCE7"
    badge_text_color = "#92400E" if auth.is_replica else "#166534"

    return f"""
    <html>
    <head>
      <style>
        body {{
          font-family: "DejaVu Sans", "Liberation Sans", "Noto Sans", sans-serif;
          font-size: {base_pt}pt;
          color: #334155;
        }}
        h2 {{
          font-size: {h2_pt}pt;
          color: #0F172A;
          margin-top: 8px;
          margin-bottom: 3px;
        }}
        table.grid {{
          border-collapse: collapse;
          border: 1px solid #CBD5E1;
          font-size: {base_pt}pt;
        }}
        table.grid th, table.grid td {{
          border: 1px solid #CBD5E1;
          padding: {cell_pad}px 5px;
          vertical-align: middle;
        }}
        table.grid th {{
          background-color: #F1F5F9;
          color: #0F172A;
          font-weight: bold;
          text-align: left;
        }}
        .label-col {{
          color: #0F172A;
          font-weight: bold;
        }}
      </style>
    </head>
    <body>
      <div style="font-size: {title_pt}pt; font-weight: bold; color: #1E293B; margin-bottom: 2px;">
        {t("pdf_doc_title")}
      </div>
      <div style="font-size: {sub_pt}pt; color: #64748B; margin-bottom: 5px;">
        {t("pdf_doc_subtitle", date=time.strftime('%Y-%m-%d %H:%M:%S'))}
      </div>

      <hr style="background-color: #0284C7; height: 2px; border: none; margin-bottom: 7px;" />

      <!-- Device Info Table -->
      <table width="100%" cellspacing="0" cellpadding="{cell_pad}" class="grid">
        <tr>
          <th width="28%">{t("param_label")}</th>
          <th width="72%">{t("value_label")}</th>
        </tr>
        <tr><td>{t("dev_model")}</td><td>{dev_name}</td></tr>
        <tr><td>{t("dev_vid_pid")}</td><td>{vid_pid}</td></tr>
        <tr><td>{t("dev_interface")}</td><td>{dev_path}</td></tr>
        <tr><td>{t("dev_layout")}</td><td>{dev_layout}</td></tr>
      </table>

      <!-- Global Verdict Banner -->
      <table width="100%" cellspacing="0" cellpadding="5" style="margin-top: 7px; margin-bottom: 4px; border: 1px solid {border_color}; background-color: {bg_color};">
        <tr>
          <td style="font-size: {base_pt + 1.0}pt; font-weight: bold; color: {text_color};">
            {verdict_text}
          </td>
        </tr>
      </table>

      <!-- Node Test Results -->
      <h2>{t("sec_node_results")}</h2>
      <table width="100%" cellspacing="0" cellpadding="{cell_pad}" class="grid">
        <tr>
          <th width="22%">{t("node_label")}</th>
          <th width="62%">{t("metrics_label")}</th>
          <th width="16%">{t("verdict_label")}</th>
        </tr>
        <tr>
          <td class="label-col">{t("node_polling")}</td>
          <td>{poll_details}</td>
          <td>{poll_verdict}</td>
        </tr>
        <tr>
          <td class="label-col">{t("node_buttons")}</td>
          <td>{btn_details}</td>
          <td>{btn_verdict}</td>
        </tr>
        <tr>
          <td class="label-col">{t("node_stick_l")}</td>
          <td>{ls_details}</td>
          <td>{pass_text if left_stick.get("status") == "PASS" else defect_text}</td>
        </tr>
        <tr>
          <td class="label-col">{t("node_stick_r")}</td>
          <td>{rs_details}</td>
          <td>{pass_text if right_stick.get("status") == "PASS" else defect_text}</td>
        </tr>
        <tr>
          <td class="label-col">{t("node_triggers")}</td>
          <td>{trig_display}</td>
          <td>{pass_text}</td>
        </tr>
      </table>

      <!-- Hardware Architecture & Authenticity -->
      <h2>{t("sec_authenticity")}</h2>
      <table width="100%" cellspacing="0" cellpadding="{cell_pad}" class="grid">
        <tr>
          <th width="28%">{t("auth_param")}</th>
          <th width="72%">{t("auth_result")}</th>
        </tr>
        <tr><td>{t("auth_stick_adc")}</td><td><b>{html.escape(auth.stick_adc_str)}</b></td></tr>
        <tr><td>{t("auth_trigger_adc")}</td><td><b>{html.escape(auth.trigger_adc_str)}</b></td></tr>
        <tr><td>{t("auth_profile")}</td><td><b>{html.escape(auth.archetype)}</b></td></tr>
        <tr><td>{t("auth_expected")}</td><td>{html.escape(auth.expected_spec)}</td></tr>
        <tr><td>{t("auth_actual")}</td><td>{html.escape(auth.actual_spec)}</td></tr>
        <tr>
          <td class="label-col">{t("auth_verdict")}</td>
          <td bgcolor="{badge_bg}" style="color: {badge_text_color}; font-weight: bold;">{html.escape(auth.verdict)}</td>
        </tr>
        <tr><td>{t("auth_conclusion")}</td><td>{html.escape(auth.comment)}</td></tr>
      </table>

      <div style="font-size: {footer_pt}pt; color: #64748B; margin-top: 7px;">
        {t("pdf_footer_note")}
      </div>
    </body>
    </html>
    """


def generate_pdf_report(
    output_filepath: str,
    device_info: Dict[str, Any],
    polling_data: Dict[str, Any],
    buttons_data: Dict[str, Any],
    left_stick: Dict[str, Any],
    right_stick: Dict[str, Any],
    triggers_data: Dict[str, Any],
    lang: Optional[str] = None,
) -> bool:
    """Generates a diagnostic PDF report fitted onto a single A4 page in RU or EN."""
    global LAST_PDF_ERROR
    LAST_PDF_ERROR = ""

    if lang is None and i18n is not None:
        lang = i18n.current_lang
    is_en = (str(lang).upper() == "EN")

    def t(key: str, **kwargs) -> str:
        if i18n is not None:
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

    # Check write access to destination path before building document
    try:
        with open(output_filepath, 'a' if os.path.exists(output_filepath) else 'w'):
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

    try:
        _ensure_qt_app()
        auth = analyze_authenticity(device_info, left_stick, right_stick, triggers_data, lang=lang)

        writer = QPdfWriter(output_filepath)
        page_layout = QPageLayout(
            QPageSize(QPageSize.A4),
            QPageLayout.Portrait,
            QMarginsF(12.0, 10.0, 12.0, 10.0),
            QPageLayout.Millimeter,
        )
        writer.setPageLayout(page_layout)
        writer.setTitle(t("pdf_doc_title"))
        writer.setCreator("Gamepad Tester Pro")

        paint_rect = writer.pageLayout().paintRectPixels(96)
        doc_size = QSizeF(paint_rect.width(), paint_rect.height())

        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setPageSize(doc_size)

        # Fit strictly onto 1 A4 page by stepping down base font size if content overflows
        for pt in (8.5, 8.0, 7.5, 7.0):
            doc.setDefaultFont(QFont("Sans Serif", int(pt)))
            html_str = _build_report_html(
                t=t,
                is_en=is_en,
                device_info=device_info,
                polling_data=polling_data,
                buttons_data=buttons_data,
                left_stick=left_stick,
                right_stick=right_stick,
                triggers_data=triggers_data,
                auth=auth,
                base_pt=pt,
            )
            doc.setHtml(html_str)
            if doc.pageCount() <= 1:
                break

        doc.print_(writer)
        return True
    except Exception as e:
        LAST_PDF_ERROR = f"{type(e).__name__}: {str(e)}"
        print(f"[PDF] Generation error: {LAST_PDF_ERROR}")
        return False

"""
English Localization Dictionary for Gamepad Tester Pro
"""

TRANSLATIONS = {
    # -------------------------------------------------------------------------
    # Main Window & Navigation
    # -------------------------------------------------------------------------
    "app_title": "Gamepad Tester Pro — Comprehensive Controller Diagnostics",
    "lbl_controller": "<b>Controller:</b>",
    "btn_rescan": "↻ Rescan Devices",
    "lbl_layout": "<b>Layout:</b>",
    "lbl_battery_charging": "🔋 Battery: {cap}% (Charging)",
    "lbl_battery_discharging": "🔋 Battery: {cap}% (Discharging)",
    "lbl_battery_full": "🔋 Battery: {cap}% (Full)",
    "lbl_battery_unknown": "🔋 Battery: —",
    "lbl_power_usb": "🔌 Power: USB (Wired)",
    "no_controllers_found": "No controllers detected",

    # Tabs
    "tab_sticks": "🎯 Sticks & Triggers",
    "tab_buttons": "🔘 Buttons & Chatter (<7ms)",
    "tab_polling": "⚡ Polling Rate (Hz)",
    "tab_feedback": "📳 Rumble & LEDs",
    "tab_report": "📋 Passport / Report",

    # -------------------------------------------------------------------------
    # Sticks & Oscilloscope
    # -------------------------------------------------------------------------
    "stick_left_name": "Left Stick (LS)",
    "stick_right_name": "Right Stick (RS)",
    "stage_free": "Free Run",
    "stage_center": "1: Center",
    "stage_circle": "2: Circularity",
    "stage_targets": "3: Target Hold (Noise)",
    "stage_snapback": "4: Snapback",
    "btn_reset": "Reset",

    "hint_free": "💡 Free run (ADC measurement)",
    "hint_center": "🎯 Release stick to center",
    "hint_center_done": "✅ Test passed (drift: {drift:.1f}%)",
    "hint_circle": "🔄 Rotate stick along outer border",
    "hint_circle_done": "✅ Test passed (error: {circ:.1f}%)",
    "hint_targets": "💡 Hold stick inside target circle",
    "hint_targets_move": "🎯 Target hold: {zone}",
    "hint_targets_settling": "⏳ Settling: {zone}",
    "hint_targets_measuring": "🎯 Measuring: {zone}",
    "hint_targets_done": "✅ Test passed (noise: {noise:.2f}%)",
    "hint_snapback_x": "⚡ 1. Flick horizontally and release",
    "hint_snapback_y": "⚡ 2. Flick vertically and release",
    "hint_snapback_done": "✅ Test passed (Snapback: X {x_rate}%, Y {y_rate}%)",

    "metric_adc": "ADC",
    "metric_bit": "bit",
    "metric_step": "step",
    "metric_adc_hint": "rotate stick...",
    "metric_center": "Center",
    "metric_coverage": "Coverage",
    "metric_error": "Error",
    "metric_noise": "Noise",
    "metric_flicks": "Flicks",
    "metric_peak": "Peak",

    "zone_north": "North (Up)",
    "zone_east": "East (Right)",
    "zone_south": "South (Down)",
    "zone_west": "West (Left)",

    "snapback_box_title": "Motion Waveform: {title} (~100 ms)",
    "snapback_peak_label": "Peak Snapback: <b>{peak:.1f}%</b>",
    "snapback_axis_y": "Coord.",
    "snapback_axis_x": "Time (~100 ms / samples)",

    # -------------------------------------------------------------------------
    # Anomalies Summary Table
    # -------------------------------------------------------------------------
    "anomalies_box_title": "Stick Anomalies & Defects Summary (X/Y Axes)",
    "col_param_check": "Check Parameter",
    "col_ls_left": "LS (Left)",
    "col_rs_right": "RS (Right)",
    "col_tolerance": "Tolerance",

    "cell_not_tested": "Not tested",
    "cell_waiting_tests": "Waiting for tests",
    "cell_pass": "✅ PASS",
    "cell_defect": "⚠️ DEFECT",

    # Row definitions (name, tol, tooltip)
    "anom_row0_name": "Center Drift (Axis X)",
    "anom_row0_tol": "< 5.0%",
    "anom_row0_tip": "<b>Zero drift along horizontal axis X:</b><br>Stick resting offset left/right.<br><i>Tolerance:</i> under 5.0%.<br><i>Measured in:</i> Stage 1 (Center).<br><b>Cause:</b> potentiometer X track wear or ADC zero calibration offset.",

    "anom_row1_name": "Center Drift (Axis Y)",
    "anom_row1_tol": "< 5.0%",
    "anom_row1_tip": "<b>Zero drift along vertical axis Y:</b><br>Stick resting offset up/down.<br><i>Tolerance:</i> under 5.0%.<br><i>Measured in:</i> Stage 1 (Center).<br><b>Cause:</b> potentiometer Y track wear or ADC zero calibration offset.",

    "anom_row2_name": "Circularity Error (360°)",
    "anom_row2_tol": "< 8.0%",
    "anom_row2_tip": "<b>Circularity Error:</b><br>Stick physical boundary deviation from an ideal circle (R=1.0).<br><i>Tolerance (with bezel):</i> under 8.0%.<br><i>Square gate (no bezel):</i> normal ~18–22%.<br><i>Measured in:</i> Stage 2 (Circularity).",

    "anom_row3_name": "Potentiometer Noise X",
    "anom_row3_tol": "< 1.50%",
    "anom_row3_tip": "<b>Noise & jitter amplitude along axis X:</b><br>Hall sensor fluctuations or potentiometer X resistive wear when holding stick.<br><i>Tolerance:</i> under 1.50%.<br><i>Measured in:</i> Stage 3 (Target Hold).",

    "anom_row4_name": "Potentiometer Noise Y",
    "anom_row4_tol": "< 1.50%",
    "anom_row4_tip": "<b>Noise & jitter amplitude along axis Y:</b><br>Hall sensor fluctuations or potentiometer Y resistive wear when holding stick.<br><i>Tolerance:</i> under 1.50%.<br><i>Measured in:</i> Stage 3 (Target Hold).",

    "anom_row5_name": "Snapback (Axis X)",
    "anom_row5_tol": "< 5.0%",
    "anom_row5_tip": "<b>Horizontal Snapback Amplitude (Axis X):</b><br>Zero overshoot left/right when rapidly releasing horizontal deflection.<br><i>Tolerance:</i> under 5.0%.<br><i>Measured in:</i> Stage 4 (Snapback).",

    "anom_row6_name": "Snapback (Axis Y)",
    "anom_row6_tol": "< 5.0%",
    "anom_row6_tip": "<b>Vertical Snapback Amplitude (Axis Y):</b><br>Zero overshoot up/down when rapidly releasing vertical deflection.<br><i>Tolerance:</i> under 5.0%.<br><i>Measured in:</i> Stage 4 (Snapback).",

    "anom_row7_name": "Snapback Rate",
    "anom_row7_tol": "< 10.0%",
    "anom_row7_tip": "<b>Snapback Rate:</b><br>Percentage of quick stick flicks that caused parasitic zero overshoot (> 5.0%).<br><i>Tolerance:</i> up to 10.0% (normal: 0%).",

    "anom_row8_name": "Overall Verdict",
    "anom_row8_tol": "—",
    "anom_row8_tip": "<b>Comprehensive stick health assessment:</b><br>Calculated based on results of all testing stages.",

    # -------------------------------------------------------------------------
    # Triggers
    # -------------------------------------------------------------------------
    "triggers_box_title": "Triggers",
    "trigger_lt_name": "<b>LT/L2</b>",
    "trigger_rt_name": "<b>RT/R2</b>",

    # -------------------------------------------------------------------------
    # Buttons & Debounce Table
    # -------------------------------------------------------------------------
    "buttons_title": "<b>Button, D-Pad Testing & Contact Chatter (&lt; 7 ms) Detection</b>",
    "btn_clear_counters": "Reset Counters",
    "col_btn_code": "Code (Hex / Dec)",
    "col_btn_name": "Button Name",
    "col_btn_state": "State",
    "col_btn_presses": "Presses",
    "col_btn_chatter": "Chatter (<7ms)",
    "col_btn_min_dt": "Min Interval",
    "chatter_log_title": "<b>Chatter Event Log (False / Repeated triggers &lt; 7 ms):</b>",

    "state_pressed": "Pressed",
    "state_released": "Released",
    "btn_ok": "OK",
    "btn_chatter_detected": "Chatter!",

    # -------------------------------------------------------------------------
    # Polling Rate & Bus Stability
    # -------------------------------------------------------------------------
    "polling_title": "<b>Polling Rate and Bus Stability</b>",
    "btn_reset_stats": "Reset Statistics",
    "axis_polling_dt": "Inter-packet interval Δt (ms)",
    "axis_polling_idx": "Polling packet index (bus history)",
    "polling_stats_fmt": "Interval dt: {dt:.2f} ms | Jitter (StdDev): {jitter:.3f} ms | Packets: {packets}",
    "polling_bus": "Bus:",
    "polling_jitter": "Jitter:",
    "polling_channel": "Channel:",
    "polling_conn_wireless": "Wireless",
    "polling_conn_wired": "Wired USB",
    "polling_dedup": "Deduped:",
    "polling_drops_excluded": "Drops excluded",
    "polling_drops": "Drops:",
    "polling_note": "ℹ️ <b>Bus Stability:</b> Rotate sticks in circles to measure active polling frequency. For wired gamepads, OS kernel packet deduplication is normal (not frame drop). Oscilloscope shows aligned bus intervals and true hardware jitter.",

    # -------------------------------------------------------------------------
    # Rumble & Actuators
    # -------------------------------------------------------------------------
    "rumble_group_title": "Force Feedback / Rumble Actuator Testing",
    "lbl_left_motor": "Left Motor (Heavy / Low Freq):",
    "lbl_right_motor": "Right Motor (Light / High Freq):",
    "btn_pulse_left": "🔴 Pulse Left (1s)",
    "btn_pulse_right": "🔵 Pulse Right (1s)",
    "btn_pulse_both": "🟣 Pulse Both (1s)",
    "btn_stop_rumble": "⏹ Stop",

    "ff_no_device": "⚠️ <b>No controller selected:</b> Connect a gamepad to test rumble motors.",
    "ff_unsupported": "⚠️ <b>Attention:</b> Connected device does not support hardware Force Feedback (rumble actuator descriptor missing in HID). Vibration commands unavailable.",
    "ff_supported": "✅ <b>Force Feedback supported:</b> Active rumble driver detected (EV_FF / Force Feedback). You can test left (heavy/low freq) and right (light/high freq) motors independently.",

    # -------------------------------------------------------------------------
    # LED & Indication
    # -------------------------------------------------------------------------
    "led_group_title": "LED & Lighting Control (Dedicated Commands)",
    "tab_led_info": "ℹ️ Technology & Compatibility",
    "tab_led_sony": "🎮 Sony PlayStation (RGB Lightbar)",
    "tab_led_xbox": "🎮 Microsoft Xbox (Ring of Light)",

    "lbl_sony_desc": "<b>Sony DualSense (PS5) & DualShock 4 (PS4) Lightbar:</b>",
    "lbl_presets": "Presets:",
    "btn_apply_rgb": "Apply RGB",

    "lbl_xbox_desc": "<b>Microsoft Xbox 360 Ring of Light:</b>",
    "lbl_players": "Players:",
    "lbl_modes": "Modes:",
    "player_1": "1️⃣ Player 1",
    "player_2": "2️⃣ Player 2",
    "player_3": "3️⃣ Player 3",
    "player_4": "4️⃣ Player 4",
    "player_off": "⚫ Off",
    "mode_rotate": "🔄 Rotate",
    "mode_fast_blink": "⚡ Fast Blink",
    "mode_slow_blink": "⏳ Slow",
    "mode_alternating": "🔀 Alternating",

    "lbl_xbox_root_notice": (
        "⚠️ <b>Notice (Linux Permissions):</b> Control over xpad Ring of Light is performed via sysfs "
        "(<code>/sys/class/leds/xpad*/brightness</code>). In Linux, writing to this node requires <b>root privileges</b> by default.<br><br>"
        "If controller does not respond to quadrant or animation commands:<br>"
        "• Run app with <code>sudo</code>, or<br>"
        "• Grant write permission once via terminal:<br>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<code>sudo chmod 666 /sys/class/leds/xpad*/brightness</code><br>"
        "• Or create a permanent udev rule for non-root access."
    ),

    "led_info_html": """
    <div style="font-family: 'Segoe UI', 'Ubuntu', 'Roboto', sans-serif;">
      <h3 style="color: #38BDF8; margin-top: 0px; margin-bottom: 6px;">ℹ️ Hardware LED Lighting Support in Linux</h3>
      <p style="color: #CBD5E1; font-size: 13px; line-height: 1.45; margin-bottom: 12px;">
        Unlike standard buttons and axes, programmatic LED control is not standardized in base USB HID.
        It is supported by the Linux kernel only for specialized official platforms with dedicated drivers:
      </p>

      <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom: 10px; background-color: #1E293B; border: 1px solid #334155; border-radius: 6px;">
        <tr>
          <td>
            <b style="color: #38BDF8; font-size: 13px;">🎮 Sony PlayStation — Full-Color RGB Lightbar</b><br/>
            <span style="color: #94A3B8; font-size: 12px; line-height: 1.45;">
              • <b>DualSense (PS5):</b> Individual RGB touchpad contour and player LEDs (<code>hid-playstation</code> kernel driver). Supports direct HID output reports (<code>0x02</code> / <code>0x31</code>) and sysfs.<br/>
              • <b>DualShock 4 (PS4):</b> RGB Lightbar strip (<code>hid-sony</code> or <code>hid-playstation</code> driver).
            </span>
          </td>
        </tr>
      </table>

      <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom: 10px; background-color: #1E293B; border: 1px solid #334155; border-radius: 6px;">
        <tr>
          <td>
            <b style="color: #10B981; font-size: 13px;">🎮 Microsoft Xbox — Ring of Light</b><br/>
            <span style="color: #94A3B8; font-size: 12px; line-height: 1.45;">
              • <b>Xbox 360 Controller (wired and wireless with receiver):</b> 4-segment player quadrant ring and system animations (rotation, blink, alternating) via <code>xpad</code> sysfs (<code>/sys/class/leds/xpad*/brightness</code>). <i>Requires root or udev rule.</i><br/>
              • <b>Xbox One / Series:</b> Xbox guide button stays solid white and is not programmatically controlled via open driver.
            </span>
          </td>
        </tr>
      </table>

      <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom: 6px; background-color: #1E293B; border: 1px solid #334155; border-radius: 6px;">
        <tr>
          <td>
            <b style="color: #F59E0B; font-size: 13px;">❌ Other Controllers (Unsupported by OS)</b><br/>
            <span style="color: #94A3B8; font-size: 12px; line-height: 1.45;">
              • <b>Nintendo Switch Pro / Joy-Con:</b> Home button LED ring requires proprietary vendor subcommands in <code>hid-nintendo</code>.<br/>
              • <b>Third-party gamepads (Flydigi, 8BitDo, Gamesir, Defender, replicas):</b> Decorative lighting is managed by on-board MCU (hardware button combos) without OS API.<br/>
              • <b>Standard DInput / Generic USB gamepads:</b> LED controls are absent from the HID descriptor.
            </span>
          </td>
        </tr>
      </table>
    </div>
    """,

    # -------------------------------------------------------------------------
    # Diagnostic Report & Passport (UI, Text & PDF)
    # -------------------------------------------------------------------------
    "report_header_title": "<b>Gamepad Technical Passport and Diagnostic Report</b>",
    "btn_refresh_report": "Refresh Data",
    "btn_copy_clipboard": "Copy to Clipboard",
    "btn_export_pdf": "📄 Export to PDF",
    "btn_export_txt": "💾 Save .txt",
    "pdf_export_success": "PDF passport successfully saved to file:\n{path}",
    "txt_export_success": "Text report successfully saved to file:\n{path}",
    "pdf_export_error": "Error generating PDF report:\n{err}",
    "report_copied_notice": "Report successfully copied to clipboard!",

    # Report Sections & Fields
    "pdf_doc_title": "🎮 Gamepad Technical Condition Passport",
    "pdf_doc_subtitle": "Inspection Date: {date} | Suite: Gamepad Tester Pro 2.0",
    "sec_device_info": "Device Information",
    "sec_node_results": "Hardware Subsystem Test Results",
    "sec_authenticity": "Hardware Architecture and Authenticity",
    "param_label": "Parameter",
    "value_label": "Value",
    "node_label": "Subsystem / Test",
    "metrics_label": "Measured Parameters",
    "verdict_label": "Verdict",

    "dev_model": "Device Model",
    "dev_vid_pid": "Identifier (VID / PID)",
    "dev_interface": "Connection Interface",
    "dev_layout": "Profile Layout",

    "verdict_global_pass": "OVERALL STATUS: ALL TESTS PASSED SUCCESSFULLY (NORMAL)",
    "verdict_global_fail": "OVERALL STATUS: ANOMALIES OR DEFECTS DETECTED",

    "node_polling": "Bus & Polling",
    "node_buttons": "Buttons (Chatter)",
    "node_stick_l": "Left Stick",
    "node_stick_r": "Right Stick",
    "node_triggers": "Triggers",

    "polling_line_pdf": "Rate: <b>{hz} Hz</b> (nominal ~{target_hz} Hz) | Jitter: <b>{jitter} ms</b><br/>Type: {conn} | {drops} | Kernel deduped: {dedup}",
    "buttons_line_pdf_pass": "Tested: {total} | Chatter (&lt; 7 ms): <b>0</b> (None detected)",
    "buttons_line_pdf_fail": "Tested: {total} | Chatter (&lt; 7 ms): <b>{chatter}</b><br/><font color='#DC2626'>⚠️ <b>Chattering buttons:</b> {buttons}</font>",
    "stick_line_pdf": "Circularity error: <b>{circ:.1f}%</b>{bezel} | Noise: <b>{jitter:.2f}%</b><br/>Snapback X: <b>{rate_x:.0f}%</b> ({flicks_x}/{total_x}, overshoot {reach_x:.1f}%) | Snapback Y: <b>{rate_y:.0f}%</b> ({flicks_y}/{total_y}, overshoot {reach_y:.1f}%)",

    "pdf_footer_note": "Report generated by Gamepad Tester Pro diagnostic software. Designed for quality inspection, hardware repair, and verification of Hall effect sensors, potentiometers, and controller platforms.",

    # Authenticity Labels
    "auth_param": "Platform Parameter",
    "auth_result": "Specification & Verification Result",
    "auth_stick_adc": "Estimated Stick ADC",
    "auth_trigger_adc": "Estimated Trigger ADC",
    "auth_profile": "Platform Profile",
    "auth_expected": "Expected by Specification",
    "auth_actual": "Actually Detected",
    "auth_verdict": "Authenticity Verdict",
    "auth_conclusion": "Expert Conclusion",

    # Text report headers
    "txt_rep_title": "GAMEPAD TECHNICAL PASSPORT",
    "txt_rep_date": "Inspection Date:",
    "txt_rep_dev": "Device:",
    "txt_rep_id": "Identifier:",
    "txt_rep_iface": "Interface:",
    "txt_rep_layout": "Detected Layout:",
    "txt_rep_verdict": "OVERALL VERDICT:",
    "txt_rep_verdict_pass": "✅ ALL TESTS PASSED (NORMAL)",
    "txt_rep_verdict_fail": "⚠️ ANOMALIES / DEFECTS DETECTED",
    "txt_rep_sec1": "1. POLLING RATE AND BUS TIMING STABILITY",
    "txt_rep_sec2": "2. BUTTONS AND CONTACT CHATTER (DEBOUNCE / CHATTER)",
    "txt_rep_sec3": "3. LEFT ANALOG STICK",
    "txt_rep_sec4": "4. RIGHT ANALOG STICK",
    "txt_rep_sec5": "5. ANALOG TRIGGERS",
    "txt_rep_sec6": "6. ESTIMATED ARCHITECTURE AND AUTHENTICITY",
    "txt_rep_sec7": "7. DETECTED ISSUES AND RECOMMENDATIONS:",
}

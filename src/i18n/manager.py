"""
Internationalization (i18n) Manager for Gamepad Tester Pro
Manages active language (RU / EN), automatic system locale detection,
and localized string retrieval.
"""

import os
import locale
from typing import Dict, Any, Callable, List

from .ru import TRANSLATIONS as RU_STRINGS
from .en import TRANSLATIONS as EN_STRINGS


def detect_system_language() -> str:
    """
    Detects system language.
    Rule: ru_*, ua_*, uk_* -> RU, anything else -> EN.
    Priority order:
    1. Environment variables (LC_ALL, LC_MESSAGES, LANG, LANGUAGE)
    2. Python locale.getdefaultlocale()
    3. PySide6 QLocale.system().name()
    """
    candidates = []
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var)
        if val:
            candidates.append(val)
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            candidates.append(loc)
    except Exception:
        pass
    try:
        from PySide6.QtCore import QLocale
        candidates.append(QLocale.system().name())
    except Exception:
        pass

    for c in candidates:
        if not c:
            continue
        low = c.strip().lower()
        if low.startswith("ru") or low.startswith("ua") or low.startswith("uk"):
            return "RU"
        else:
            return "EN"

    return "EN"


class I18nManager:
    """Central localization manager."""

    SUPPORTED_LANGUAGES = ["RU", "EN"]

    def __init__(self, initial_lang: str = None):
        if initial_lang and initial_lang.upper() in self.SUPPORTED_LANGUAGES:
            self._current_lang = initial_lang.upper()
        else:
            self._current_lang = detect_system_language()

        self._bundles = {
            "RU": RU_STRINGS,
            "EN": EN_STRINGS,
        }
        self._listeners: List[Callable[[str], None]] = []

    @property
    def current_lang(self) -> str:
        return self._current_lang

    def set_language(self, lang: str):
        lang = lang.upper()
        if lang not in self.SUPPORTED_LANGUAGES:
            lang = "EN"
        if self._current_lang != lang:
            self._current_lang = lang
            for cb in list(self._listeners):
                try:
                    cb(self._current_lang)
                except Exception as e:
                    print(f"[i18n] Error in language listener callback: {e}")

    def subscribe(self, callback: Callable[[str], None]):
        """Registers a callback when language changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[str], None]):
        """Unregisters a language change callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def tr(self, key: str, **kwargs) -> str:
        """Retrieves localized string for key in current language."""
        bundle = self._bundles.get(self._current_lang, EN_STRINGS)
        text = bundle.get(key)
        if text is None:
            # Fallback to English, then to key itself
            text = EN_STRINGS.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# Global Singleton Instance
i18n = I18nManager()


def tr(key: str, **kwargs) -> str:
    """Convenience helper function for i18n.tr."""
    return i18n.tr(key, **kwargs)

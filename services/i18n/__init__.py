"""
i18n package — per-language string files loaded here.

Public API (unchanged):
    from services.i18n import get as t
    t(lang, key, **kwargs) -> str

To add a new language:
  1. Create services/i18n/<code>.py with a STRINGS dict.
  2. Import it below and add it to STRINGS.
  3. Add the language choice to setup_cog.py and config.py.

To add a new key:
  - Add it to en.py first (source of truth).
  - Add translations to each other language file.
  - Any missing key falls back to English automatically.
"""

import random

from services.i18n import en, ja, es, de, hi, pl, fr

STRINGS: dict[str, dict] = {
    "en": en.STRINGS,
    "ja": ja.STRINGS,
    "es": es.STRINGS,
    "de": de.STRINGS,
    "hi": hi.STRINGS,
    "pl": pl.STRINGS,
    "fr": fr.STRINGS,
}


def get(lang: str, key: str, **kwargs) -> str:
    """
    Return the localised string for `key` in `lang`.
    Falls back to English if the key is missing in the requested language.
    If the value is a list, a random item is chosen each call.
    """
    lang_strings = STRINGS.get(lang) or STRINGS["en"]
    value = lang_strings.get(key) or STRINGS["en"].get(key, f"[{key}]")

    if isinstance(value, list):
        value = random.choice(value)

    if kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass

    return value

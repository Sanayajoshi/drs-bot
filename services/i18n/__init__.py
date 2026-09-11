"""
i18n package — per-language string files loaded here with database override caching.

Public API:
    from services.i18n import get as t
    t(lang, key, **kwargs) -> str

To add a new language:
  1. Create services/i18n/<code>.py with a STRINGS dict.
  2. Import it below and add it to STRINGS.
  3. Add the language choice to setup_cog.py and config.py.
"""

import random
import re
import logging
from typing import Any

from services.i18n import en, ja, es, de, hi, pl, fr

logger = logging.getLogger("drs.i18n")

STRINGS: dict[str, dict] = {
    "en": en.STRINGS,
    "ja": ja.STRINGS,
    "es": es.STRINGS,
    "de": de.STRINGS,
    "hi": hi.STRINGS,
    "pl": pl.STRINGS,
    "fr": fr.STRINGS,
}

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "ja": "日本語 (Japanese)",
    "es": "Español (Spanish)",
    "de": "Deutsch (German)",
    "hi": "हिन्दी (Hindi)",
    "pl": "Polski (Polish)",
    "fr": "Français (French)",
}

# In-memory cache for dynamic DB overrides / variations: {lang: {msg_key: [texts]}}
_DB_STRINGS: dict[str, dict[str, list[str]]] = {}


def sync_from_db(db_ops) -> int:
    """Load active translations from the database table into memory cache."""
    global _DB_STRINGS
    try:
        msgs = db_ops.get_all_i18n_messages()
        if msgs:
            _DB_STRINGS = msgs
            total = sum(len(v) for lang_dict in msgs.values() for v in lang_dict.values())
            logger.info(f"Loaded {total} translation variations from database into memory cache.")
            return total
    except Exception as e:
        logger.error(f"Failed to sync translations from database: {e}", exc_info=True)
    return 0


class _SafeFormatDict(dict):
    """Dictionary that returns an empty string or the key itself for missing keys."""
    def __missing__(self, key):
        return ""


def get(lang: str, key: str, **kwargs: Any) -> str:
    """
    Return the localised string for `key` in `lang`.
    Priority:
      1. DB translations for requested `lang`
      2. File translations for requested `lang`
      3. DB translations for `en` (fallback)
      4. File translations for `en` (source of truth)
    If the value is a list, a random item is chosen each call.
    Safely formats kwargs and cleans extra spacing.
    """
    if not lang:
        lang = "en"
    lang = lang.lower()

    # 1. DB requested language
    value = _DB_STRINGS.get(lang, {}).get(key)
    # 2. File requested language
    if not value:
        value = STRINGS.get(lang, {}).get(key)
    # 3. DB English fallback
    if not value:
        value = _DB_STRINGS.get("en", {}).get(key)
    # 4. File English fallback
    if not value:
        value = STRINGS.get("en", {}).get(key, f"[{key}]")

    if isinstance(value, list):
        value = random.choice(value) if value else f"[{key}]"

    if kwargs:
        try:
            # Map synonyms: pilot / name
            safe_kwargs = _SafeFormatDict(kwargs)
            if "pilot" in kwargs and "name" not in kwargs:
                safe_kwargs["name"] = kwargs["pilot"]
            elif "name" in kwargs and "pilot" not in kwargs:
                safe_kwargs["pilot"] = kwargs["name"]

            # Map queue / level
            if "queue" in kwargs and "level" not in kwargs:
                safe_kwargs["level"] = kwargs["queue"]
            if "queues" in kwargs and "levels" not in kwargs:
                safe_kwargs["levels"] = kwargs["queues"]

            value = str(value).format_map(safe_kwargs)
        except Exception as e:
            logger.warning(f"Error formatting translation key {key} for lang {lang}: {e}")

    # Clean double spaces if icon was empty
    value = re.sub(r"[ \t]{2,}", " ", value).strip()
    return value


# Alias
t = get

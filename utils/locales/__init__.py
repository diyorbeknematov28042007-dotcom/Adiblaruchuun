"""Tarjimalar yuklovchi."""
from . import uz, ru, en

_LOCALES = {
    "uz": uz.T,
    "ru": ru.T,
    "en": en.T,
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """Tarjima olish. Agar kalit topilmasa, uz versiyasini qaytaradi."""
    locale = _LOCALES.get(lang, _LOCALES["uz"])
    val = locale.get(key) or _LOCALES["uz"].get(key) or key
    if isinstance(val, str) and kwargs:
        try:
            return val.format(**kwargs)
        except (KeyError, IndexError):
            return val
    return val


def get_locale(lang: str) -> dict:
    return _LOCALES.get(lang, _LOCALES["uz"])

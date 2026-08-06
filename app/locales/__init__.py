from app.locales import ar, en, fr

_LOCALES = {"ar": ar.STRINGS, "en": en.STRINGS, "fr": fr.STRINGS}

SUPPORTED_LANGUAGES = ["ar", "en", "fr"]


def t(lang: str | None, key: str, **kwargs) -> str:
    lang = lang if lang in _LOCALES else "ar"
    template = _LOCALES[lang].get(key) or _LOCALES["ar"].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template

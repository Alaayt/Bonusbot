"""قائمة الدول العربية المدعومة افتراضيًا. يمكن للمدير إضافة دول جديدة من لوحة الإدارة (جدول admin_countries في قاعدة البيانات)."""

DEFAULT_SUPPORTED_COUNTRIES = {
    "IQ": {"ar": "العراق", "en": "Iraq", "fr": "Irak"},
    "EG": {"ar": "مصر", "en": "Egypt", "fr": "Égypte"},
    "DZ": {"ar": "الجزائر", "en": "Algeria", "fr": "Algérie"},
    "MA": {"ar": "المغرب", "en": "Morocco", "fr": "Maroc"},
    "TN": {"ar": "تونس", "en": "Tunisia", "fr": "Tunisie"},
    "LY": {"ar": "ليبيا", "en": "Libya", "fr": "Libye"},
    "MR": {"ar": "موريتانيا", "en": "Mauritania", "fr": "Mauritanie"},
    "SA": {"ar": "السعودية", "en": "Saudi Arabia", "fr": "Arabie saoudite"},
    "AE": {"ar": "الإمارات", "en": "UAE", "fr": "Émirats arabes unis"},
    "QA": {"ar": "قطر", "en": "Qatar", "fr": "Qatar"},
    "KW": {"ar": "الكويت", "en": "Kuwait", "fr": "Koweït"},
    "BH": {"ar": "البحرين", "en": "Bahrain", "fr": "Bahreïn"},
    "OM": {"ar": "عُمان", "en": "Oman", "fr": "Oman"},
    "JO": {"ar": "الأردن", "en": "Jordan", "fr": "Jordanie"},
    "LB": {"ar": "لبنان", "en": "Lebanon", "fr": "Liban"},
    "PS": {"ar": "فلسطين", "en": "Palestine", "fr": "Palestine"},
    "YE": {"ar": "اليمن", "en": "Yemen", "fr": "Yémen"},
    "SD": {"ar": "السودان", "en": "Sudan", "fr": "Soudan"},
    "SO": {"ar": "الصومال", "en": "Somalia", "fr": "Somalie"},
    "OTHER": {"ar": "دولة أخرى", "en": "Other country", "fr": "Autre pays"},
}


def country_name(code: str, lang: str) -> str:
    entry = DEFAULT_SUPPORTED_COUNTRIES.get(code, DEFAULT_SUPPORTED_COUNTRIES["OTHER"])
    return entry.get(lang, entry["en"])

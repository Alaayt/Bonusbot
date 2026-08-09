import html

from app.promotions.schemas.promotion import Promotion

_LABELS = {
    "ar": {
        "quick_intro": "إليك ملخص سريع عن {name}:",
        "reward": "الفائدة",
        "steps": "كيفية الاشتراك",
        "min_deposit": "الحد الأدنى للإيداع",
        "status_active": "نشط حاليًا ✅",
        "status_scheduled": "مجدول (لم يبدأ بعد أو ضمن فترة محددة) 🗓",
        "status_expired": "منتهي حاليًا ⏹",
        "status_unknown": "غير مؤكد الحالة بعد ⚠️",
        "full_title": "التفاصيل الكاملة - {name}",
        "eligibility": "الأهلية",
        "wagering": "متطلبات الاستخدام/التدوير",
        "expiry": "الصلاحية",
        "warnings": "تنبيهات مهمة",
        "source": "المصدر الرسمي",
        "last_checked": "آخر مراجعة",
        "unverified_note": "⚠️ بعض تفاصيل هذا العرض غير مؤكدة بعد رسميًا - لن نخترع أي رقم مفقود.",
        "blocked_note": "هذا العرض قيد المراجعة حاليًا ولا تتوفر لدينا بعد تفاصيل موثقة كافية عنه.",
    },
    "en": {
        "quick_intro": "Here's a quick summary of {name}:",
        "reward": "Reward",
        "steps": "How to join",
        "min_deposit": "Minimum deposit",
        "status_active": "Currently active ✅",
        "status_scheduled": "Scheduled 🗓",
        "status_expired": "Currently expired ⏹",
        "status_unknown": "Status not confirmed yet ⚠️",
        "full_title": "Full details - {name}",
        "eligibility": "Eligibility",
        "wagering": "Wagering/usage requirements",
        "expiry": "Validity",
        "warnings": "Important notes",
        "source": "Official source",
        "last_checked": "Last checked",
        "unverified_note": "⚠️ Some details of this offer aren't officially confirmed yet - we won't invent any missing number.",
        "blocked_note": "This offer is currently under review and we don't have enough verified details yet.",
    },
    "fr": {
        "quick_intro": "Voici un résumé rapide de {name} :",
        "reward": "Avantage",
        "steps": "Comment participer",
        "min_deposit": "Dépôt minimum",
        "status_active": "Actif actuellement ✅",
        "status_scheduled": "Programmé 🗓",
        "status_expired": "Expiré actuellement ⏹",
        "status_unknown": "Statut non confirmé ⚠️",
        "full_title": "Détails complets - {name}",
        "eligibility": "Éligibilité",
        "wagering": "Conditions de mise/utilisation",
        "expiry": "Validité",
        "warnings": "Remarques importantes",
        "source": "Source officielle",
        "last_checked": "Dernière vérification",
        "unverified_note": "⚠️ Certains détails de cette offre ne sont pas encore officiellement confirmés - nous n'inventerons aucun chiffre manquant.",
        "blocked_note": "Cette offre est actuellement en cours de vérification et nous ne disposons pas encore de détails confirmés suffisants.",
    },
}


def _l(lang: str, key: str) -> str:
    return _LABELS.get(lang, _LABELS["ar"]).get(key, key)


def _status_label(lang: str, status: str) -> str:
    return _l(lang, f"status_{status}") if f"status_{status}" in _LABELS.get(lang, _LABELS["ar"]) else _l(lang, "status_unknown")


def _esc(value: object) -> str:
    """يهرّب أي قيمة ديناميكية من بيانات العرض قبل حقنها في نص بصيغة HTML لتيليجرام -
    القيم (روابط، مفاتيح JSON، نصوص حرة) قد تحتوي &/</> فتكسر تحليل التنسيق إن لم تُهرّب."""
    return html.escape(str(value))


def format_quick_summary(promo: Promotion, lang: str) -> str:
    if promo.verification_status == "blocked":
        return f"<b>{_esc(promo.name(lang))}</b>\n\n{_l(lang, 'blocked_note')}"

    name = promo.name(lang)
    lines = [_esc(_l(lang, "quick_intro").format(name=name)), ""]
    lines.append(_status_label(lang, promo.status))

    reward = promo.reward or {}
    if reward:
        lines.append(f"\n<b>{_l(lang, 'reward')}:</b> {_esc(_summarize_reward(reward))}")

    if promo.activation_steps:
        lines.append(f"\n<b>{_l(lang, 'steps')}:</b>")
        for i, step in enumerate(promo.activation_steps[:3], 1):
            lines.append(f"{i}. {_esc(step)}")

    min_dep = (promo.deposit_conditions or {}).get("min_deposit_eur")
    if min_dep:
        lines.append(f"\n<b>{_l(lang, 'min_deposit')}:</b> {_esc(min_dep)} EUR")

    if promo.verification_status == "partial":
        lines.append(f"\n{_l(lang, 'unverified_note')}")

    return "\n".join(lines)


def format_full_details(promo: Promotion, lang: str) -> str:
    if promo.verification_status == "blocked":
        return (
            f"<b>{_esc(promo.name(lang))}</b>\n\n{_l(lang, 'blocked_note')}\n\n"
            f"{_l(lang, 'source')}: {_esc(promo.source_url)}"
        )

    name = promo.name(lang)
    lines = [f"<b>{_esc(_l(lang, 'full_title').format(name=name))}</b>", ""]
    lines.append(_status_label(lang, promo.status))

    reward = promo.reward or {}
    if reward:
        lines.append(f"\n<b>{_l(lang, 'reward')}:</b> {_esc(_summarize_reward(reward))}")

    if promo.eligible_countries:
        countries = "الكل / All" if "ALL" in promo.eligible_countries else ", ".join(promo.eligible_countries)
        lines.append(f"\n<b>{_l(lang, 'eligibility')}:</b> {_esc(countries)}")

    if promo.activation_steps:
        lines.append(f"\n<b>{_l(lang, 'steps')}:</b>")
        for i, step in enumerate(promo.activation_steps, 1):
            lines.append(f"{i}. {_esc(step)}")

    wagering = promo.wagering_conditions or {}
    if wagering:
        lines.append(f"\n<b>{_l(lang, 'wagering')}:</b> {_esc(_summarize_dict(wagering))}")

    expiry = promo.expiry_conditions or {}
    if expiry:
        lines.append(f"\n<b>{_l(lang, 'expiry')}:</b> {_esc(_summarize_dict(expiry))}")

    if promo.important_warnings:
        lines.append(f"\n<b>{_l(lang, 'warnings')}:</b>")
        for w in promo.important_warnings:
            lines.append(f"⚠️ {_esc(w)}")

    lines.append(f"\n<b>{_l(lang, 'source')}:</b> {_esc(promo.source_url)}")
    lines.append(f"<b>{_l(lang, 'last_checked')}:</b> {_esc(promo.last_checked_at)}")

    if promo.verification_status == "partial":
        lines.append(f"\n{_l(lang, 'unverified_note')}")

    return "\n".join(lines)


def _summarize_reward(reward: dict) -> str:
    parts = []
    if "percentage" in reward:
        parts.append(f"{reward['percentage']}%")
    if "max_amount_eur" in reward and reward["max_amount_eur"]:
        parts.append(f"حتى {reward['max_amount_eur']} EUR")
    if "amount" in reward and reward["amount"]:
        parts.append(str(reward["amount"]))
    if not parts:
        return reward.get("type", "غير محدد").replace("_", " ")
    return " - ".join(parts)


def _summarize_dict(d: dict) -> str:
    parts = []
    for k, v in d.items():
        if v is None or v == "":
            continue
        parts.append(f"{k.replace('_', ' ')}: {v}")
    return " | ".join(parts) if parts else "غير محدد"

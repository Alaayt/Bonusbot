import json

from openai import AsyncOpenAI

from app.ai.prompts.loader import build_system_prompt
from app.ai.rag.search import get_relevant_promotions
from app.common.config import get_settings

settings = get_settings()
_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def _promotion_context_block(query: str, lang: str, country_code: str | None) -> str:
    promos = get_relevant_promotions(query, lang=lang, country_code=country_code)
    if not promos:
        return "لا توجد عروض مطابقة بدرجة كافية في قاعدة المعرفة لهذا السؤال. أخبر المستخدم بصراحة ولا تخترع بديلاً."
    payload = [p.model_dump() for p in promos]
    return "بيانات العروض ذات الصلة (من قاعدة المعرفة الموثقة فقط):\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def _user_context_block(lang: str, country_code: str | None, has_account: bool | None, stage: str | None) -> str:
    return (
        "سياق المستخدم الحالي:\n"
        f"- اللغة: {lang}\n"
        f"- الدولة: {country_code or 'غير معروفة بعد'}\n"
        f"- لديه حساب حالي: {has_account if has_account is not None else 'غير معروف بعد'}\n"
        f"- مرحلته الحالية: {stage or 'جديد'}\n"
        f"- البروموكود الرسمي: {settings.promo_code}\n"
        f"- رابط التسجيل الرسمي (AFFILIATE_REGISTRATION_URL): {settings.affiliate_registration_url or 'غير مُعد بعد - أخبر المستخدم أنه يحتاج للتواصل مع المدير'}\n"
        f"- رابط تحميل التطبيق (APP_DOWNLOAD_URL): {settings.app_download_url or 'غير مُعد بعد'}"
    )


async def generate_reply(
    user_message: str,
    lang: str,
    country_code: str | None,
    has_account: bool | None,
    stage: str | None,
    conversation_history: list[dict[str, str]],
    extra_system_sections: list[str] | None = None,
) -> str:
    system_prompt = build_system_prompt(extra_sections=extra_system_sections)
    context = (
        _user_context_block(lang, country_code, has_account, stage)
        + "\n\n"
        + _promotion_context_block(user_message, lang, country_code)
    )

    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_history,
        {"role": "user", "content": f"{context}\n\n---\n\nرسالة المستخدم: {user_message}"},
    ]

    client = get_openai_client()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=1024,
        messages=messages,
    )
    return response.choices[0].message.content or ""

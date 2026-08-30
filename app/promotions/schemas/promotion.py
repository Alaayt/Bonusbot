from typing import Any

from pydantic import BaseModel


class PromotionNames(BaseModel):
    ar: str = ""
    en: str = ""
    fr: str = ""


class Promotion(BaseModel):
    id: str
    slug: str
    category: str = "unknown"
    names: PromotionNames = PromotionNames()
    status: str = "unknown"  # active | scheduled | expired | unknown
    new_players_only: bool | None = None
    promo_code_required: bool | None = None
    promo_code: str | None = None
    eligible_countries: list[str] = []
    excluded_countries: list[str] = []
    eligible_users: list[str] = []
    start_at: str | None = None
    end_at: str | None = None
    timezone: str | None = None
    reward: dict[str, Any] = {}
    activation_steps: list[str] = []
    deposit_conditions: dict[str, Any] = {}
    betting_conditions: dict[str, Any] = {}
    casino_conditions: dict[str, Any] = {}
    wagering_conditions: dict[str, Any] = {}
    withdrawal_conditions: dict[str, Any] = {}
    expiry_conditions: dict[str, Any] = {}
    disqualification_reasons: list[str] = []
    kyc_requirements: list[str] = []
    important_warnings: list[str] = []
    faq: list[dict[str, Any]] = []
    source_url: str = ""
    raw_source_file: str | None = None
    last_checked_at: str = ""
    verification_status: str = "unknown"  # verified | partial | blocked
    verified_via: str | None = None

    def name(self, lang: str) -> str:
        return getattr(self.names, lang, None) or self.names.en or self.names.ar or self.slug

    def is_presentable(self) -> bool:
        """لا نعرض العرض للاعب إلا إذا كان لدينا بيانات فعلية (ليس blocked بدون أي محتوى)."""
        return self.verification_status in ("verified", "partial") and bool(self.reward or self.activation_steps)

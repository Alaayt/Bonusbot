import json
from functools import lru_cache
from pathlib import Path

from app.promotions.schemas.promotion import Promotion

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "promotions"


@lru_cache
def _load_all() -> dict[str, Promotion]:
    promotions: dict[str, Promotion] = {}
    for file in sorted(DATA_DIR.glob("*.json")):
        try:
            raw = json.loads(file.read_text(encoding="utf-8"))
            promo = Promotion.model_validate(raw)
            promotions[promo.slug] = promo
        except Exception as exc:  # noqa: BLE001
            # عرض معطوب لا يجب أن يُسقط كل البوت - يُسجَّل ويُتجاهل
            print(f"[promotion_store] فشل تحميل {file.name}: {exc}")
    return promotions


def reload_promotions() -> None:
    """يُستدعى بعد أن يوافق المدير على تحديث - يمسح الكاش لإعادة القراءة من القرص."""
    _load_all.cache_clear()


def get_all_promotions() -> list[Promotion]:
    return list(_load_all().values())


def get_presentable_promotions() -> list[Promotion]:
    return [p for p in get_all_promotions() if p.is_presentable()]


def get_promotion(slug: str) -> Promotion | None:
    return _load_all().get(slug)


def get_by_category(category_prefix: str) -> list[Promotion]:
    return [p for p in get_presentable_promotions() if p.category.startswith(category_prefix)]

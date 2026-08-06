import json
from pathlib import Path

from app.promotions.schemas.promotion import Promotion

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "promotions"


def test_every_json_file_matches_schema_and_has_no_fake_url():
    files = list(DATA_DIR.glob("*.json"))
    assert len(files) >= 29

    for file in files:
        raw = json.loads(file.read_text(encoding="utf-8"))
        promo = Promotion.model_validate(raw)  # يرمي استثناء إن خالف السكيمة

        assert promo.slug == file.stem
        if promo.verification_status != "blocked":
            assert promo.source_url.startswith("https://1xbet.fi"), f"مصدر غير رسمي في {file.name}"

        # قاعدة الدقة: لا مبالغ EUR ضمن reward إلا إن كانت مذكورة كأرقام (وليست نصوصًا اختُلقت)
        if "max_amount_eur" in promo.reward:
            assert isinstance(promo.reward["max_amount_eur"], (int, float, type(None)))

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


def build_system_prompt(extra_sections: list[str] | None = None) -> str:
    sections = [
        load_prompt("system_identity"),
        load_prompt("persuasion"),
        load_prompt("explain_offer"),
        load_prompt("troubleshoot"),
    ]
    if extra_sections:
        sections.extend(extra_sections)
    return "\n\n---\n\n".join(sections)

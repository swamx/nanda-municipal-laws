from functools import lru_cache
from pathlib import Path

_SKILL_MD_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"


@lru_cache(maxsize=1)
def load_skill_md() -> str:
    """Reads the repo's root SKILL.md - the same file served live at GET /skill.md
    and the same one a real autonomous agent is told to follow. Loaded once per
    process; call load_skill_md.cache_clear() in tests if SKILL.md is monkeypatched.
    """
    return _SKILL_MD_PATH.read_text(encoding="utf-8")

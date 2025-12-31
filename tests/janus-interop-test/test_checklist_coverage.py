"""Test that all 7 safety items from CLAUDE.dot are present"""
from pathlib import Path

SAFETY_ITEMS = [
    "Close active queries",
    "Context manager",
    "py_object(true)",
    "py_free",
    "Parameterize input",
    "Catch exceptions",
    "heartbeat",
]

# Alternative phrasings that satisfy the same safety item
SAFETY_ALTERNATIVES = {
    "Close active queries": ["close query", "active query", "query lifecycle"],
    "Context manager": ["context manager", "with query", "with statement"],
    "py_object(true)": ["py_object", "method call"],
    "py_free": ["py_free", "free object", "memory"],
    "Parameterize input": ["parameterize", "user input", "injection"],
    "Catch exceptions": ["catch exception", "exception handler", "try/catch", "error handling", "handle exception", "catch/3"],
    "heartbeat": ["heartbeat", "long operation", "timeout"],
}


def read_skill(skill_name: str) -> str:
    """Read skill content from SKILL.md"""
    skill_path = Path(__file__).parent.parent.parent / "skills" / skill_name / "SKILL.md"
    return skill_path.read_text()


def similar_phrase(item: str, content: str) -> bool:
    """Check if any alternative phrasing of the safety item is present"""
    content_lower = content.lower()
    alternatives = SAFETY_ALTERNATIVES.get(item, [])
    return any(alt.lower() in content_lower for alt in alternatives)


def test_all_safety_items_present():
    """Verify all 7 safety items from CLAUDE.dot are documented"""
    content = read_skill("janus-interop")
    missing = []
    for item in SAFETY_ITEMS:
        if item.lower() not in content.lower() and not similar_phrase(item, content):
            missing.append(item)

    assert not missing, f"Missing safety items in janus-interop: {missing}"


def test_skill_file_exists():
    """Verify the skill file exists"""
    skill_path = Path(__file__).parent.parent.parent / "skills" / "janus-interop" / "SKILL.md"
    assert skill_path.exists(), f"Skill file not found: {skill_path}"


def test_checklist_format():
    """Verify checklist is formatted as a list or table"""
    content = read_skill("janus-interop")
    has_list_format = any(marker in content for marker in ["- [ ]", "- [x]", "1.", "2.", "|"])
    assert has_list_format, "Safety checklist should be formatted as a list or table"

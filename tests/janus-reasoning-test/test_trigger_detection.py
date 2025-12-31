"""Test that janus-reasoning triggers are complete and match CLAUDE.md"""
import os
from pathlib import Path

SKILL_PATH = Path(__file__).parent.parent.parent / "skills" / "janus-reasoning" / "SKILL.md"

REQUIRED_TRIGGERS = [
    "Test result doesn't match expectation",
    "Second failed fix attempt",
    "Can't decide between approaches",
    "Same error message twice in a row",
    "Output matches neither prediction nor its negation",
]

# Alternative phrasings that satisfy the same trigger
TRIGGER_ALTERNATIVES = {
    "Test result doesn't match expectation": ["test fails", "unexpected result", "expectation vs reality"],
    "Second failed fix attempt": ["tried 2 fixes", "2 fixes", "second attempt", "failed twice"],
    "Can't decide between approaches": ["can't decide", "paradigm", "prolog/python"],
    "Same error message twice in a row": ["same error twice", "repeated error"],
    "Output matches neither prediction nor its negation": ["neither prediction", "contradictory"],
}


def read_skill(skill_name: str) -> str:
    """Read skill content from SKILL.md"""
    skill_path = Path(__file__).parent.parent.parent / "skills" / skill_name / "SKILL.md"
    return skill_path.read_text()


def similar_phrase(trigger: str, content: str) -> bool:
    """Check if any alternative phrasing of the trigger is present"""
    content_lower = content.lower()
    alternatives = TRIGGER_ALTERNATIVES.get(trigger, [])
    return any(alt.lower() in content_lower for alt in alternatives)


def test_all_triggers_documented():
    """Verify all confusion triggers from CLAUDE.md are documented in janus-reasoning"""
    content = read_skill("janus-reasoning")
    missing = []
    for trigger in REQUIRED_TRIGGERS:
        if trigger.lower() not in content.lower() and not similar_phrase(trigger, content):
            missing.append(trigger)

    assert not missing, f"Missing triggers in janus-reasoning: {missing}"


def test_skill_file_exists():
    """Verify the skill file exists"""
    assert SKILL_PATH.exists(), f"Skill file not found: {SKILL_PATH}"


def test_skill_has_frontmatter():
    """Verify the skill has valid YAML frontmatter"""
    content = read_skill("janus-reasoning")
    assert content.startswith("---"), "Skill must start with YAML frontmatter"
    assert content.count("---") >= 2, "Skill must have closing frontmatter delimiter"

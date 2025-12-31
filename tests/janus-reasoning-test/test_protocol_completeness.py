"""Test that all 7 prompts are present (6 original + PARADIGM FIT)"""
from pathlib import Path

REQUIRED_PROMPTS = [
    "EXPECTATION vs REALITY",
    "SEMANTIC",
    "SYMBOLIC",
    "COMPARE",
    "ONE HYPOTHESIS",
    "TRACK",
    "PARADIGM FIT",  # NEW - added per senior review
]

# Alternative phrasings that satisfy the same prompt
PROMPT_ALTERNATIVES = {
    "EXPECTATION vs REALITY": ["expectation", "reality", "expected", "actual"],
    "SEMANTIC": ["semantic", "pattern", "intuition"],
    "SYMBOLIC": ["symbolic", "logic", "derive"],
    "COMPARE": ["compare", "agree", "conflict"],
    "ONE HYPOTHESIS": ["one hypothesis", "single hypothesis", "hypothesis at a time"],
    "TRACK": ["track", "log", "record"],
    "PARADIGM FIT": ["paradigm fit", "paradigm mismatch", "paradigm switch"],
}


def read_skill(skill_name: str) -> str:
    """Read skill content from SKILL.md"""
    skill_path = Path(__file__).parent.parent.parent / "skills" / skill_name / "SKILL.md"
    return skill_path.read_text()


def similar_phrase(prompt: str, content: str) -> bool:
    """Check if any alternative phrasing of the prompt is present"""
    content_lower = content.lower()
    alternatives = PROMPT_ALTERNATIVES.get(prompt, [])
    return any(alt.lower() in content_lower for alt in alternatives)


def test_all_prompts_present():
    """Verify all protocol prompts are present in janus-reasoning"""
    content = read_skill("janus-reasoning")
    missing = []
    for prompt in REQUIRED_PROMPTS:
        if prompt not in content and not similar_phrase(prompt, content):
            missing.append(prompt)

    assert not missing, f"Missing prompts in janus-reasoning: {missing}"


def test_protocol_section_exists():
    """Verify there is a protocol or process section"""
    content = read_skill("janus-reasoning")
    has_protocol = any(marker in content.lower() for marker in ["protocol", "process", "steps", "prompts"])
    assert has_protocol, "janus-reasoning must have a protocol/process section"

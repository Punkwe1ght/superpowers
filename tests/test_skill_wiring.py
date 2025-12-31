"""Test cross-skill handoffs are documented"""
from pathlib import Path


def read_skill(skill_name: str) -> str:
    """Read skill content from SKILL.md"""
    skill_path = Path(__file__).parent / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        # Try parent directory (tests are one level down)
        skill_path = Path(__file__).parent.parent / "skills" / skill_name / "SKILL.md"
    return skill_path.read_text()


def test_janus_reasoning_references_interop():
    """Verify janus-reasoning mentions handoff to janus-interop"""
    content = read_skill("janus-reasoning")
    assert "janus-interop" in content, \
        "janus-reasoning must reference janus-interop for safety checklist handoff"


def test_janus_re_references_reasoning():
    """Verify janus-reverse-engineering mentions handoff to janus-reasoning"""
    content = read_skill("janus-reverse-engineering")
    assert "janus-reasoning" in content, \
        "janus-reverse-engineering must reference janus-reasoning for unresolvable contradictions"


def test_janus_re_references_interop():
    """Verify janus-reverse-engineering mentions handoff to janus-interop"""
    content = read_skill("janus-reverse-engineering")
    assert "janus-interop" in content, \
        "janus-reverse-engineering must reference janus-interop before Prolog queries"


def test_using_superpowers_routes_to_reasoning():
    """Verify using-superpowers documents routing to janus-reasoning"""
    content = read_skill("using-superpowers")
    assert "janus-reasoning" in content, \
        "using-superpowers must route confusion triggers to janus-reasoning"


def test_using_superpowers_routes_to_interop():
    """Verify using-superpowers documents routing to janus-interop"""
    content = read_skill("using-superpowers")
    assert "janus-interop" in content, \
        "using-superpowers must route Prolog/Python interop to janus-interop"


def test_using_superpowers_routes_to_re():
    """Verify using-superpowers documents routing to janus-reverse-engineering"""
    content = read_skill("using-superpowers")
    assert "janus-reverse-engineering" in content, \
        "using-superpowers must route RE analysis to janus-reverse-engineering"


def test_handoff_table_exists():
    """Verify using-superpowers has a handoff or routing table"""
    content = read_skill("using-superpowers")
    # Check for table markers or handoff section
    has_table = "|" in content and "Skill" in content
    has_handoff_section = "handoff" in content.lower() or "routing" in content.lower()
    assert has_table or has_handoff_section, \
        "using-superpowers must have a skill routing table or handoff section"

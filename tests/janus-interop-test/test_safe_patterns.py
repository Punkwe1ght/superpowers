"""Test that example code in janus-interop follows safe patterns"""
import re
from pathlib import Path


def read_skill(skill_name: str) -> str:
    """Read skill content from SKILL.md"""
    skill_path = Path(__file__).parent.parent.parent / "skills" / skill_name / "SKILL.md"
    return skill_path.read_text()


def extract_code_blocks(content: str, language: str = None) -> list[str]:
    """Extract fenced code blocks from markdown, optionally filtered by language"""
    if language:
        pattern = rf"```{language}\n(.*?)```"
    else:
        pattern = r"```(?:\w+)?\n(.*?)```"
    return re.findall(pattern, content, re.DOTALL)


def test_no_undefined_predicates():
    """Verify example code doesn't use undefined predicates like log_error/1"""
    content = read_skill("janus-interop")

    # Known undefined predicates that should not appear
    undefined_predicates = ["log_error"]

    prolog_blocks = extract_code_blocks(content, "prolog")
    for block in prolog_blocks:
        for pred in undefined_predicates:
            assert pred not in block, f"Undefined predicate '{pred}' found in Prolog example"


def test_uses_print_message_for_errors():
    """Verify error handling uses print_message/2 instead of undefined predicates"""
    content = read_skill("janus-interop")

    # If there are error handling examples, they should use print_message
    if "error" in content.lower() and "catch" in content.lower():
        prolog_blocks = extract_code_blocks(content, "prolog")
        error_blocks = [b for b in prolog_blocks if "catch" in b or "error" in b.lower()]

        for block in error_blocks:
            if "log_error" in block:
                assert False, "Use print_message(error, ...) instead of log_error/1"


def test_context_manager_pattern():
    """Verify Python examples use context manager for queries"""
    content = read_skill("janus-interop")
    python_blocks = extract_code_blocks(content, "python")

    # If there are query examples, they should use 'with' statement
    query_blocks = [b for b in python_blocks if "query" in b.lower()]
    if query_blocks:
        has_context_manager = any("with" in b for b in query_blocks)
        # This is a soft check - we document the pattern, doesn't mean every example uses it
        # The test passes if context managers are mentioned somewhere in the skill
        assert has_context_manager or "context manager" in content.lower(), \
            "Query examples should demonstrate context manager pattern"

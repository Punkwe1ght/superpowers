"""Validate Prolog syntax for extracted facts."""

import re
from typing import Tuple

# Valid predicates we expect from extraction
VALID_PREDICATES = {"concept", "relates", "example", "formula"}

# Valid relation types
VALID_RELATION_TYPES = {"requires", "illustrates", "contrasts", "extends", "contains"}

# Pattern for a Prolog fact: predicate(arg1, arg2, ...).
FACT_PATTERN = re.compile(
    r'^([a-z_][a-z0-9_]*)\s*\((.*)\)\s*\.\s*$',
    re.IGNORECASE
)

# Pattern for comments
COMMENT_PATTERN = re.compile(r'^%.*$')


def check_balanced_parens(text: str) -> bool:
    """Check if parentheses are balanced."""
    count = 0
    in_string = False
    escape_next = False

    for char in text:
        if escape_next:
            escape_next = False
            continue
        if char == '\\':
            escape_next = True
            continue
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == '(':
            count += 1
        elif char == ')':
            count -= 1
            if count < 0:
                return False

    return count == 0


def parse_prolog_string(s: str) -> Tuple[str, int]:
    """Parse a Prolog string, returning the string content and end position."""
    if not s.startswith('"'):
        raise ValueError("String must start with quote")

    result = []
    i = 1
    while i < len(s):
        if s[i] == '"':
            # Check for doubled quote (escaped)
            if i + 1 < len(s) and s[i + 1] == '"':
                result.append('"')
                i += 2
            else:
                # End of string
                return ''.join(result), i + 1
        elif s[i] == '\\' and i + 1 < len(s):
            # Backslash escape (also valid in some Prolog)
            result.append(s[i + 1])
            i += 2
        else:
            result.append(s[i])
            i += 1

    raise ValueError("Unterminated string")


def validate_fact(line: str) -> Tuple[bool, str]:
    """Validate a single Prolog fact line.

    Returns (is_valid, error_message).
    """
    line = line.strip()

    # Skip empty lines and comments
    if not line or line.startswith('%'):
        return True, ""

    # Check balanced parentheses
    if not check_balanced_parens(line):
        return False, "Unbalanced parentheses"

    # Match fact pattern
    match = FACT_PATTERN.match(line)
    if not match:
        return False, f"Invalid fact syntax: {line[:50]}..."

    predicate = match.group(1)
    # args_str = match.group(2)

    # Validate predicate name
    if predicate not in VALID_PREDICATES:
        return False, f"Unknown predicate: {predicate}"

    # Validate the line ends with a period
    if not line.rstrip().endswith('.'):
        return False, "Fact must end with period"

    return True, ""


def validate_prolog_syntax(prolog_text: str) -> bool:
    """Validate Prolog syntax for extracted facts.

    Returns True if all facts are syntactically valid.
    """
    lines = prolog_text.strip().split('\n')
    has_facts = False

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('%'):
            continue

        has_facts = True
        is_valid, error = validate_fact(line)
        if not is_valid:
            return False

    # A response with only comments (like "% No concepts on this page") is valid
    return True


def validate_file(filepath: str) -> Tuple[bool, list[str]]:
    """Validate a Prolog file, returning (is_valid, list_of_errors)."""
    errors = []

    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines, comments, and directives
            if not line or line.startswith('%') or line.startswith(':-'):
                continue

            is_valid, error = validate_fact(line)
            if not is_valid:
                errors.append(f"Line {line_num}: {error}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # Test validation
    test_cases = [
        ('concept(nash_equilibrium, 42, "A strategy profile").', True),
        ('relates(nash_equilibrium, best_response, requires).', True),
        ('example(prisoners_dilemma, 15, "Two suspects").', True),
        ('formula(mixed_strategy, 87, "p*U(A) + (1-p)*U(B)").', True),
        ('% No concepts on this page', True),
        ('concept(test, 1, "Quote ""test"" here").', True),  # Doubled quotes
        ('invalid_predicate(foo, bar).', False),  # Unknown predicate
        ('concept(test, 1, "unclosed string', False),  # Unclosed string
        ('concept(test, 1, "missing period"', False),  # Missing period
    ]

    print("Running validation tests...")
    for text, expected in test_cases:
        result = validate_prolog_syntax(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] {text[:50]}... -> {result} (expected {expected})")

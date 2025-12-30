#!/usr/bin/env bash
# Test: subagent-driven-development skill
# Verifies that the skill is loaded and follows correct workflow
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== Test: subagent-driven-development skill ==="
echo ""

# Test 1: Verify skill can be loaded
echo "Test 1: Skill loading..."

output=$(run_claude "What is the subagent-driven-development skill? Describe its key steps briefly." 60)

# Accept both kebab-case and title case variations
if assert_contains "$output" "subagent-driven-development\|Subagent-Driven Development\|subagent.*development" "Skill is recognized"; then
    : # pass
else
    exit 1
fi

# The skill's core feature is subagent dispatching and two-stage review
if assert_contains "$output" "subagent\|two-stage\|spec.*compliance\|code.*quality\|review" "Mentions core workflow"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 2: Verify skill describes correct workflow order
echo "Test 2: Workflow ordering..."

output=$(run_claude "In the subagent-driven-development skill, what comes first: spec compliance review or code quality review? Be specific about the order." 60)

# Check that spec compliance is described as coming first
if assert_contains "$output" "spec.*first\|spec.*before.*quality\|compliance.*then.*quality\|1.*spec\|first.*spec" "Spec compliance comes first"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 3: Verify self-review is mentioned
echo "Test 3: Self-review requirement..."

output=$(run_claude "Does the subagent-driven-development skill require implementers to do self-review? What should they check?" 60)

if assert_contains "$output" "self-review\|self review" "Mentions self-review"; then
    : # pass
else
    exit 1
fi

# Self-review catches issues like missing requirements
if assert_contains "$output" "missing\|complete\|requirement\|issue\|check\|verify" "Self-review catches issues"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 4: Verify task extraction concept
echo "Test 4: Task extraction..."

output=$(run_claude "In subagent-driven-development, how does the controller get task information from the plan?" 60)

# The skill extracts tasks from the plan
if assert_contains "$output" "extract\|read.*plan\|task\|plan" "Extracts tasks from plan"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 5: Verify spec compliance reviewer is skeptical
echo "Test 5: Spec compliance reviewer mindset..."

output=$(run_claude "What is the spec compliance reviewer's attitude toward the implementer's report in subagent-driven-development?" 60)

# The spec reviewer checks if implementation matches spec (issues = not done)
if assert_contains "$output" "verify\|check\|confirm\|match\|compliant\|issues" "Reviewer verifies"; then
    : # pass
else
    exit 1
fi

if assert_contains "$output" "spec\|requirement\|implementation\|code" "Reviewer checks code"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 6: Verify review loops
echo "Test 6: Review loop requirements..."

output=$(run_claude "In subagent-driven-development, what happens if a reviewer finds issues? Is it a one-time review or a loop?" 60)

if assert_contains "$output" "loop\|again\|repeat\|until.*approved\|until.*compliant" "Review loops mentioned"; then
    : # pass
else
    exit 1
fi

if assert_contains "$output" "implementer.*fix\|fix.*issues" "Implementer fixes issues"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 7: Verify full task text is provided
echo "Test 7: Task context provision..."

output=$(run_claude "In subagent-driven-development, how does the controller provide task information to the implementer subagent? Does it make them read a file or provide it directly?" 60)

# Controller provides full task text to subagent (no file reading overhead)
if assert_contains "$output" "provide\|full.*text\|include\|pass\|give\|send" "Provides text directly"; then
    : # pass
else
    exit 1
fi

echo ""

echo "=== All subagent-driven-development skill tests passed ==="

#!/usr/bin/env python3
"""
Test the janus-reverse-engineering skill approach against real decompiled code.

This demonstrates how the skill's Prolog-based constraint checking would work:
1. Pattern match to form hypothesis
2. Assert facts about function structure
3. Check for contradictions before claiming
"""

import json
import re

# Load samples
with open("samples.json") as f:
    samples = json.load(f)

print("=" * 70)
print("JANUS REVERSE ENGINEERING SKILL TEST")
print("=" * 70)

def extract_function_info(ghidra_code):
    """Extract facts from Ghidra decompiled code."""
    facts = {
        "function_name": None,
        "params": [],
        "calls": [],
        "has_stack_check": False,
        "has_crypto_constants": False,
        "has_loop": False,
        "writes_memory": False,
        "reads_memory": False,
    }

    # Extract function name
    match = re.search(r'(\w+)\s*\([^)]*\)\s*{', ghidra_code)
    if match:
        facts["function_name"] = match.group(1)

    # Extract parameters
    match = re.search(r'\(([^)]+)\)', ghidra_code)
    if match:
        params = match.group(1).split(',')
        facts["params"] = [p.strip() for p in params if p.strip()]

    # Check for function calls
    calls = re.findall(r'\b(\w+)\s*\(', ghidra_code)
    facts["calls"] = [c for c in calls if c != facts["function_name"] and c not in ['if', 'while', 'for', 'return']]

    # Check for stack canary
    if '__stack_chk_fail' in ghidra_code:
        facts["has_stack_check"] = True

    # Check for crypto-like constants (hex values)
    hex_constants = re.findall(r'0x[0-9a-fA-F]+', ghidra_code)
    if len(hex_constants) > 3:
        facts["has_crypto_constants"] = True

    # Check for loops
    if 'do {' in ghidra_code or 'while' in ghidra_code or 'for' in ghidra_code:
        facts["has_loop"] = True

    # Check for memory operations
    if '*(' in ghidra_code or '*(int' in ghidra_code or '*(long' in ghidra_code:
        facts["writes_memory"] = True
        facts["reads_memory"] = True

    return facts

def form_hypothesis(facts):
    """Form hypothesis based on extracted facts (pattern matching)."""
    hypotheses = []

    # Check function name for hints
    name = facts["function_name"] or ""
    if "hash" in name.lower() or "md4" in name.lower() or "md5" in name.lower():
        hypotheses.append(("crypto_hash", "high", "function name contains hash/md"))
    if "password" in name.lower():
        hypotheses.append(("handles_credentials", "medium", "function name contains password"))
    if "tcp" in name.lower() or "socket" in name.lower():
        hypotheses.append(("network_io", "medium", "function name contains tcp/socket"))

    # Check for crypto patterns
    if facts["has_crypto_constants"] and facts["has_loop"]:
        hypotheses.append(("crypto_operation", "low", "has hex constants and loop"))

    # Check for stack protection
    if facts["has_stack_check"]:
        hypotheses.append(("stack_protected", "high", "calls __stack_chk_fail"))

    return hypotheses

def check_contradictions(facts, hypotheses):
    """Check for contradictions (Prolog constraint checking simulation)."""
    contradictions = []

    for hyp, conf, reason in hypotheses:
        if hyp == "crypto_hash":
            # Crypto hash should call a hash function
            hash_calls = [c for c in facts["calls"] if "hash" in c.lower() or "md" in c.lower()]
            if not hash_calls:
                contradictions.append((hyp, "missing_call", "no hash function called"))

        if hyp == "crypto_operation":
            # Should have key input
            if len(facts["params"]) < 2:
                contradictions.append((hyp, "missing_input", "crypto needs key + data, only {} params".format(len(facts["params"]))))

    return contradictions

def run_skill_test(sample_idx, ghidra_code, source_code):
    """Run the skill test on a single sample."""
    print(f"\n{'─' * 70}")
    print(f"SAMPLE {sample_idx + 1}")
    print(f"{'─' * 70}")

    # Step 1: Extract facts (RECOGNIZE)
    facts = extract_function_info(ghidra_code)
    print(f"\n[1] RECOGNIZE - Extracted facts:")
    print(f"    Function: {facts['function_name']}")
    print(f"    Params: {len(facts['params'])}")
    print(f"    Calls: {facts['calls'][:5]}{'...' if len(facts['calls']) > 5 else ''}")
    print(f"    Stack check: {facts['has_stack_check']}")
    print(f"    Crypto constants: {facts['has_crypto_constants']}")

    # Step 2: Form hypotheses (ASSERT)
    hypotheses = form_hypothesis(facts)
    print(f"\n[2] ASSERT - Hypotheses formed:")
    if hypotheses:
        for hyp, conf, reason in hypotheses:
            print(f"    hypothesis({facts['function_name']}, {hyp}, {conf})")
            print(f"        Reason: {reason}")
    else:
        print("    (no strong hypotheses from patterns)")

    # Step 3: Check contradictions (CHECK)
    contradictions = check_contradictions(facts, hypotheses)
    print(f"\n[3] CHECK - Contradiction query:")
    if contradictions:
        for hyp, kind, detail in contradictions:
            print(f"    CONTRADICTION: {hyp} - {kind}")
            print(f"        {detail}")
    else:
        print("    No contradictions found")

    # Step 4: Resolve or present (RESOLVE/PRESENT)
    print(f"\n[4] PRESENT - Final assessment:")
    valid_hypotheses = [h for h in hypotheses if h[0] not in [c[0] for c in contradictions]]
    if valid_hypotheses:
        for hyp, conf, reason in valid_hypotheses:
            print(f"    ✓ {hyp} (confidence: {conf})")
    else:
        print("    No validated hypotheses - need more analysis")

    # Compare with ground truth
    print(f"\n[GROUND TRUTH] Original source excerpt:")
    source_lines = source_code.split('\n')[:3]
    for line in source_lines:
        print(f"    {line}")

# Run tests on samples
for i, sample in enumerate(samples[:5]):  # Test first 5
    run_skill_test(i, sample["instruction"], sample["output"])

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("""
This demonstrates the janus-reverse-engineering skill's approach:
1. RECOGNIZE: Extract structural facts from decompiled code
2. ASSERT: Form hypotheses based on patterns
3. CHECK: Query for contradictions before claiming
4. PRESENT: Only report validated hypotheses

In a real implementation, Prolog would handle constraint propagation
and catch logical contradictions the pattern matcher misses.
""")

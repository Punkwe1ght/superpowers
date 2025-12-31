#!/usr/bin/env python3
"""
Demonstrates Python-Prolog interop for the janus-reverse-engineering skill.

Python extracts facts from decompiled code, Prolog checks constraints
and catches contradictions, Python presents validated results.
"""

import janus_swi as janus
import json
import os
import re

# Initialize Prolog with absolute path
_script_dir = os.path.dirname(os.path.abspath(__file__))
janus.consult(os.path.join(_script_dir, "janus_re.pl"))

def extract_facts_from_ghidra(ghidra_code: str) -> dict:
    """Extract facts from Ghidra decompiled code (Python pattern matching)."""
    facts = {
        "function_name": None,
        "params": [],
        "calls": [],
        "has_stack_check": False,
        "has_null_check": False,
    }

    # Extract function name
    match = re.search(r'(\w+)\s*\([^)]*\)\s*\n?\s*{', ghidra_code)
    if match:
        facts["function_name"] = match.group(1)

    # Extract parameters
    match = re.search(r'\(([^)]+)\)', ghidra_code)
    if match:
        params = match.group(1).split(',')
        facts["params"] = [p.strip().split()[-1] for p in params if p.strip()]

    # Check for function calls
    calls = re.findall(r'\b([A-Za-z_]\w+)\s*\(', ghidra_code)
    facts["calls"] = list(set(c for c in calls
                               if c != facts["function_name"]
                               and c not in ['if', 'while', 'for', 'return', 'long', 'int', 'uint', 'void']))

    # Check for stack canary
    facts["has_stack_check"] = '__stack_chk_fail' in ghidra_code

    # Check for null checks
    facts["has_null_check"] = '!= 0' in ghidra_code or '== 0' in ghidra_code

    return facts


VALID_ROLES = frozenset({"counter", "buffer", "struct_access", "socket", "key", "input", "output", "unknown"})


def validate_role(role: str) -> str:
    """Validate that role is a known semantic role."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}', must be one of: {sorted(VALID_ROLES)}")
    return role


def infer_param_role(param_name: str, code_body: str) -> str:
    """Infer semantic role from parameter usage patterns."""
    # Escape for regex (handle *param_1)
    p = re.escape(param_name.lstrip('*'))

    # Pattern 1: Counter - *p = *p + 1 or (*p)++
    if re.search(rf'\*{p}\s*=\s*\*{p}\s*\+\s*1', code_body):
        return validate_role("counter")
    if re.search(rf'\(\s*\*{p}\s*\)\s*\+\+', code_body):
        return validate_role("counter")

    # Pattern 2: Buffer - base in pointer arithmetic (base + idx * stride)
    if re.search(rf'{p}\s*\+\s*.*\*\s*\d+', code_body):
        return validate_role("buffer")
    if re.search(rf'\(\s*long\s*\)\s*{p}\s*\*', code_body):
        return validate_role("buffer")

    # Pattern 3: Struct access - param[N] where N is small constant
    if re.search(rf'{p}\s*\[\s*\d\s*\]', code_body):
        return validate_role("struct_access")

    return validate_role("unknown")


def find_sample_by_name(samples: list, func_name: str) -> dict:
    """Find sample by function name instead of hardcoded index."""
    for sample in samples:
        if func_name in sample.get("instruction", ""):
            return sample
    raise ValueError(f"Sample with function '{func_name}' not found")


def assert_facts_to_prolog(func_id: str, facts: dict, hypothesis: tuple, code: str):
    """Load extracted facts into Prolog knowledge base."""
    # Clear previous facts
    janus.query_once("clear_facts")

    # Assert function
    janus.query_once(
        "assertz(function(FuncId, Name, sig(void, [])))",
        {"FuncId": func_id, "Name": facts["function_name"]}
    )

    # Assert parameter flows using pattern inference
    for i, param in enumerate(facts["params"], 1):
        role = infer_param_role(param, code)
        janus.query_once(
            "assertz(arg_flows_to(FuncId, ArgN, Role))",
            {"FuncId": func_id, "ArgN": i, "Role": role}
        )

    # Assert calls
    for call in facts["calls"]:
        janus.query_once(
            "assertz(calls(FuncId, Callee, []))",
            {"FuncId": func_id, "Callee": call}
        )

    # Assert hypothesis
    hyp_purpose, hyp_confidence = hypothesis
    janus.query_once(
        "assertz(hypothesis(FuncId, Purpose, Confidence))",
        {"FuncId": func_id, "Purpose": hyp_purpose, "Confidence": hyp_confidence}
    )

    # Assert patterns
    if facts["has_stack_check"]:
        janus.query_once(
            "assertz(known_pattern(FuncId, stack_protection))",
            {"FuncId": func_id}
        )
    if facts["has_null_check"]:
        janus.query_once(
            "assertz(known_pattern(FuncId, null_validation))",
            {"FuncId": func_id}
        )

def check_contradictions(func_id: str) -> list:
    """Query Prolog for contradictions."""
    contradictions = []
    try:
        # Use wrapper predicate to avoid compound term conversion
        for result in janus.query("contradiction_str(FuncId, CStr)", {"FuncId": func_id}):
            contradictions.append(result["CStr"])
    except janus.PrologError as e:
        print(f"  [ERROR] Prolog query failed: {e}")
    return contradictions


def check_mitigations(func_id: str) -> list:
    """Query Prolog for security mitigations."""
    mitigations = []
    try:
        for result in janus.query("mitigation_str(FuncId, MStr)", {"FuncId": func_id}):
            mitigations.append(result["MStr"])
    except janus.PrologError as e:
        print(f"  [ERROR] Prolog query failed: {e}")
    return mitigations

def run_janus_analysis(ghidra_code: str, hypothesis: tuple, ground_truth: str = None):
    """Run the Janus Reverse Engineering analysis pipeline."""
    print("\n" + "-" * 60)

    # Step 1: RECOGNIZE (Python pattern matching)
    facts = extract_facts_from_ghidra(ghidra_code)
    func_id = facts["function_name"] or "unknown"

    print(f"[RECOGNIZE] Function: {func_id}")
    print(f"  Parameters: {facts['params']}")
    print(f"  Calls: {facts['calls']}")
    print(f"  Stack check: {facts['has_stack_check']}")

    # Step 2: ASSERT (Python -> Prolog)
    print(f"\n[ASSERT] Hypothesis: {hypothesis[0]} (confidence: {hypothesis[1]})")
    assert_facts_to_prolog(func_id, facts, hypothesis, ghidra_code)

    # Step 3: CHECK (Prolog constraint propagation)
    print("\n[CHECK] Querying Prolog for contradictions...")
    contradictions = check_contradictions(func_id)
    mitigations = check_mitigations(func_id)

    if contradictions:
        print("  [WARNING] CONTRADICTIONS FOUND:")
        for c in contradictions:
            print(f"    - {c}")
    else:
        print("  [OK] No contradictions")

    if mitigations:
        print(f"  Mitigations: {mitigations}")

    # Step 4: PRESENT (validated result)
    print("\n[PRESENT]", end=" ")
    if contradictions:
        print(f"Cannot claim '{hypothesis[0]}' - hypothesis contradicted")
    else:
        print(f"Validated: {func_id} is {hypothesis[0]} (confidence: {hypothesis[1]})")

    if ground_truth:
        print(f"\n[GROUND TRUTH] {ground_truth[:80]}...")

    return {
        "function": func_id,
        "hypothesis": hypothesis,
        "contradictions": contradictions,
        "mitigations": mitigations,
        "validated": not contradictions
    }

def run_tests():
    """Run all test cases."""
    print("=" * 60)
    print("JANUS BRIDGE TEST - Python <-> Prolog Interop")
    print("=" * 60)

    # Load samples from dataset
    samples_path = os.path.join(_script_dir, "samples.json")
    with open(samples_path) as f:
        samples = json.load(f)

    # Test 1: GenerateNtPasswordHashHash (real crypto - should pass)
    print("\n" + "=" * 60)
    print("TEST 1: Password Hash Function (should validate)")
    print("=" * 60)

    hash_sample = find_sample_by_name(samples, "GenerateNtPasswordHashHash")
    run_janus_analysis(
        hash_sample["instruction"],
        ("hash_md4", "high"),
        hash_sample["output"]
    )

    # Test 2: hp3800_fixedpwm (scanner - false crypto, should contradict)
    print("\n" + "=" * 60)
    print("TEST 2: Scanner Driver - False Crypto (should contradict)")
    print("=" * 60)

    scanner_sample = find_sample_by_name(samples, "hp3800_fixedpwm")
    run_janus_analysis(
        scanner_sample["instruction"],
        ("crypto_operation", "low"),
        scanner_sample["output"]
    )

    # Test 3: TCP function (network I/O - should pass)
    print("\n" + "=" * 60)
    print("TEST 3: TCP Network Function (should validate)")
    print("=" * 60)

    tcp_sample = find_sample_by_name(samples, "ioabs_tcp_pre_select")
    run_janus_analysis(
        tcp_sample["instruction"],
        ("network_io", "medium"),
        tcp_sample["output"]
    )

    # Test 4: Same function with WRONG hypothesis
    print("\n" + "=" * 60)
    print("TEST 4: TCP Function with WRONG hypothesis (should contradict)")
    print("=" * 60)

    run_janus_analysis(
        tcp_sample["instruction"],
        ("aes_encrypt", "low"),
        tcp_sample["output"]
    )

    print("\n" + "=" * 60)
    print("JANUS BRIDGE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()

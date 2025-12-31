# Semantic Parameter Inference for Janus RE Skill

**Date:** 2025-12-30
**Status:** Design Complete
**Problem:** Ghidra's generic param names break constraint validation

## Problem Statement

The janus-reverse-engineering skill uses Prolog to validate hypotheses about function purpose. Test 3 exposed a gap:

```
Ghidra gives:  int *param_1, int *param_2, long param_3
Ground truth:  connection c, int *n, struct pollfd *pfds
```

The constraint checker requires semantic roles:
```prolog
requires(network_io, [socket, buffer]).
```

But params like `*param_1` don't match `socket`. Result: false contradiction.

## Solution

Two-layer inference:

```
┌─────────────────────────────────────────────────────────┐
│  Python: Pattern Detection                              │
│  - Analyze HOW params are used in code body             │
│  - Emit structural roles: buffer, counter, struct_access│
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Prolog: Flexible Matching                              │
│  - Map structural roles to semantic requirements        │
│  - struct_access + network_io → satisfies socket        │
│  - buffer (any context) → satisfies buffer              │
└─────────────────────────────────────────────────────────┘
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Inference strategy | Usage-pattern heuristics | Works within Claude's pattern-matching strength |
| Scope | Minimal (3 patterns) | YAGNI - add patterns as tests fail |
| Detection location | Python | Keep Prolog focused on logic |
| Role mapping | Flexible Prolog rules | Decouples structural from semantic |

## Implementation

### Python: Pattern Detection

Add to `test_janus_bridge.py`, migrate to skill if proven:

```python
def infer_param_role(param_name: str, code_body: str) -> str:
    """Infer semantic role from how parameter is used in code."""

    # Escape for regex (handle *param_1)
    p = re.escape(param_name.lstrip('*'))

    # Pattern 1: Counter - *p = *p + 1 or (*p)++
    if re.search(rf'\*{p}\s*=\s*\*{p}\s*\+\s*1', code_body):
        return "counter"
    if re.search(rf'\(\s*\*{p}\s*\)\s*\+\+', code_body):
        return "counter"

    # Pattern 2: Buffer - base in ptr arithmetic (base + idx * stride)
    if re.search(rf'{p}\s*\+\s*.*\*\s*\d+', code_body):
        return "buffer"
    if re.search(rf'\(\s*long\s*\)\s*{p}\s*\*', code_body):
        return "buffer"

    # Pattern 3: Struct access - param[N] where N is small constant
    if re.search(rf'{p}\s*\[\s*\d\s*\]', code_body):
        return "struct_access"

    return "unknown"
```

### Prolog: Flexible Matching

Add to `janus_re.pl`:

```prolog
%% Flexible role matching - structural roles satisfy semantic requirements

% Buffer pattern satisfies buffer requirement
has_input(Func, buffer) :-
    arg_flows_to(Func, _, buffer).

% Struct access satisfies socket for network hypotheses
has_input(Func, socket) :-
    arg_flows_to(Func, _, struct_access),
    hypothesis(Func, network_io, _).

% Struct access satisfies key for crypto hypotheses
has_input(Func, key) :-
    arg_flows_to(Func, _, struct_access),
    hypothesis(Func, Purpose, _),
    crypto_purpose(Purpose).

%% Helper predicates
crypto_purpose(aes_encrypt).
crypto_purpose(aes_decrypt).
crypto_purpose(hmac).
crypto_purpose(hash_md4).
crypto_purpose(hash_md5).
```

## Test Plan

| Test | Before | After | Status |
|------|--------|-------|--------|
| Test 1: Hash | Validates | Validates | No change |
| Test 2: Scanner | Contradicts | Contradicts | No change |
| Test 3: TCP | Contradicts | Validates | Fixed |
| Test 4: TCP wrong hyp | Contradicts | Contradicts | No change |

### Verification Steps

1. Add `infer_param_role()` to test file
2. Replace naive `semantic_map` with pattern inference
3. Add flexible matching rules to `janus_re.pl`
4. Run `python3 test_janus_bridge.py`
5. Confirm Test 3 validates, others unchanged

## Future Extensions

Add patterns only when tests fail:

| Pattern | Trigger | Use Case |
|---------|---------|----------|
| `fd_arg` | File I/O test fails | Detect file descriptor params |
| `size_arg` | Malloc test fails | Detect size/length params |
| `output_ptr` | Return-by-ref fails | Detect output buffer params |

## Files Modified

- `tests/janus-re-test/test_janus_bridge.py` - add pattern inference
- `tests/janus-re-test/janus_re.pl` - add flexible matching rules

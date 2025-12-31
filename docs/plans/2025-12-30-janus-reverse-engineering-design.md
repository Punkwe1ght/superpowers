# Janus Reverse Engineering Skill Design

**Date:** 2025-12-30
**Status:** Implemented

## Problem

Claude has specific limitations during reverse engineering:

1. **State tracking degrades** across many functions
2. **Constraint propagation is inconsistent** (says "X is pointer" then treats as int)
3. **Logical contradictions go unnoticed** in pattern-matched hypotheses
4. **Hallucinated vulnerabilities** waste user time (NDSS: 231% time overhead)

## Insight

The NDSS paper on human-LLM teaming in SRE studied how *humans* should use LLMs. But the real question: how should *Claude* augment its own reasoning?

The Janus paper shows Prolog and Python can interoperate with hundreds of thousands of round-trips per second. Prolog excels at exactly what Claude struggles with: constraint propagation and consistency checking.

**Key reframe:** Use Prolog not as a workflow tool, but as a cognitive backend that catches Claude's errors before they reach the user.

## Design

### Core Pattern

```
RECOGNIZE → ASSERT → CHECK → RESOLVE/RETRACT → PRESENT
```

1. **Recognize**: Claude pattern-matches (its strength)
2. **Assert**: Commit hypothesis to Prolog knowledge base
3. **Check**: Query for contradictions
4. **Resolve/Retract**: Fix contradiction or withdraw claim
5. **Present**: Only then tell user

### Knowledge Base Schema

```prolog
% Facts
function(Addr, Name, Signature).
calls(Caller, Callee, Args).
arg_flows_to(Func, ArgN, Dest).

% Hypotheses (tagged)
hypothesis(Func, Purpose, Confidence).

% Constraint checking
requires(Purpose, [Inputs]).
contradiction(Func, Reason).
```

### Vulnerability Claims

Special handling because NDSS found Claude's unchecked vuln claims cause 231% time waste:

```prolog
vuln_hypothesis(Func, Type, Reason).
vuln_reachable(Func).
vuln_contradicted(Func, Why).
mitigation_present(Func, What).
```

Rule: Never claim vulnerability unless reachable AND not contradicted.

## Integration

| Skill | Relationship |
|-------|--------------|
| `janus-interop` | Safety checklist for all Prolog queries |
| `janus-reasoning` | Escalation when contradictions unresolvable |

## Files

```
skills/janus-reverse-engineering/SKILL.md  # NEW
```

## Rationale

This skill differs from existing Janus skills:

- `janus-reasoning`: Generic debugging methodology (semantic + symbolic thinking)
- `janus-interop`: Safety checklist for Prolog/Python code
- `janus-reverse-engineering`: **Domain-specific cognitive augmentation** using Prolog to catch Claude's RE errors

The key insight: Claude should use Prolog as a reasoning backend, not just follow a methodology about reasoning.

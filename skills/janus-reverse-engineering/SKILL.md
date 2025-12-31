---
name: janus-reverse-engineering
description: Use when analyzing decompiled code, tracing cross-function data flow, or claiming function purpose or vulnerabilities
---

# Janus Reverse Engineering

## Why This Exists

I have specific limitations during RE:

| My Limitation | What Goes Wrong |
|---------------|-----------------|
| State tracking across functions | Lose track of register/variable contents after ~10 functions |
| Constraint propagation | Say "X is a pointer" then treat it as int |
| Logical consistency | Pattern-match "looks like crypto" but miss contradictions |
| Hallucination | Claim vulnerabilities that don't exist (NDSS: 231% time wasted) |

**Solution:** Use Prolog as a consistency checker. Assert facts as I discover them. Query before making claims. Catch contradictions before presenting to user.

## When to Use

**Triggers:**
- Analyzing decompiled/disassembled code
- Tracing data flow across multiple functions
- Making claims about function purpose, types, or security properties
- About to tell user "this is vulnerable" or "this does X"

## The Pattern

```
┌─────────────────────────────────────────────────────────────┐
│ 1. RECOGNIZE (pattern matching - my strength)               │
│    "This looks like AES based on constants and structure"   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ASSERT (commit to Prolog knowledge base)                 │
│    ?- assertz(hypothesis(0x401000, aes_encrypt, medium)).   │
│    ?- assertz(requires(aes_encrypt, [key, plaintext])).     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CHECK (query for contradictions BEFORE telling user)     │
│    ?- contradiction(0x401000, Why).                         │
│    Why = missing_input(key).  ← I would have hallucinated   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. RESOLVE or RETRACT                                       │
│    Either find the missing piece, or retract hypothesis     │
└─────────────────────────────────────────────────────────────┘
```

## Knowledge Base Schema

### Facts I Assert

```prolog
% Declare dynamic predicates
:- dynamic function/3.
:- dynamic calls/3.
:- dynamic returns/2.
:- dynamic reads/3.
:- dynamic writes/3.
:- dynamic arg_flows_to/3.
:- dynamic hypothesis/3.
:- dynamic known_pattern/2.
:- dynamic vuln_hypothesis/3.

% Function basics
%   function(Addr, Name, Signature)
%   calls(Caller, Callee, Args)
%   returns(Func, Type)

% Data flow
%   reads(Func, Addr, Size)
%   writes(Func, Addr, Size)
%   arg_flows_to(Func, ArgN, SemanticRole)  % SemanticRole: key, plaintext, etc.

% Hypotheses (Confidence: low/medium/high)
%   hypothesis(Func, Purpose, Confidence)
%   known_pattern(Func, PatternName)
%   vuln_hypothesis(Func, VulnType, Reason)
```

### Constraint Rules

```prolog
% What patterns require
requires(aes_encrypt, [key, plaintext]).
requires(aes_decrypt, [key, ciphertext]).
requires(hmac, [key, message]).
requires(malloc, [size]).
requires(free, [pointer]).

% Detect missing inputs
missing_input(Func, Required) :-
    hypothesis(Func, Purpose, _),
    requires(Purpose, Inputs),
    member(Required, Inputs),
    \+ has_input(Func, Required).

has_input(Func, Input) :-
    arg_flows_to(Func, _, Input).

% Detect contradictions
contradiction(Func, missing_input(What)) :-
    missing_input(Func, What).

contradiction(Func, type_mismatch(Arg, Expected, Actual)) :-
    hypothesis(Func, Purpose, _),
    requires_type(Purpose, Arg, Expected),
    actual_type(Func, Arg, Actual),
    Expected \= Actual.

contradiction(Func, conflicting_hypotheses(H1, H2)) :-
    hypothesis(Func, H1, _),
    hypothesis(Func, H2, _),
    H1 \= H2,
    incompatible(H1, H2).

% Symmetric incompatibility check
incompatible(A, B) :- incompatible_(A, B).
incompatible(A, B) :- incompatible_(B, A).

incompatible_(encrypt, decrypt).
incompatible_(malloc, free).
incompatible_(read_only, writes_memory).
```

## Pre-Claim Checklist

Before telling the user "this function does X" or "this is vulnerable":

```
□ Hypothesis asserted to Prolog
  "hypothesis(Addr, Purpose, Confidence) asserted"

□ Constraints checked
  "?- contradiction(Addr, Why). → [results]"

□ No unresolved contradictions
  "Contradictions: none" OR "Resolved by: ___"

□ Confidence justified
  "Confidence is [low/medium/high] because: ___"
```

**If contradiction found:** Resolve it or downgrade claim. Do NOT present contradicted hypothesis as fact.

## Worked Example

**Scenario:** Analyzing function at 0x401000, looks like encryption.

### Step 1: Recognize

Looking at decompiled code, I see:
- XOR operations in a loop
- Constants that look like S-box values
- 16-byte block operations

My pattern recognition says: "This looks like AES."

### Step 2: Assert

```prolog
?- assertz(function(0x401000, unknown, sig(void, [ptr(void), ptr(void), ptr(void)]))).
?- assertz(hypothesis(0x401000, aes_encrypt, medium)).
?- assertz(known_pattern(0x401000, sbox_lookup)).
?- assertz(known_pattern(0x401000, xor_rounds)).

% What I observed about inputs
?- assertz(arg_flows_to(0x401000, 1, output_buffer)).
?- assertz(arg_flows_to(0x401000, 2, input_buffer)).
?- assertz(arg_flows_to(0x401000, 3, unknown)).  % Third arg unclear
```

### Step 3: Check

```prolog
?- contradiction(0x401000, Why).
Why = missing_input(key).
```

**Prolog caught my error.** AES requires a key. I only traced 3 args: output, input, unknown. Where's the key?

### Step 4: Resolve

Options:
1. Third arg IS the key → update: `arg_flows_to(0x401000, 3, key)`
2. Key is global → assert: `reads(0x401000, 0x405000, 16), global_key(0x405000)`
3. Not actually AES → retract hypothesis

I re-examine the code. Third arg is indeed used in key schedule operations.

```prolog
?- retract(arg_flows_to(0x401000, 3, unknown)).
?- assertz(arg_flows_to(0x401000, 3, key)).

?- contradiction(0x401000, Why).
false.  % No contradictions
```

### Step 5: Present to User

Now I can tell the user:
> "Function 0x401000 appears to be AES encryption. It takes (output, input, key) as arguments. Confidence: medium, based on S-box constants and XOR round structure."

Without the Prolog check, I might have said "this is AES" without noticing the key input was unaccounted for.

## Vulnerability Claims

**CRITICAL:** The NDSS study found I cause 231% time waste on false vulnerability claims.

Before claiming "this is vulnerable":

```prolog
% Assert the vulnerability hypothesis
?- assertz(vuln_hypothesis(Func, buffer_overflow, Reason)).

% Check if it's actually reachable
?- vuln_reachable(Func).

% Check if mitigations exist
?- mitigation_present(Func, Mitigation).

% Check for contradicting evidence
?- vuln_contradicted(Func, Why).
```

**Rules:**

```prolog
% --- User-defined predicates (assert these based on analysis) ---
% user_controlled_input(Source) - Source is attacker-controlled (e.g., argv, recv)
% data_flows(From, To) - taint propagates from From to To
% bounds_check_before(Func) - bounds validation precedes vulnerable op
% size_validation_before(Func) - size check precedes vulnerable op

:- dynamic user_controlled_input/1.
:- dynamic data_flows/2.
:- dynamic bounds_check_before/1.
:- dynamic size_validation_before/1.

% Reachability: attacker input flows to function
vuln_reachable(Func) :-
    user_controlled_input(Source),
    data_flows(Source, Func).

% Transitive data flow (define base cases via assertz)
data_flows(A, C) :-
    data_flows(A, B),
    data_flows(B, C),
    A \= C.  % Prevent trivial cycles

vuln_contradicted(Func, bounds_checked) :-
    vuln_hypothesis(Func, buffer_overflow, _),
    bounds_check_before(Func).

vuln_contradicted(Func, size_validated) :-
    vuln_hypothesis(Func, buffer_overflow, _),
    size_validation_before(Func).

mitigation_present(Func, stack_canary) :-
    calls(Func, '__stack_chk_fail', _).
```

**If vuln_contradicted succeeds:** Do NOT claim vulnerability. State uncertainty.

## Integration

**REQUIRED:** Use `superpowers:janus-interop` for all Prolog queries:
- Context manager for queries
- Exception handling for py_call
- Parameterized inputs (never string interpolation)

**ESCALATE:** Use `superpowers:janus-reasoning` when contradiction unresolvable:
1. Enter janus-reasoning protocol
2. Complete semantic + symbolic analysis
3. Derive which hypothesis is wrong
4. Retract incorrect assertion

## Red Flags

| My Thought | Reality |
|------------|---------|
| "This is obviously AES" | Assert and CHECK before claiming |
| "I can see the vulnerability" | Query vuln_contradicted first |
| "The pattern is clear" | Patterns deceive. Constraints don't. |
| "I'll just tell them what I see" | What I "see" may contradict itself |
| "Prolog check seems overkill" | NDSS: my unchecked claims waste user time |

## Quick Reference

```
BEFORE claiming function purpose:
  1. ?- assertz(hypothesis(Addr, Purpose, Confidence))
  2. ?- contradiction(Addr, Why)
  3. Resolve or retract
  4. Only then present to user

BEFORE claiming vulnerability:
  1. ?- assertz(vuln_hypothesis(Func, Type, Reason))
  2. ?- vuln_reachable(Func)
  3. ?- vuln_contradicted(Func, Why)
  4. ?- mitigation_present(Func, What)
  5. Only claim if reachable AND not contradicted

WHEN contradiction found:
  → Try to resolve with more analysis
  → If unresolvable → janus-reasoning protocol
  → If still stuck → downgrade confidence, state uncertainty
```

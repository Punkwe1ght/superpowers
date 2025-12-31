---
name: janus-interop
description: Use when writing or executing Prolog/Python interop code - mandatory safety protocol
---

# Janus Interop Safety

## Overview

Prolog/Python interop requires careful resource management. Query leaks, unfreed objects, and unparameterized input cause subtle bugs.

**Core principle:** Complete the checklist before and after writing interop code.

## When to Use

**Trigger:** Code uses any of:

| Prolog | Python |
|--------|--------|
| `py_call` | `janus.query()` |
| `py_iter` | `janus.query_once()` |
| `py_setattr` | `janus.apply()` |
| `py_free` | `janus.apply_once()` |
| `py_with_gil` | `janus.Term()` |
| `py_object` | |

## Pre-Execution Checklist

Complete each item. Write the answer, not just "yes."

### Query Lifecycle

**Close active queries before new ones:**
```
Queries in scope: ___
Closed via: ___
```

**Use context manager for iteration:**
```python
# REQUIRED:
for result in janus.query("goal(X)"):
    process(result)

# FORBIDDEN:
q = janus.query("goal(X)")
result = next(q)  # Who closes this?
```

### Object Lifecycle

**Pass py_object(true) for objects needing method calls:**
```
Objects requiring methods: ___
```

**Call py_free/1 for large objects:**
```
Large allocations: ___
Freed at: ___
```

### Safety

**Parameterize user input (no string interpolation):**
```prolog
% REQUIRED:
py_call(module:func(Input), Result)

% FORBIDDEN:
format(atom(Call), "module:func('~w')", [Input]),
py_call(Call, Result)
```

**Handle exceptions:**
```prolog
catch(
    py_call(module:func, Result),
    Error,
    handle_py_error(Error)
)
```

### Performance

**Insert heartbeat() for operations >100ms:**
```
Long operations: ___
heartbeat() at: ___
```

## Post-Execution Verification

Verify in actual code. Line numbers required.

| Check | Location | Status |
|-------|----------|--------|
| All query() calls: context manager or explicit close? | Line ___: | [manager/close/VIOLATION] |
| All py_call: exception handling present? | Line ___: | [handled/VIOLATION] |
| All user inputs: parameterized? | Line ___: | [parameterized/VIOLATION] |
| All large objects: py_free path exists? | Line ___: | [freed/N/A] |
| All long operations: heartbeat present? | Line ___: | [heartbeat/N/A] |

**If ANY violation, fix before proceeding.**

## Safe Patterns

### Prolog Side

```prolog
%% query_user(+Name, -Result) is det
%% Safe query with cleanup - always succeeds (Result may be error term)
query_user(Name, Result) :-
    catch(
        py_call(db:lookup(Name), Result, [py_object(true)]),
        Error,
        (print_message(error, Error), Result = error(Error))
    ).

%% process_all(+Goal) is det
%% Safe iteration with heartbeat - processes all items, always succeeds
process_all(Goal) :-
    forall(
        py_iter(generator:items, Item),
        (heartbeat, process_item(Item))
    ).

%% with_large_object(-Obj, :Goal) is semidet
%% Safe large object handling - succeeds if Goal succeeds, always frees Obj
with_large_object(Obj, Goal) :-
    setup_call_cleanup(
        py_call(create_large, Obj),
        call(Goal, Obj),
        py_free(Obj)
    ).
```

### Python Side

```python
# Safe Prolog query from Python
def find_solutions(goal):
    results = []
    for solution in janus.query(goal):
        results.append(solution)
        # Context manager handles cleanup
    return results

# Parameterized query (safe)
def lookup_user(name):
    return janus.query_once("user(Name, Data)", {"Name": name})

# UNSAFE - string interpolation
def lookup_user_bad(name):
    return janus.query_once(f"user('{name}', Data)")  # INJECTION RISK
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `next()` without close | Query leak | Use `for` loop or `with` |
| String interpolation in queries | Injection | Parameterize with dict |
| Missing `py_object(true)` | Method calls fail | Add option when keeping object |
| No exception handling | Silent failures | Wrap in `catch/3` |
| Long operations without heartbeat | Timeout/hang | Add `heartbeat` in loops |

## Red Flags

| Thought | Reality |
|---------|---------|
| "I'll close the query later" | You won't. Use context manager. |
| "This input is trusted" | Parameterize anyway. Defense in depth. |
| "Exception handling is verbose" | Silent failures are worse. |
| "It's a small object" | Memory leaks accumulate. Free it. |
| "The operation is fast" | Add heartbeat anyway. It's cheap. |

## Quick Reference

```
BEFORE writing interop:
  □ Queries in scope identified
  □ Object lifecycle planned
  □ Exception handling strategy chosen
  □ User inputs identified for parameterization

AFTER writing interop:
  □ All queries use context manager or explicit close
  □ All py_call wrapped in catch
  □ All user input parameterized
  □ Large objects freed
  □ Long operations have heartbeat
```

## Handoffs

| Condition | Next | Entry Point |
|-----------|------|-------------|
| Checklist complete | Caller | Resume at code writing |
| Violation found | Caller | Fix before proceeding |

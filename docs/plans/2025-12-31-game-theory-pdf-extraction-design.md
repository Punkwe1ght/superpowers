# Game Theory PDF Knowledge Extraction Design

**Date:** 2025-12-31
**Status:** Approved
**Input:** game-theory-101.pdf (377 pages, 3.4MB)
**Output:** Prolog knowledge base queryable via Janus

## Overview

Extract concepts, relationships, examples, and formulas from a game theory textbook into Prolog facts. Uses a hybrid approach: automated extraction followed by interactive Janus verification.

## Approach

**Phase 1: Automated Extraction**
- Python script iterates through all 377 pages
- Calls Claude API for each page with structured extraction prompt
- Accumulates Prolog facts in `output/knowledge.pl`
- Tracks progress for resumability

**Phase 2: Janus Verification**
- Load knowledge base in Claude Code session
- Run verification queries via SWI-Prolog/Janus
- Fix undefined references, duplicates, malformed facts
- Produce clean, queryable knowledge base

## Prolog Schema

```prolog
% Core concept definition
concept(Name, Page, Definition).
% e.g., concept(nash_equilibrium, 42, "A strategy profile where no player can benefit by unilaterally changing their strategy").

% Relationships between concepts
relates(Concept1, Concept2, RelationType).
% e.g., relates(nash_equilibrium, best_response, requires).

% Relation types:
% - requires: A requires understanding B
% - illustrates: A is an example of B
% - contrasts: A is opposed to or different from B
% - extends: A builds on or generalizes B
% - contains: A includes B as a component

% Examples and applications
example(Concept, Page, Description).
% e.g., example(prisoners_dilemma, 15, "Two suspects interrogated separately").

% Mathematical notation
formula(Concept, Page, Expression).
% e.g., formula(mixed_strategy, 87, "p*U(A) + (1-p)*U(B)").
```

## Project Structure

```
game-theory-extractor/
├── extract.py          # Main extraction loop
├── prompts.py          # Claude prompt templates
├── state.json          # Progress tracker (current page, errors)
├── output/
│   ├── knowledge.pl    # Accumulated Prolog facts
│   └── raw/            # Raw Claude responses (for debugging)
├── verify.pl           # Verification queries
└── pyproject.toml      # Dependencies: pypdf, anthropic
```

## Extraction Script

```python
def process_pdf(pdf_path: str, start_page: int = 1):
    reader = PdfReader(pdf_path)

    for page_num in range(start_page - 1, len(reader.pages)):
        text = reader.pages[page_num].extract_text()

        if not text or len(text) < 50:  # Skip empty/image pages
            log_skip(page_num + 1)
            continue

        prolog_facts = call_claude(text, page_num + 1)
        append_to_knowledge_base(prolog_facts)
        save_state(page_num + 1)

        time.sleep(0.5)  # Rate limiting
```

## Claude Prompt Template

```python
EXTRACTION_PROMPT = """You are extracting game theory concepts into Prolog facts.

Page {page_num} text:
\"\"\"
{page_text}
\"\"\"

Extract concepts, relationships, examples, and formulas from this page.
Output ONLY valid Prolog facts using these predicates:

concept(name, {page_num}, "definition").
relates(concept1, concept2, relation_type).
example(concept, {page_num}, "description").
formula(concept, {page_num}, "expression").

Rules:
- Use snake_case for concept names (nash_equilibrium, not "Nash Equilibrium")
- relation_type must be one of: requires, illustrates, contrasts, extends, contains
- If the page has no extractable concepts, output: % No concepts on this page
- Escape quotes in strings with backslash
- Each fact on its own line

Output facts only, no explanation."""
```

## Model Selection

- **Model:** claude-sonnet-4-20250514
- **Input per page:** ~1,500 tokens
- **Output per page:** ~200 tokens
- **Total:** ~640K input, 75K output
- **Estimated cost:** ~$2.50

## Verification Queries

```prolog
% Find undefined concepts (referenced but never defined)
undefined_concept(C) :-
    relates(C, _, _),
    \+ concept(C, _, _).
undefined_concept(C) :-
    relates(_, C, _),
    \+ concept(C, _, _).

% Find orphan concepts (defined but never related to anything)
orphan_concept(C) :-
    concept(C, _, _),
    \+ relates(C, _, _),
    \+ relates(_, C, _).

% Find duplicate definitions
duplicate_concept(C, Pages) :-
    findall(P, concept(C, P, _), Pages),
    length(Pages, N),
    N > 1.

% Validate relation types
invalid_relation(C1, C2, R) :-
    relates(C1, C2, R),
    \+ member(R, [requires, illustrates, contrasts, extends, contains]).
```

## Workflow

```
Phase 1: Automated Extraction (runs unattended)
─────────────────────────────────────────────────
1. python extract.py game-theory-101.pdf
2. Script iterates 377 pages, calls Claude for each
3. Prolog facts accumulate in output/knowledge.pl
4. Progress saved in state.json (resumable)
5. ~30-45 minutes runtime, ~$2.50 cost

Phase 2: Janus Verification (interactive)
─────────────────────────────────────────────────
1. Load knowledge.pl in Claude Code session
2. Run verification queries via Janus
3. Review undefined refs, orphans, duplicates
4. Fix issues (re-extract pages or manual edits)
5. Final knowledge base ready for queries
```

## Deliverables

- `game-theory-extractor/` - Complete Python project
- `output/knowledge.pl` - Prolog knowledge base (~2,000-5,000 facts estimated)
- `verify.pl` - Verification queries for ongoing QA

## Next Steps

1. Create `game-theory-extractor/` project structure
2. Implement `extract.py` with resumable state
3. Implement `prompts.py` with extraction template
4. Run extraction on full PDF
5. Verify with Janus queries

# -*- coding: utf-8 -*-
"""Claude prompt templates for game theory concept extraction."""

EXTRACTION_PROMPT = '''\
You are extracting game theory concepts into Prolog facts.

Page {page_num} text:
"""
{page_text}
"""

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
- For strings containing double quotes, double them: "He said ""hello"""
- Each fact on its own line
- For formulas: preserve mathematical structure even if symbols appear garbled
- Mark uncertain or complex formulas with: % FORMULA_CHECK_NEEDED
- Use ASCII approximations for symbols: >= for greater-equal, sum() for sigma, E[] for expected value

Output facts only, no explanation.'''

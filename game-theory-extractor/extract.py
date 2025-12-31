#!/usr/bin/env python3
"""Extract game theory concepts from PDF into Prolog knowledge base."""

import json
import os
import sys
import time
from pathlib import Path

import anthropic
from anthropic import APIError, RateLimitError
from pypdf import PdfReader

from prompts import EXTRACTION_PROMPT
from validate import validate_prolog_syntax

STATE_FILE = "state.json"
KNOWLEDGE_FILE = "output/knowledge.pl"
RAW_DIR = "output/raw"

# Ensure output directories exist
Path(RAW_DIR).mkdir(parents=True, exist_ok=True)


def load_state() -> int:
    """Load last successful page from state file. Returns 1 if no state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f).get("current_page", 1)
    return 1


def save_state(page_num: int) -> None:
    """Persist current page for crash recovery."""
    with open(STATE_FILE, "w") as f:
        json.dump({"current_page": page_num}, f)


def log_skip(page_num: int) -> None:
    """Log skipped pages (empty or too short)."""
    print(f"  [SKIP] Page {page_num}: empty or too short")


def log_error(page_num: int, error: Exception) -> None:
    """Log API errors."""
    print(f"  [ERROR] Page {page_num}: {error}")


def log_invalid_output(page_num: int, output: str) -> None:
    """Log invalid Prolog output."""
    print(f"  [INVALID] Page {page_num}: failed syntax validation")


def save_raw_response(page_num: int, response: str) -> None:
    """Save raw Claude response for debugging."""
    path = Path(RAW_DIR) / f"page_{page_num:03d}.txt"
    with open(path, "w") as f:
        f.write(response)


def append_to_knowledge_base(prolog_facts: str) -> None:
    """Append validated Prolog facts to knowledge base."""
    with open(KNOWLEDGE_FILE, "a") as f:
        f.write(prolog_facts)
        if not prolog_facts.endswith("\n"):
            f.write("\n")


def init_knowledge_base() -> None:
    """Initialize knowledge base with schema declarations."""
    if not os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "w") as f:
            f.write("""%% Game Theory Knowledge Base
%% Extracted from game-theory-101.pdf

:- dynamic concept/3.
:- dynamic relates/3.
:- dynamic example/3.
:- dynamic formula/3.

%% Relation types (declared as facts for validation):
valid_relation_type(requires).    % A requires B
valid_relation_type(illustrates). % A exemplifies B
valid_relation_type(contrasts).   % A opposes B
valid_relation_type(extends).     % A generalizes B
valid_relation_type(contains).    % A includes B

%% === Extracted Facts ===

""")


def call_claude(page_text: str, page_num: int) -> str:
    """Call Claude API to extract Prolog facts from page text."""
    client = anthropic.Anthropic()

    prompt = EXTRACTION_PROMPT.format(page_num=page_num, page_text=page_text)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def process_pdf(pdf_path: str, start_page: int | None = None, max_pages: int | None = None) -> None:
    """Process PDF and extract concepts to Prolog knowledge base.

    Args:
        pdf_path: Path to PDF file
        start_page: Page to start from (1-indexed). If None, resumes from state.
        max_pages: Maximum pages to process. If None, processes all.
    """
    if start_page is None:
        start_page = load_state()
        if start_page > 1:
            print(f"Resuming from page {start_page}")

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    if max_pages:
        end_page = min(start_page + max_pages - 1, total_pages)
    else:
        end_page = total_pages

    max_retries = 3

    print(f"Processing pages {start_page}-{end_page} of {total_pages} from {pdf_path}")
    init_knowledge_base()

    for page_num in range(start_page - 1, end_page):
        current_page = page_num + 1
        print(f"[{current_page}/{total_pages}] Processing page {current_page}...")

        text = reader.pages[page_num].extract_text()

        if not text or len(text) < 50:
            log_skip(current_page)
            save_state(current_page)
            continue

        for attempt in range(max_retries):
            try:
                prolog_facts = call_claude(text, current_page)

                # Add page marker comment
                facts_with_marker = f"\n% === Page {current_page} ===\n{prolog_facts}"

                if validate_prolog_syntax(prolog_facts):
                    append_to_knowledge_base(facts_with_marker)
                    save_state(current_page)
                    print(f"  [OK] Extracted facts from page {current_page}")
                else:
                    log_invalid_output(current_page, prolog_facts)
                    save_raw_response(current_page, prolog_facts)
                    save_state(current_page)
                break

            except RateLimitError:
                wait_time = 2 ** attempt
                print(f"  [RATE LIMIT] Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            except APIError as e:
                log_error(current_page, e)
                save_state(page_num)  # Resume from previous page
                if attempt == max_retries - 1:
                    raise

        time.sleep(0.5)  # Base rate limiting

    print(f"\nExtraction complete. Knowledge base saved to {KNOWLEDGE_FILE}")


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python extract.py <pdf_path> [start_page]")
        print("  pdf_path: Path to the PDF file")
        print("  start_page: Optional page to start from (overrides state.json)")
        sys.exit(1)

    pdf_path = sys.argv[1]
    start_page = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    process_pdf(pdf_path, start_page)


if __name__ == "__main__":
    main()

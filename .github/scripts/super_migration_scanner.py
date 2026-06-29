#!/usr/bin/env python3
"""
GAIA Super Migration Scanner

Scans GitHub issues for operative "magic" or ungrounded "metaphysical" language
and labels them `needs-super-migration` for triage.

Exempt patterns (Category 2 & 3 per docs/SUPER_VS_MAGIC.md):
  - "no magic" / "no magic numbers" / "no magic behavior"  -> idiomatic denial, already aligned
  - "magic link" (auth context)                           -> technical idiom
  - "magical conflation" (epistemic error label)          -> philosophy-of-science term
  - "Laws of Magic" only when inside a historical-quote block
  - "Magic Suspension Protocol" (governance doc title)    -> named legacy artifact
"""

import os
import re
from github import Github

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TOKEN      = os.environ["GITHUB_TOKEN"]
REPO_NAME  = os.environ["REPO"]
SINGLE_NUM = os.environ.get("ISSUE_NUMBER", "").strip()

FLAG_LABEL       = "needs-super-migration"
FLAG_LABEL_COLOR = "e11d48"   # deep red — high visibility
FLAG_LABEL_DESC  = "Issue contains operative magic/metaphysical language that needs migration to super/coherence framing per docs/SUPER_VS_MAGIC.md"

# Patterns that MUST be flagged (operative magic)
OPERATIVE_PATTERNS = [
    r'\bmagic\b(?!al conflation)(?! link)(?! number)(?!-number)',
    r'\bmagical\b(?! conflation)',
    r'\bspell(?:work|casting|s)?\b',
    r'\binvocation\b',
    r'\britual\b(?! review)',          # "ritual review" is a process term, not operative
    r'\bmystical\b',
    r'\bmysticism\b',
    r'\boccult\b',
    r'\bsorcery\b',
    r'\bwizardry\b',
    r'\balchemy\b(?! as metaphor)',    # alchemy-as-metaphor is a named T5 symbolic use
    r'\bsupernatural\b',
    r'\bmetaphysical(?!-as-symbolic)\b',  # raw metaphysical without tier label = flag
]

# Patterns that are EXEMPT (Category 2 & 3 — already aligned or governance)
EXEMPT_PATTERNS = [
    r'no magic',
    r'no.magic.numbers?',
    r'magic link',
    r'magical conflation',
    r'Magic Suspension Protocol',
    r'Laws of Magic.*historical',
    r'Old Term.*Magic Frame',          # mapping table in SUPERCOMPUTER_DOCTRINE
    r'category [23]',
    r'SUPER_VS_MAGIC',
    r'needs-super-migration',          # issue is already tagged; don't re-flag
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_exempt(text: str) -> bool:
    """Return True if the text contains only exempt magic references."""
    # Strip all exempt occurrences from the text before checking operative patterns
    cleaned = text
    for pattern in EXEMPT_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    return cleaned == text  # True = no operative patterns remain after stripping

def contains_operative_magic(text: str) -> bool:
    """Return True if text has operative magic language that is NOT exempt."""
    # First remove all exempt substrings
    cleaned = text
    for pattern in EXEMPT_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    # Now check if any operative pattern remains
    for pattern in OPERATIVE_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return True
    return False

def ensure_label(repo):
    """Create the needs-super-migration label if it doesn't exist."""
    try:
        repo.get_label(FLAG_LABEL)
    except Exception:
        repo.create_label(
            name=FLAG_LABEL,
            color=FLAG_LABEL_COLOR,
            description=FLAG_LABEL_DESC
        )
        print(f"Created label: {FLAG_LABEL}")

def scan_issue(issue) -> bool:
    """Scan a single issue. Returns True if flagged."""
    full_text = f"{issue.title or ''} {issue.body or ''}"
    if not contains_operative_magic(full_text):
        return False

    current_labels = [lbl.name for lbl in issue.labels]
    if FLAG_LABEL not in current_labels:
        issue.add_to_labels(FLAG_LABEL)
        print(f"  FLAGGED  #{issue.number}: {issue.title[:80]}")
    else:
        print(f"  ALREADY  #{issue.number}: {issue.title[:80]}")
    return True

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    g    = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)

    ensure_label(repo)

    if SINGLE_NUM:
        # Triggered by a single issue event
        issue = repo.get_issue(int(SINGLE_NUM))
        print(f"Scanning single issue #{SINGLE_NUM}...")
        flagged = scan_issue(issue)
        print(f"Result: {'FLAGGED' if flagged else 'CLEAN'}")
    else:
        # Scheduled / manual: scan ALL open issues
        print("Scanning all open issues...")
        open_issues = repo.get_issues(state='open')
        total = 0
        flagged = 0
        for issue in open_issues:
            # Skip pull requests (GitHub API includes them in issues)
            if issue.pull_request:
                continue
            total += 1
            if scan_issue(issue):
                flagged += 1
        print(f"\nScan complete: {flagged}/{total} issues flagged as needs-super-migration")

if __name__ == "__main__":
    main()

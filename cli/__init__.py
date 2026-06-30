"""
GAIA OS CLI.

The command-line interface to the GAIA Operating System.
Every command boots GAIA if not already live, then delegates
to the GAIAOSApi. The CLI is a thin, honest terminal skin over
the API — it adds formatting, colour, and ceremony but no logic.

Commands:
  gaia boot              — Boot the GAIA OS and print the manifest
  gaia status            — Print OS status
  gaia schumann          — Print Schumann resonance confirmation
  gaia gaian birth       — Run the interactive birth ceremony
  gaia gaian list        — List all registered GAIANs
  gaia gaian status ID   — Print one GAIAN's status
  gaia talk ID           — Start an interactive session with a GAIAN
  gaia memory recall ID  — Recall a GAIAN's memories
  gaia memory stats ID   — Print memory stats for a GAIAN
  gaia fs stats          — Print filesystem stats
  gaia fs integrity      — Run tamper-detection on all GAIAN homes
  gaia version           — Print GAIA OS version
"""

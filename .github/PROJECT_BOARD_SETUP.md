# GAIA Super Migration Command — Project Board Setup Guide

> **Status:** Active — June 29, 2026  
> **Purpose:** Step-by-step instructions to create the GitHub Projects v2 board that serves as the single unified view of the entire super migration effort.  
> **Cross-Reference:** `docs/SUPER_VS_MAGIC.md` · `.github/LABELS.md` · `.github/workflows/super-migration-scanner.yml`

---

## Why This Board Exists

With ~300+ issues in varying states of migration, no single mental model can hold the full picture. This board externalizes the map so the work becomes navigable rather than overwhelming. Once set up, you stop holding the system in your head — the system holds itself.

---

## Step 1 — Create Issue Types (Org Level)

Navigate to: **GitHub → Your Profile → Settings → Organizations → [Your Org] → Issue Types**

> If the repository is personal (not org), Issue Types are set per-repo under: **Repo → Settings → General → Issues → Issue Types**

Create these Issue Types:

| Type Name | Description | Icon |
|---|---|---|
| `Canon Migration` | Migrating canon docs from magic to super framing | 📜 |
| `Super Alignment` | Aligning code, comments, or UX to super/coherence language | ⚡ |
| `Feature` | New capability or system function | ✨ |
| `Bug` | Something broken or behaving incorrectly | 🐛 |
| `Research` | Investigation, hypothesis, or external reference work | 🔬 |
| `Infrastructure` | CI/CD, Docker, deployment, tooling | 🔧 |
| `Documentation` | Doc creation, update, or structural improvement | 📝 |

---

## Step 2 — Create Issue Fields (Org Level)

Navigate to: **GitHub → Your Profile → Settings → Organizations → [Your Org] → Issue Fields**

> Or per-repo: **Repo → Settings → General → Issues → Custom Fields**

Create these fields:

### Field 1: Migration Status
- **Type:** Single select  
- **Options:**
  - `magic-based` (🔴 red) — issue still uses operative magic language
  - `partially-migrated` (🟡 yellow) — some migration done, not complete
  - `super-aligned` (🟢 green) — fully migrated to super/coherence language
  - `migration-exempt` (⚪ grey) — Category 2/3 use, no migration needed
  - `not-applicable` (⚫ dark) — issue has nothing to do with terminology

### Field 2: Canon Layer
- **Type:** Single select  
- **Options:**
  - `T1 — Established Science`
  - `T2 — Strong Evidence`
  - `T3 — Promising Hypothesis`
  - `T4 — Traditional Knowledge`
  - `T5 — Symbolic/Poetic`
  - `T6 — Sacred Speculation`
  - `Non-epistemic` (code/infra/UI issues)

### Field 3: Sprint Wave
- **Type:** Single select  
- **Options:**
  - `Wave 1 — Doctrine & Renames`
  - `Wave 2 — Core Canon Semantics`
  - `Wave 3 — Governance & Meta`
  - `Wave 4 — Code & UX Cleanup`
  - `Wave 5 — Simulation & Proofs`
  - `Backlog`

### Field 4: Effort
- **Type:** Single select  
- **Options:**
  - `XS — < 30 min`
  - `S — 30 min–2 hrs`
  - `M — 2–4 hrs`
  - `L — 4–8 hrs`
  - `XL — > 8 hrs`

---

## Step 3 — Create the Project Board

1. Go to **github.com/[your-username]** → **Projects** → **New Project**
2. Name it: **`GAIA Super Migration Command`**
3. Description: *Single unified view of the magic→super migration effort across all issues and documents.*
4. Choose **Table** as default layout.

---

## Step 4 — Create Views

Inside the project, create these views:

### View 1: Full Table (Default)
- **Layout:** Table
- **Columns:** Issue # · Title · Issue Type · Migration Status · Canon Layer · Sprint Wave · Effort · Assignee · Labels
- **Sort:** Migration Status (magic-based first), then Priority
- **Filter:** None (shows everything)

### View 2: Migration Board (Kanban)
- **Layout:** Board
- **Group by:** Migration Status
- **Columns:** magic-based | partially-migrated | super-aligned | migration-exempt
- **Filter:** Label = `needs-super-migration` OR Issue Type = `Canon Migration` OR `Super Alignment`

### View 3: Sprint Waves (Roadmap)
- **Layout:** Board
- **Group by:** Sprint Wave
- **Columns:** Wave 1 | Wave 2 | Wave 3 | Wave 4 | Wave 5 | Backlog

### View 4: Active Sprint
- **Layout:** Board
- **Group by:** Status (Ready | In Progress | Review | Done)
- **Filter:** Sprint Wave = current wave
- **This is your daily working view.**

---

## Step 5 — Add All Existing Issues

1. In the Table view, click **Add items**
2. Search for the repository
3. Click **Add all open issues** (this bulk-adds all ~300+ issues)
4. The Super Migration Scanner will auto-label any issues containing operative magic language within 24 hours (or trigger it manually from Actions → Super Migration Scanner → Run workflow)

---

## Step 6 — Bulk Set Migration Status

After the scanner runs:

1. Filter Table view by label `needs-super-migration`
2. Select all flagged issues
3. Bulk-set `Migration Status` = `magic-based`
4. For all remaining issues, bulk-set `Migration Status` = `not-applicable` or manually classify as `super-aligned` / `migration-exempt`

This entire step should take 1–2 hours maximum with the table bulk-edit feature.

---

## Step 7 — Enable Automation

In the project, go to **Settings → Workflows** and enable:

- **Item added to project** → Set Status to `Ready`
- **Item closed** → Set Status to `Done`
- **Pull request merged** → Set Status to `Done`
- **Auto-archive items** → Archive `Done` items after 7 days

---

## Maintenance Protocol

Once the board is live, the weekly rhythm is:

1. **Monday:** Review any new `needs-super-migration` flags from the nightly scanner
2. **Mid-week:** Work issues in the Active Sprint view
3. **Friday:** Move completed issues to Done; pull next items from Sprint Wave backlog
4. **Monthly:** Review Wave progress; promote next Wave to active

---

## The Result

After setup, every issue in the system has:
- A **type** (what kind of work it is)
- A **migration status** (where it is in the magic→super journey)
- A **canon layer** (what epistemic tier it operates at)
- A **sprint wave** (when it gets worked)
- A **priority** and **effort** estimate

You stop holding the map in your head. The board holds the map. You hold the work.

---

*Order is not constraint. Order is the condition under which coherence becomes possible.*

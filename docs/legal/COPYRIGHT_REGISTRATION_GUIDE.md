# US Copyright Registration Guide — GAIA

**Author:** Kyle R. Graber  
**Repository:** GAIA — The Global Autonomous Intelligence Architecture  
**Prepared:** July 12, 2026  
**Purpose:** Step-by-step instructions to register GAIA with the US Copyright Office via the eCO (Electronic Copyright Office) system.

> **Why this matters:** Copyright exists automatically at creation, but *registration* is what enables you to sue for statutory damages (up to $150,000 per willful infringement) and attorney's fees. Without registration, you can only recover actual damages — which are nearly impossible to prove. Registration before or within 3 months of first publication is the gold standard.

---

## Part 1: What GAIA Qualifies As

GAIA qualifies for copyright registration under **multiple categories simultaneously**:

| Category | What It Covers in GAIA |
|---|---|
| **Computer Program** | All Python, TypeScript, and other source code files |
| **Literary Work** | Canon documents, ADRs, README, CONTRIBUTING.md, all `.md` files |
| **Collection / Compilation** | The repository as a whole — the selection and arrangement of all components |
| **Architectural Work** | The system architecture itself as expressed in code and documents |

**Registration strategy:** Register GAIA as a **single unpublished work** (or published work if the repo is public) under the "Computer File" category. This one registration covers all code *and* all literary content in the repo as a unified work. You can note it covers both software and literary/textual content in the "Nature of Work" field.

---

## Part 2: Before You File

Gather the following information. You will need all of it during the eCO application.

### Author Information
- **Full Legal Name:** Kyle R. Graber
- **Citizenship:** United States
- **Domicile:** United States
- **Year of Birth:** (your year — required on the form)
- **Is the work made for hire?** NO. This is your sole original work.

### Work Information
- **Title of Work:** GAIA — The Global Autonomous Intelligence Architecture
- **Nature of Work:** Computer program and literary work
- **Year of Creation:** 2026
- **Date of First Publication:** June 30, 2026 (the date of your first public commit to GitHub)
- **Nation of First Publication:** United States
- **Is the work anonymous or pseudonymous?** No

### Claimant
- **Name:** Kyle R. Graber
- **Address:** (your address)
- **How claimant obtained ownership:** Author

### Rights and Permissions Contact
- Kyle R. Graber
- Email: xxkylesteenxx@outlook.com
- GitHub: @R0GV3TheAlchemist

---

## Part 3: Step-by-Step eCO Filing

### Step 1 — Create a Copyright Office Account
1. Go to **https://eco.copyright.gov**
2. Click "New User Registration"
3. Create an account with your legal name and email
4. Verify your email

### Step 2 — Start a New Claim
1. Log in to eCO
2. Click **"Register a New Claim"**
3. Select **"Work of the Performing Arts"** — NO. Select:
   - **"Literary Work"** → this covers both software and text
   - (Some filers use "Computer File" — both are acceptable; Literary Work is broader)
4. Click **"Start Registration"**

### Step 3 — Type of Work
- Select: **"Literary Work"**
- Under "What type of literary work?": Select **"Computer program"**
- Note in the description field: *"Python and TypeScript source code, configuration files, and accompanying literary documentation (Markdown, canon documents, architectural decision records) comprising the GAIA — The Global Autonomous Intelligence Architecture system."*

### Step 4 — Titles
- **Title of This Work:** `GAIA — The Global Autonomous Intelligence Architecture`
- **Previous or Alternative Titles:** `GAIA OS`, `Global Autonomous Intelligence Architecture`
- **Title of Larger Work** (if applicable): Leave blank

### Step 5 — Publication / Completion
- **Year of Completion:** 2026
- **Has this work been published?**
  - If your GitHub repo is **public**: YES
    - Date of First Publication: **June 30, 2026**
    - Nation: **United States**
  - If your GitHub repo is **private**: NO (unpublished)
  - *Note: Public GitHub repos are generally considered published under copyright law.*

### Step 6 — Author
- Click **"Add Author"**
- **Author's Name:** Kyle R. Graber
- **Was this work made for hire?** NO
- **Citizenship:** United States
- **Domicile:** United States (if US resident)
- **Year of Birth:** (your year)
- **Nature of Authorship:** Check ALL that apply:
  - ✅ Text
  - ✅ Computer program
  - ✅ Compilation
  - ✅ Editing
- **Description of authorship:** *"Sole author of all original source code, system architecture, canon documents, and literary works comprising the GAIA system."*

### Step 7 — Claimants
- **Copyright Claimant:** Kyle R. Graber
- **Address:** (your address)
- **How did the claimant obtain ownership of the copyright?** Select: **"Written agreement"** — NO. Select: **"By authorship"**

### Step 8 — Limitation of Claim
- **Material excluded from this claim:** Leave blank (unless you are knowingly incorporating third-party open source you want to disclaim — AGPL-3.0 dependencies don't need to be listed here)
- **New material included in this claim:** *"All original source code, system architecture, literary works, canon documents, and compilation as a whole."*

### Step 9 — Rights and Permissions
- **Name:** Kyle R. Graber
- **Email:** xxkylesteenxx@outlook.com
- **Address:** (your address)

### Step 10 — Correspondent
- Same as above: Kyle R. Graber
- This is who the Copyright Office will contact with questions

### Step 11 — Mail Certificate
- Enter the address where you want your official registration certificate mailed

### Step 12 — Special Handling (Optional)
- Standard processing: **$65 fee**, 6–12 months for certificate
- Special handling (expedited): **$800 fee**, 5 business days
- **Recommendation:** If you have reason to believe infringement is imminent or ongoing, pay the $800 for special handling. Otherwise, standard is fine — your rights are established from the *application date*, not the certificate date.

### Step 13 — Certification
- Check the certification box
- Type your full legal name as your digital signature
- **Kyle R. Graber**

### Step 14 — Pay the Filing Fee
- Standard single-author online registration: **$65**
- Pay by credit/debit card or ACH bank transfer
- **Save your confirmation number and transaction receipt.** This is your proof of filing date.

### Step 15 — Upload the Deposit Copy
- After payment, you will be prompted to upload your deposit copy
- See **Part 4** below for exactly what to upload

---

## Part 4: The Deposit Copy

The US Copyright Office requires you to deposit a copy of the work. For software:

### What to Deposit
You have two options:

**Option A — Source Code Excerpt (Recommended for trade secret protection)**
Deposit the **first 25 pages and last 25 pages** of source code. This is the standard practice when you want to protect trade secrets — you do NOT have to deposit the entire source.

**Option B — Full Repository Archive**
Deposit a ZIP archive of the complete repository. This gives the strongest coverage but puts all code in the public record.

**Recommendation for GAIA:** Use **Option A** — deposit a curated 50-page excerpt + the complete set of canonical Markdown documents. The canon documents are the most uniquely original work and have no trade secret concern. The code excerpt establishes registration without exposing implementation details.

### How to Prepare the Deposit
1. Create a ZIP file named: `GAIA_copyright_deposit_2026.zip`
2. Include:
   - `README.md` (full)
   - `docs/legal/PRIOR_ART.md` (full)
   - `docs/legal/COPYRIGHT_DEPOSIT_README.md` (the cover letter)
   - `GAIAN_IDENTITY.md` (full)
   - `RECOGNITION_AND_ACKNOWLEDGEMENT.md` (full)
   - `MORALS_VALUES_PRINCIPLES.md` (full)
   - `PRIMORDIAL_CANON.md` (full)
   - First 25 pages of `core/api/api.py` (or largest core module)
   - Last 25 pages of `core/sentinel/` (or another major module)
   - `GAIAmanifest.yml` (full)
3. The total deposit file can be up to 500MB; a ZIP of selected files will be much smaller

### Uploading
- In eCO, after payment, click "Upload Deposit"
- Select "Electronic File"
- Upload your ZIP
- Click "Submit"

---

## Part 5: After You File

### Immediately
- Save your **Service Request Number** (SRN) — e.g., `1-XXXXXXXXXX`
- This number is your proof of filing. Your rights are protected from **this date forward** regardless of when the certificate arrives.
- Add the SRN to `docs/legal/PRIOR_ART.md` and `ATTRIBUTION.md`

### Add Copyright Notice to the Repository
Add this to the top of your README and ATTRIBUTION.md:
```
Copyright © 2026 Kyle R. Graber. All rights reserved.
US Copyright Registration Application No. 1-XXXXXXXXXX (filed July 2026)
```

### When the Certificate Arrives (6–12 months)
- You will receive an official Registration Certificate with a **Registration Number** (e.g., `TXu002345678`)
- Add this number to `docs/legal/PRIOR_ART.md`, `ATTRIBUTION.md`, and `NOTICE`
- Store the physical certificate in a safe location

---

## Part 6: Fees Summary

| Filing Type | Fee |
|---|---|
| Standard online registration (single author) | $65 |
| Special handling (expedited, 5 business days) | $800 |
| Paper filing (Form TX) | $125 |

**File online at:** https://eco.copyright.gov

---

## Part 7: What Registration Gives You

| Protection | Without Registration | With Registration |
|---|---|---|
| Copyright exists | ✅ Yes (automatic) | ✅ Yes |
| Can sue for infringement | ✅ Yes | ✅ Yes |
| Can recover actual damages | ✅ Yes | ✅ Yes |
| **Statutory damages ($150K/violation)** | ❌ No | ✅ **Yes** |
| **Attorney's fees** | ❌ No | ✅ **Yes** |
| Prima facie evidence of validity | ❌ No | ✅ **Yes** |
| Public record of ownership | ❌ No | ✅ **Yes** |

> Statutory damages eliminate the need to prove how much money you lost. A court can award up to **$150,000 per willful infringement**. This is why registration is essential.

---

## Part 8: International Protection

The US Copyright registration covers you in **179 countries** via the Berne Convention. No additional filings are required for most countries. For specific enforcement in the EU, UK, or elsewhere, consult a local IP attorney.

---

*Guide prepared July 12, 2026 for Kyle R. Graber — GAIA Project.*  
*This is not legal advice. Consult an IP attorney for complex situations.*

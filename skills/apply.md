---
name: apply
description: End-to-end job application pipeline from JD URL to submitted confirmation. Tailors a resume + cover letter to the JD keywords, validates against profile rules, and submits via Greenhouse/Lever/Ashby. Defaults to --no-submit (review first) unless told to ship.
---

# /apply — Reusable Application Pipeline

End-to-end pipeline from JD URL to submitted confirmation, tuned for Claude Code + browser MCP. Targets ~35 tool calls per submission instead of the 80 a manual run takes.

## Pre-flight

Reads `profile.yml` for:
- `apply.base_resume` — path to your canonical resume (markdown). If empty, skill runs in submit-only mode (no tailoring).
- `apply.application_profile` — path to a JSON file of autofill data (name, phone, links, "why this company" stems).
- `apply.output_dir` — where per-application folders are written (default `~/.job-radar/applications/`).
- `apply.default_no_submit` — if true (default), pipeline halts after render; you submit manually.
- `identity.*` — used in the cover letter and form fields.
- `visa.enabled` — if true, runs an eligibility gate before tailoring.

## Inputs

```
/apply <jd-url> [flags]

Flags:
  --no-submit         (default if apply.default_no_submit=true) Stop after render. Review PDFs, then re-run with --submit-only.
  --submit-only       Skip tailor/render. Use existing materials in <output_dir>/<slug>/. Just submit.
  --cold              Bypass warm-line check. By default, halts if a warm contact is found in radar.db.
  --skip-recon        Skip the visa eligibility gate (only relevant if visa.enabled).
```

## Pipeline (7 phases)

### Phase 0: Pre-flight context (parallel)

Run in parallel:
1. `WebFetch <jd-url>` → save raw text to `<output_dir>/<slug>/jd.txt`
2. Read `profile.apply.base_resume` (canonical resume markdown)
3. Read `profile.apply.application_profile` (autofill JSON)

If `base_resume` is unset, jump to Phase 6 in submit-only mode.

### Phase 1: Eligibility gate (only if visa.enabled)

```
if profile.visa.enabled is false:
    skip this phase (citizens / PRs do not need it)

else:
    company_lower = lower(company)
    run visa/lca_lookup.py annotate(company)
    if verdict == 'STRONG' or 'LIKELY':
        eligibility = "PASS"
    elif verdict == 'UNVERIFIED' and JD has explicit sponsorship language:
        eligibility = "PASS (JD-stated)"
    else:
        halt with: "Visa-recon UNVERIFIED for {company}. Re-run with --skip-recon if you have other context."
```

### Phase 2: Warm-line check

```
contacts = sqlite3 ~/.job-radar/radar.db "SELECT * FROM contacts WHERE company = '<company>'"
if contacts AND not --cold:
    halt with: "Warm contact found at {company}. Run /warm-line <company> first.
                Or re-run /apply with --cold."
```

### Phase 3: Tailor materials

1. **Resume** at `<output_dir>/<slug>/resume.md`:
   - Load base from `profile.apply.base_resume`.
   - Extract verbatim keywords from JD (run a JD-keyword pass, mirror the JD's exact phrasing in matching skill / bullet sentences).
   - Strip em dashes (replace with comma, colon, or "and") — strongest AI-writing tell.

2. **Cover letter** at `<output_dir>/<slug>/cover_letter.md`:
   - 3 paragraphs. Lead mirrors JD's headline keywords. Middle paragraph evidences your proof points. Closing ties to the company's stated value.

3. **"Why this company?" starter** at `<output_dir>/<slug>/_why_company_starter.md`:
   - 3-paragraph draft.
   - Mark with `// REVIEW REQUIRED — operator must own this paragraph before submission`.

### Phase 4: Validate before render

If the user has a custom validation script (e.g. `profile.apply.validate_script`), run it. Otherwise, run these mechanical checks:

```bash
# em dashes (strongest AI-writing tell)
grep -c "—" <output_dir>/<slug>/resume.md  # must be 0
grep -c "—" <output_dir>/<slug>/cover_letter.md  # must be 0

# graduation year leak (if profile.apply.no_grad_year=true)
grep -E "20[0-2][0-9]" <output_dir>/<slug>/resume.md  # inspect, year-only matches should not be a grad year
```

Non-zero exit on any required check halts the pipeline.

### Phase 5: Render (one shot)

Render via pandoc + weasyprint (the most universal CSS-respecting renderer):

```bash
pandoc <output_dir>/<slug>/resume.md \
  -o <output_dir>/<slug>/resume.pdf \
  --pdf-engine=weasyprint \
  --css="<path-to-shared-css>"

pandoc <output_dir>/<slug>/cover_letter.md \
  -o <output_dir>/<slug>/cover_letter.pdf \
  --pdf-engine=weasyprint \
  --css="<path-to-shared-css>"
```

If `profile.apply.shared_css` is set, use it. Otherwise weasyprint's default works (sane defaults, just verify page count <= 3).

If page count > 3 (resume) or > 1.5 (cover), halt and ask the operator to trim.

If `--no-submit`, stop here. Print review checklist:
- Open `<output_dir>/<slug>/resume.pdf` for visual review
- Open `<output_dir>/<slug>/_why_company_starter.md` and finalize the custom essay
- When ready, re-run with `--submit-only`

### Phase 6: Submit (browser flow)

Navigate to JD URL via chrome-devtools MCP (or playwright MCP).

**Resume upload** (1 round trip):
```
browser_click(Resume/CV "Attach" button) → file_chooser opens
browser_file_upload([resume.pdf])
```

**Textbox batch** (1 round trip via `browser_fill_form`):
Iterate the autofill profile. Build a single `fill_form` call with name, email, phone, LinkedIn, current company, current title, location, remote preference.

**Cover letter** (1 round trip):
Type cover letter body into "Additional Information" textarea.

**"Why this company?"** (1 round trip):
Type operator-finalized text from `_why_company_starter.md`. If file still contains `// REVIEW REQUIRED`, halt with: "Custom essay not finalized."

**Custom dropdowns** (2 round trips each):
For each form dropdown (eligibility, EEO, etc.):
1. `browser_click(combobox)` to expand
2. Read options, then `browser_click(option-id-matching-default)`

**Phone country dropdown** (Greenhouse-specific):
1. `browser_click(country combobox)`
2. `browser_click('#react-select-country-option-0')` (United States) — or the appropriate index for the user's country

**Submit click**.

**Verification code handling**:
```
text = browser_evaluate(() => document.body.innerText)
if "verification code" in text:
    code = retrieve_via_gmail()  # search 'from:no-reply@us.greenhouse-mail.io subject:"Security code" newer_than:5m'
    fill_split_input(code)        # use native-setter pattern, not browser_type
    Submit again
```

### Phase 7: Persist

Three writes in parallel:

1. `<output_dir>/<slug>/submitted-<timestamp>.md` — full submission record
2. `<output_dir>/<slug>/STATUS.md` — one-liner for parallel-session coordination
3. `~/.job-radar/radar.db` — insert into `applications` (status='applied', date_applied, source, job_url, salary_range, location, remote_policy, notes, warm_line)

## Failure-mode playbook

| Symptom | Cause | Fix |
|---|---|---|
| Resume PDF > 3 pages | Content too dense | Trim Skills section first, then early-career bullets |
| Em dashes appear in render | Base resume contains them | Run sed replacement in Phase 3 |
| Submit returns "Country / Select a country" error | Phone country react-select is required | Click country combobox + select option-0 |
| browser_type only fills first slot of split input | React focus + synthetic event handler | Use JS-injected native-setter pattern |
| Gmail returns empty for verification | Wrong sender pattern | Greenhouse uses `from:no-reply@us.greenhouse-mail.io subject:"Security code"` |

## What this skill deliberately does NOT do

- Generate the "Why <Company>?" essay end-to-end. The operator owns that paragraph. Skill drafts a starter, marks it for review, halts submit until reviewed.
- Render DOCX. ATS forms accept PDF. Add support later if needed.
- Auto-send DMs. Outreach lives in `/warm-line`.

## Companion skills

- `/job-radar` — surface the next pick
- `/warm-line <company>` — runs before this, surfaces leverage path
- `/job-radar-linkedin` — feeds the pipeline

## Note on tailoring quality

This skill ships a basic JD-mirror tailor. **Real tailoring quality depends on the depth of your evidence bank** — the set of concrete scope points, metrics, and projects you can pull from. The base resume in `profile.apply.base_resume` is the floor; richer evidence pulled from a separate "experience ledger" produces better matches.

If you're shipping many applications, consider building an evidence bank: a markdown file or SQLite table of every concrete bullet you might use (with context, dates, metrics), then have Claude select the best subset per JD.

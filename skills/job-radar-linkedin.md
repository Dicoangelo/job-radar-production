---
name: job-radar-linkedin
description: Free LinkedIn-Premium replacement. Ingests the LinkedIn job-alert emails already landing in Gmail, parses the structured subject lines into scored deduped rows in radar.db's job_postings table, and wires named connections into contacts as warm-line signal. No Premium, no scraping, no API spend. Loopable.
---

# Job Radar — LinkedIn Alert Ingest

LinkedIn's free job-alert emails are pre-filtered to your saved searches and carry a signal Premium's UI buried: **the warm-line line** ("Pat Example · 5 connections"). That signal is what `/job-radar` and `/warm-line` read out of the `contacts` table. This skill turns the inbox into structured pipeline.

## Pre-flight

- Requires the Claude Code Gmail MCP authenticated for the user's inbox.
- Requires `profile.gmail.enabled: true`.
- Reads `profile.gmail.linkedin_alert_sender` (default `jobalerts-noreply@linkedin.com`) and `profile.gmail.ingest_window` (default `newer_than:30h`).

## Architecture

```
Gmail (jobalerts-noreply@linkedin.com)
   ↓  Claude Gmail MCP — search_threads (sender query, NOT label)
subject-line parse → JSON job cards
   ↓  pipe to engine/linkedin_ingest.py
radar.db: job_postings (source=linkedin_alert) + contacts (warm-line)
   ↓
/job-radar ranks with warm-line joins  →  /apply
```

## Run

### 1. Pull the alert corpus

**Use the sender query, not a label.** Gmail labels often return empty through the MCP even when mail is labelled — a known quirk. The sender query is reliable:

```
mcp__claude_ai_Gmail__search_threads(
  query='from:jobalerts-noreply@linkedin.com newer_than:30h',
  pageSize=40)
```

For a one-off backfill, widen to `newer_than:10d`. For the daily loop, keep `newer_than:30h` (alerts fire ~every 2h; 30h gives overlap so nothing is missed across a missed run — dedup handles overlap).

### 2. Parse subject lines (no body fetch needed for triage)

LinkedIn encodes the entire triage payload in the subject. Two patterns:

- **Pattern A (saved-alert digest):**
  `"<saved-alert-name>": <Company> - <Role> posted on <M/D/YY>`
  Regex: `^["'](?P<alert>[^"']+)["']:\s*(?P<company>.+?)\s+-\s+(?P<role>.+?)\s+posted on\s+(?P<posted>\d{1,2}/\d{1,2}/\d{2,4})`

- **Pattern B (single-job alert):**
  `<Role> at <Company>`
  Regex: `^(?P<role>.+?)\s+ at\s+(?P<company>.+)$` → set `alert="single-job"`

Build a JSON array of cards: `{company, role, posted (ISO), alert, location?}`. Convert `M/D/YY` → `YYYY-MM-DD`. Location is not in the subject; leave it null (the scorer handles empty location).

### 3. (Optional, top-of-shortlist only) Body fetch for warm-line + Easy Apply

Do **not** `get_thread` all 40 emails — round-trip waste for zero triage gain. The subject line is 100% of the ranking signal. Fetch bodies **only** for roles that survive to the top of the shortlist, to extract:
- `named_connection` (the "<Name> · N connections" / "N school alum" line — warm-line gold)
- `easy_apply` (presence of an "Easy Apply" badge → flag for direct-ATS resolution)
- a direct job URL if present

Add those fields to the relevant cards before the final ingest, or run a second enrichment pass.

### 4. Ingest

```bash
echo '<json-array>' | python3 ~/.job-radar/engine/linkedin_ingest.py
```

The script prints a one-screen radar report and is idempotent — re-running across overlapping windows updates `last_seen_at` and never duplicates postings or contacts.

## Output

Print the script's report verbatim — it is already in radar format. Do not add a wall of commentary.

## LinkedIn EasyApply rule

Every row this skill surfaces is a **lead**, not an apply target. Before `/apply`:
1. Resolve the role to its **direct ATS** (company careers page / Greenhouse / Lever / Ashby / Workday).
2. Apply there. LinkedIn EasyApply has near-zero response in most lanes; the direct ATS is the working channel.

The job_postings row's `url` is a LinkedIn search fallback; `/apply` or `/job-radar-firecrawl` resolves the real ATS link.

## Warm-line wiring

When a card has `named_connection`, the script upserts a `contacts` row with `relationship='linkedin_connection'`. This lights up:
- `/job-radar`'s warm-line annotation
- `/warm-line` Tier 2/Tier 3 ranking

The contact is a **candidate**, not a verified relationship — the note records this. `/warm-line <company>` verifies degree/strength before any outreach.

## Loop

```
/loop 24h /job-radar-linkedin
```

Daily ingest with `newer_than:30h`. Idempotent, so loop overlap is safe.

## Notes for Claude

- Subject-line parse is the contract. If LinkedIn changes the subject format, fix the two regexes above; don't fall back to brittle body scraping.
- The scorer is shared with the ATS pipeline. A false-negative here is a false-negative there too — fix it once in `profile.yml` by adding a lane signal.
- Do not re-surface already-applied roles. The script dedups against `applications` all-time, all-status (company + fuzzy role, 0.92 ratio). Applied / rejected / withdrawn / ghosted — never resurfaces.
- `+0 warm-line contacts` on a re-run is correct, not a bug — it means connections were already in `contacts` (idempotent).
- One screen. Same compression discipline as `/job-radar`.

## Files

- Skill: `~/.claude/commands/job-radar-linkedin.md` (this file)
- Engine: `~/.job-radar/engine/linkedin_ingest.py`
- Shared scorer: `~/.job-radar/engine/scorer.py`
- Output table: `~/.job-radar/radar.db` → `job_postings` (source=`linkedin_alert`) + `contacts`

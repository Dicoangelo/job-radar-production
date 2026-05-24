---
name: job-radar
description: Daily job intelligence packed down to one concrete pick. Runs the ATS scraper pipeline against the targets in profile.yml, ranks by score + warm-line + (optional) visa annotation, then emits ONE top pick plus 3 backups. Loopable.
---

# Job Radar — Packed Down

Goal: produce one concrete next-pick in under 60 seconds. Not a wall of options.

## Pre-flight

This skill reads `profile.yml` (resolved from `$JOB_RADAR_PROFILE`, then `~/.job-radar/profile.yml`, then `./profile.yml`). If no profile exists, halt and tell the user to run `install.sh` or copy an example from `examples/profile.*.yml`.

## Run

```bash
cd ~/.job-radar/engine    # or wherever install.sh placed the engine
python3 discover.py             # ATS scan, writes to ~/.job-radar/radar.db
python3 briefing.py > /tmp/radar.md   # raw output, do not display
```

If `discover.py` errors on a specific company, surface the company name + error class once. Don't dump full stack traces.

## Filter and rank (Claude does this against radar.db, not Python)

After the pipeline runs, query `~/.job-radar/radar.db` and apply these filters:

1. **Location filter:** keep only rows whose `location` matches `profile.location_whitelist`. The scorer already penalized off-whitelist locations; you can choose to drop them entirely here or leave them in.

2. **Title blocklist:** the scorer already dropped these to `lane='unfit'`. Treat any row with `lane='unfit'` as suppressed.

3. **Dedup:** when the same (company, role) appears N times across geos, keep only the highest-score row.

4. **Visa annotation (only if `profile.visa.enabled` is true):** run this query against `~/.job-radar/lca.db`:
   ```sql
   SELECT COUNT(*) AS lca_count, ROUND(AVG(wage_rate_from), 0) AS avg_wage
   FROM lca_filings
   WHERE employer_normalized LIKE '%' || lower('<company>') || '%'
     AND decision_date >= date('now', '-3 years');
   ```
   Annotate with `[VISA: STRONG]` if count >= 50, `[VISA: LIKELY]` if 5-49, `[VISA: UNVERIFIED]` if < 5. If `profile.visa.enabled` is false, skip this step entirely — citizens and PRs do not need it.

5. **Warm-line annotation:** for each remaining row, query the contacts table:
   ```sql
   SELECT COUNT(*) AS connections
   FROM contacts
   WHERE company LIKE '%' || lower('<company>') || '%';
   ```
   Annotate with `[WARM: N]`. If N >= 1, this is a warm-line-locked candidate; if N = 0, warm-line-needed.

6. **Already-applied filter:** suppress any row where `(company, role)` already exists in `applications` (any status). The briefing's shortlist query already does this — trust it.

7. **Final rank:** order by — (1) rows with `[WARM: >=1]` first, then (2) rows visa-STRONG (if visa enabled), then (3) rows by raw score. Use `profile.output.shortlist_threshold` as the floor.

## Output (this is what Claude prints)

Use this exact format. One screen. No wall of postings.

```
JOB RADAR <YYYY-MM-DD>

TOP PICK
  Company:     <name>
  Role:        <title>
  URL:         <url>
  Score:       <N>
  Visa:        <STRONG/LIKELY/UNVERIFIED — only if visa enabled, else omit>
  Warm-line:   <N connections> (<top contact name if any>)
  Why:         <1-2 sentences: lane fit + warm-line + visa>
  Action:      paste this into your apply session:
                 JD URL: <url>
                 Warm-line: <draft DM ready or "needs LinkedIn scan">

BACKUPS
  1. <company> — <role> · <score> · <warm> — <url>
  2. <company> — <role> · <score> · <warm> — <url>
  3. <company> — <role> · <score> · <warm> — <url>

PIPELINE
  Shortlist after filters: <N>
  Warm-line locked:        <N>
  Stale (>14d):            <N>
  Already applied:         <N>
```

That is the entire output. No methodology section, no "Do NOT" list.

## Output counts

`profile.output.top_pick_count` and `profile.output.backup_count` control the cardinality. Defaults are 1 top + 3 backups. If a user wants a different shape, they edit the profile.

## Skip lists (suppress in output)

- Companies the user has applied to 3+ times with no response (per `profile.warm_line.ats_block_threshold`).
- Companies tagged `notes LIKE '%do not apply%'` in `target_companies`.
- Rows with `status='stale'` (>7 days unseen by the scraper).

## Loop

```
/loop 24h /job-radar
```

Daily run. Skill output is one screen. Briefings persist at `~/.job-radar/briefings/YYYY-MM-DD.md`.

## Notes for Claude

- Do not list more than `profile.output.top_pick_count + profile.output.backup_count` rows. Compression is the point of this skill.
- Do not paste the raw briefing markdown into the response. The briefing is internal data; the skill output is the report above.
- The visa annotation is **optional**. If `profile.visa.enabled` is false (default), omit the Visa: line entirely.
- If `discover.py` fails (no internet, bad slug), surface the failure but still rank whatever's in the DB from prior runs.
- This skill does not tailor or apply. Pair with `/warm-line` (next step before applying) and `/apply` (when ready to submit).

## Companion skills

- `/job-radar-linkedin` — free LinkedIn alert ingest, runs alongside the ATS scraper
- `/job-radar-firecrawl` — paid broad-web variant
- `/warm-line <company>` — surfaces warm-line leverage before applying
- `/apply <jd-url>` — end-to-end apply pipeline (tailor + submit)

## Claude.ai (web/desktop) fallback

This skill is built for Claude Code (CLI). On Claude.ai web/desktop:
1. The engine still runs locally (Python + SQLite, no Claude required).
2. Run `python3 ~/.job-radar/engine/discover.py && python3 ~/.job-radar/engine/briefing.py` in your terminal.
3. Paste the briefing into Claude.ai as project knowledge.
4. Use this skill's body as the system prompt for that conversation.

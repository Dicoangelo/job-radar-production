---
name: job-radar-firecrawl
description: Paid-API variant of /job-radar using Firecrawl search across the live web. Broader, fresher coverage than the ATS scraper. Skips dead channels (LinkedIn EasyApply), prefers direct careers pages. Use when willing to spend Firecrawl credits for higher-quality discovery.
---

# Job Radar — Firecrawl Build

Paid-API variant of `/job-radar`. The default radar scans the ATS boards listed in `profile.targets`; this variant uses **Firecrawl `search`** to query the live web across job boards, then `scrape` the top candidates for full JD analysis.

**Pre-flight:**
- Requires `profile.firecrawl.enabled: true` and `FIRECRAWL_API_KEY` in env.
- Reads `profile.firecrawl.search_queries` for the query list.
- Reads `profile.firecrawl.credit_warn_threshold` to warn on low credit balance.

**When to use this over `/job-radar`:**
- Fresh coverage (last 24-72h) across boards the ATS scraper doesn't index
- Willing to spend ~5-15 Firecrawl credits per run
- Bypass LinkedIn EasyApply and find the same role on the company's direct ATS

**When to use `/job-radar` instead:**
- Daily routine, no API spend
- The ATS pipeline's accumulated history + dedup is enough

## Goal

Same as `/job-radar`: one concrete top pick + 3 backups. Not a wall of options.

## Discovery layer — Firecrawl

For each query in `profile.firecrawl.search_queries`, run:

```bash
firecrawl search "<query>" --limit 10
```

Save results. Each result has `URL`, `title`, `description` — enough to triage.

## Channel filter (apply immediately after search)

- **DROP** any URL matching `linkedin.com/jobs` (EasyApply has near-zero response)
- **DOWNRANK** URLs from staffing agencies (acarasolutions, aleron, robertwalters, randstad, kellyservices, manpower, hays, etc.)
- **PREFER** in this order:
  1. Direct careers pages (`careers.<company>.com`, `<company>.com/careers`)
  2. Ashby (`jobs.ashbyhq.com`)
  3. Lever (`jobs.lever.co`)
  4. Greenhouse (`boards.greenhouse.io`, `job-boards.greenhouse.io`)
  5. Workday (`myworkdayjobs.com`) — flag as opaque

If a role surfaces on LinkedIn but ALSO has a direct careers page or ATS posting, route to the direct version.

## Discovery refinement — direct ATS lookup

For roles that look in-lane but only surface on LinkedIn, do a follow-up search:

```bash
firecrawl search "<exact title> <company> careers" --limit 3
firecrawl search "site:jobs.lever.co <company> <title>" --limit 3
firecrawl search "site:jobs.ashbyhq.com <company> <title>" --limit 3
firecrawl search "site:boards.greenhouse.io <company> <title>" --limit 3
```

If no direct version exists and the role is high-fit, decide: skip (per EasyApply rule) or flag as warm-line-only.

## Scrape JDs for top candidates

After channel filter, scrape 5-7 best matches:

```bash
firecrawl scrape "<url>" --format markdown
```

## Score with the same engine

Pass each scraped JD's markdown into `engine/scorer.py`. Same scoring brain as `/job-radar` — no second source of truth.

```bash
python3 -c "
import sys
sys.path.insert(0, '$HOME/.job-radar/engine')
import scorer
print(scorer.score_posting('<role>', '<description>', '<location>'))
"
```

## radar.db cross-reference

Same as `/job-radar` — annotate visa (if enabled), warm-line, and already-applied status per row from `~/.job-radar/radar.db`.

## Output

Same format as `/job-radar` (one top pick + 3 backups), with one addition:

```
JOB RADAR (FIRECRAWL) <YYYY-MM-DD>

DISCOVERY METRIC
  Queries run:           <N>
  Raw results:           <N>
  After channel filter:  <N>  (dropped: <N> LinkedIn, <N> staffing agency)
  After scoring:         <N>
  Firecrawl credits used: ~<N>

TOP PICK
  [same format as /job-radar]

BACKUPS
  1-3. <same format as /job-radar>

PIPELINE CONTRAST
  Roles surfaced here, NOT in /job-radar ATS pipeline: <list>
  (this is where the Firecrawl variant earns its credits)
```

## Cost guardrails

- One run targets ~10-15 Firecrawl credits.
- If `--cheap` is passed (TODO), skip the JD scrape step — only return search-result-level triage (~5 credits).
- If `firecrawl --status` shows balance < `profile.firecrawl.credit_warn_threshold`, warn before running.

## Notes for Claude

- The ATS pipeline still owns dedup, history, and warm-line joins; this skill only handles discovery + ATS-channel-quality.
- Don't include LinkedIn EasyApply results in the output. Find the direct ATS version or skip.
- One screen. Same compression discipline as `/job-radar`.

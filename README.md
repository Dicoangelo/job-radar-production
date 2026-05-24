# job-radar

> Self-hosted job search intelligence for Claude Code. Daily ATS scan, LinkedIn alert ingest, warm-line orchestration, and end-to-end apply pipeline — packed into a single top pick.

Cold job applications convert at ~3-5% in most lanes. Most listings on LinkedIn that look "Easy" are dead channels. The right offer lives behind a warm-line, on a direct ATS, scored against keywords you've already tuned. **job-radar** is the toolchain that runs that loop for you, daily, in your terminal — using your data, your scoring rules, your warm-line graph.

This is the productized version of a system that's processed thousands of applications and shipped dozens. It's been generalized into a portable Claude Code package with a single `profile.yml` you tune to your lane.

## What you get

Five Claude Code skills:

| Skill | What it does |
|---|---|
| `/job-radar` | Daily ATS scan across your target companies (Greenhouse, Lever, Ashby). Outputs one top pick + 3 backups. |
| `/job-radar-linkedin` | Ingests LinkedIn job-alert emails from Gmail, parses subject-line cards into your DB, captures warm-line connections automatically. |
| `/job-radar-firecrawl` | Optional paid variant. Broader live-web discovery via Firecrawl search. ~10-15 credits/run. |
| `/warm-line <company>` | Before any cold apply: surfaces Tier 1-4 connections, drafts ready-to-paste outreach. |
| `/apply <jd-url>` | End-to-end: WebFetch the JD, tailor resume + cover letter, render to PDF, submit via browser MCP. |

Plus a Python engine running locally:
- SQLite at `~/.job-radar/radar.db` — your data, your machine.
- ATS scrapers for Greenhouse, Lever, Ashby (no auth required, just public endpoints).
- A config-driven scorer that classifies postings by **your** lane regex and blocklist.
- Optional H-1B visa annotation module (LCA filings lookup), off by default.

## Quickstart

```bash
# 1. Clone
git clone https://github.com/Dicoangelo/job-radar-production.git
cd job-radar-production

# 2. Install (sets up ~/.job-radar/, copies skills to ~/.claude/commands/)
bash install.sh

# 3. Pick a starter profile and edit it
cp examples/profile.revops.yml ~/.job-radar/profile.yml
$EDITOR ~/.job-radar/profile.yml

# 4. Restart Claude Code, then in any project:
/job-radar
```

That's the whole loop. The skills auto-discover the profile at `~/.job-radar/profile.yml`. The DB initializes on first run.

## Configuration: profile.yml

Everything is driven by one YAML file. The starter profiles in `examples/` cover the common lanes:

- `profile.revops.yml` — Revenue Operations IC / Manager
- `profile.partner-ops.yml` — Partner Operations / Cloud Alliances
- `profile.generic.yml` — Scaffolding for any role family

Inside, you tune:

```yaml
lanes:                    # role families you'd take
  revops:
    title_signals:        # regex patterns matching role titles
    desc_boosts:          # phrases that reinforce a match

title_blocklist: [...]    # roles you'd never take (regex)

description_red_flags: [...]   # JD signals that penalize (10+ yrs, clearance)
description_green_flags: [...] # JD signals that boost (remote, 3-5 yrs)

location_whitelist: [...]      # what counts as a fit
location_blacklist: [...]      # drop entirely

comp_floor: { amount: 110000, currency: USD }

visa:
  enabled: false                # most users: leave off
  status: citizen               # citizen | tn | h1b | o1

targets:                        # companies whose ATS to scrape
  - { name: Stripe, ats_type: greenhouse, ats_slug: stripe, ... }
```

See `profile.example.yml` for the full annotated schema.

## How the scorer works

1. **Title-first classification.** A posting's title must match a lane's `title_signals` regex to get scored. No match = `unfit`.
2. **Blocklist check.** Any posting matching `title_blocklist` is dropped to `unfit` regardless of other signals.
3. **Baseline of 45** for a lane match.
4. **Description scan** applies green/red flag deltas from your profile.
5. **Location scan** boosts (+10) for whitelist, penalizes (-8) for off-whitelist, drops (-100) for blacklist.
6. **Comp floor scan** penalizes if posted comp is below your floor.
7. Final score clamped to 0-100. Shortlist threshold (default 60) gates the briefing output.

This logic lives in `engine/scorer.py`. You can read all 150 lines and verify what's happening.

## Database schema

One SQLite file at `~/.job-radar/radar.db`. Six tables:

- `target_companies` — seeded from `profile.targets` on first run
- `job_postings` — all discovered postings, deduped by `(company, external_id, source)`
- `applications` — your submitted apps (logged manually or via `/apply`)
- `contacts` — warm-line graph
- `outreach` — every drafted/sent DM, recruiter email, referral
- `radar_runs` — run history

The schema is plain SQL in `engine/schema.sql`. Backup is `cp ~/.job-radar/radar.db ~/Desktop/radar-backup.db`.

## The visa module (optional)

Most users are citizens or permanent residents and can ignore this. If you need work authorization in a country where you're not a citizen (TN, H-1B, O-1, etc.), set `profile.visa.enabled: true` and the scorer will annotate companies with LCA filing counts.

You build the LCA database once from DOL's public H-1B disclosure data:

```bash
# DOL publishes quarterly; download the CSV
# https://www.dol.gov/agencies/eta/foreign-labor/performance
python3 visa/build_lca_db.py H-1B_Disclosure_Data_FYxxxx.csv
```

The visa module never runs for citizens/PRs. It's a clean opt-in.

## Tuning your scoring (the actual moat)

The skeleton is generic. The **value** is in the lane regex you write and the green/red flags you add. Start with the closest example profile, run it for a week, then:

- Roles you'd actually take that surfaced as `unfit`? Your lane regex is too narrow. Add a pattern.
- Roles that scored high but you'd skip? Add to `title_blocklist` or `description_red_flags`.
- Companies that keep showing in shortlist but you've applied to with no response? Bump their `applications` row to `ghosted` — the briefing's history-aware shortlist will deprioritize them.

This is the same loop the original author ran for 18 months. The starter profiles encode learnings; the live profile is where YOUR learnings accumulate.

## Daily loop

```
/loop 24h /job-radar           # daily ATS scan + one pick
/loop 24h /job-radar-linkedin  # ingest LinkedIn alerts (free, no Premium needed)
```

Output is one screen per run. Briefings persist at `~/.job-radar/briefings/YYYY-MM-DD.md` for audit.

## Claude.ai (web/desktop) fallback

This package is built for Claude Code (the CLI). If you only have Claude.ai web/desktop:

1. The Python engine still runs locally — no Claude required:
   ```bash
   python3 ~/.job-radar/engine/discover.py        # scan ATS
   python3 ~/.job-radar/engine/briefing.py        # generate briefing
   ```
2. Paste the briefing into a Claude.ai project as knowledge.
3. Use the contents of any skill file (`skills/job-radar.md`, etc.) as the system prompt for that project.

The browser-automation parts of `/apply` won't work in Claude.ai web — they need MCP tools that only Claude Code has. The rest works fine as paste-the-briefing-and-discuss.

## What this doesn't do (yet)

- **DOCX render** — `/apply` ships PDF only. Most modern ATS accept PDF; if you need DOCX, pandoc handles it (`pandoc resume.md -o resume.docx`).
- **Workday adapter** — Workday is opaque and varies wildly per tenant. Use `/job-radar-firecrawl` for those.
- **Mobile** — Claude Code is desktop-first; mobile not supported.
- **Multi-user / hosted** — single-user, self-hosted by design. Your data stays local.

## Roadmap

- [ ] More ATS adapters (Workable, SmartRecruiters, Rippling)
- [ ] JD-keyword extractor v2 (Claude-driven, not regex)
- [ ] Optional Supabase sync for cross-device access
- [ ] Dashboard view (HTML, served from `~/.job-radar/`)
- [ ] More starter profiles (PM, Marketing, Eng, Customer Success)

PRs welcome. The codebase is small (< 1500 lines of Python + 5 markdown skills) and intentionally readable.

## Uninstall

```bash
bash install.sh --uninstall
```

This removes `~/.job-radar/` and the five skills from `~/.claude/commands/`. Your profile is backed up to `~/job-radar-profile.backup.yml` so you can re-install later without losing config.

## License

MIT. See LICENSE.

## Credits

Built and battle-tested by Dico Angelo (https://dicoangelo.metaventionsai.com) over 18 months of active job search. Productized so anyone can run the same loop without rebuilding the toolchain from scratch.

If this saves you a week of search-toolchain plumbing, send a note. If it lands you an offer, send two.

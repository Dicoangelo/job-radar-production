<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:a855f7,50:6366f1,100:06b6d4&height=220&section=header&text=Job%20Radar&fontSize=64&fontColor=ffffff&animation=fadeIn&fontAlignY=36&desc=Self-hosted%20Job%20Search%20Intelligence%20for%20Claude%20Code&descAlignY=58&descSize=18" width="100%" alt="Job Radar"/>
</p>

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=600&size=22&duration=3000&pause=1000&color=06B6D4&center=true&vCenter=true&multiline=false&repeat=true&width=820&height=40&lines=5+Claude+skills+%E2%80%A2+ATS+%2B+LinkedIn+%2B+Firecrawl+%E2%80%A2+Warm-line+%E2%80%A2+Apply+pipeline" alt="Typing SVG" />

<br/>

[![Metaventions AI](https://img.shields.io/badge/METAVENTIONS_AI-Architected_Intelligence-06b6d4?style=for-the-badge&labelColor=0d1117)](https://metaventionsai.com)
[![Author](https://img.shields.io/badge/Dicoangelo-Ecosystem-a855f7?style=for-the-badge&logo=github&labelColor=0d1117)](https://github.com/Dicoangelo)
[![License](https://img.shields.io/badge/License-MIT-6366f1?style=for-the-badge&labelColor=0d1117)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Built_for-Claude_Code-06b6d4?style=for-the-badge&labelColor=0d1117)](https://docs.claude.com/en/docs/claude-code)

<br/>

<img src="https://img.shields.io/badge/Skills-5-a855f7?style=for-the-badge&labelColor=0d1117" alt="Skills" />
<img src="https://img.shields.io/badge/ATS_Adapters-3-8b5cf6?style=for-the-badge&labelColor=0d1117" alt="ATS Adapters" />
<img src="https://img.shields.io/badge/Engine_LOC-~1500-6366f1?style=for-the-badge&labelColor=0d1117" alt="Engine LOC" />
<img src="https://img.shields.io/badge/Storage-SQLite_(local)-06b6d4?style=for-the-badge&labelColor=0d1117" alt="Storage" />
<img src="https://img.shields.io/badge/Version-0.1.0-a855f7?style=for-the-badge&labelColor=0d1117" alt="Version" />

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=0d1117" alt="Python" />
<img src="https://img.shields.io/badge/SQLite-WAL-003B57?style=for-the-badge&logo=sqlite&logoColor=white&labelColor=0d1117" alt="SQLite" />
<img src="https://img.shields.io/badge/Greenhouse-Adapter-25A954?style=for-the-badge&labelColor=0d1117" alt="Greenhouse" />
<img src="https://img.shields.io/badge/Lever-Adapter-5843E5?style=for-the-badge&labelColor=0d1117" alt="Lever" />
<img src="https://img.shields.io/badge/Ashby-Adapter-1F2937?style=for-the-badge&labelColor=0d1117" alt="Ashby" />
<img src="https://img.shields.io/badge/Firecrawl-Optional-FF6B35?style=for-the-badge&labelColor=0d1117" alt="Firecrawl" />

<br/>

*One concrete top pick a day. Not a wall of options.*

</div>

<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553ee.gif" width="100%"/>

<br/>

## The Loop

<div align="center">

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              JOB-RADAR DAILY LOOP                              │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   DISCOVER          →          SCORE             →         RANK               │
│   ATS scrapers                  lane regex                  warm-line          │
│   LinkedIn alerts               blocklist                   visa (opt)         │
│   Firecrawl search              comp floor                  history-aware      │
│                                                                                │
│   ════════════════════════════════════════════════════════════════════════════ │
│                                                                                │
│   • Free Premium replacement          • Same scoring brain across sources     │
│   • Direct ATS routing                • SQLite local, your data               │
│   • Warm-line graph capture           • Idempotent re-runs                    │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

</div>

<br/>

<img src="https://user-images.githubusercontent.com/74038190/212284115-f47cd8ff-2ffb-4b04-b5bf-4d1c14c0247f.gif" width="100%"/>

<br/>

## System Architecture

<div align="center">

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#06b6d4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#06b6d4', 'lineColor': '#a855f7', 'secondaryColor': '#1a1a2e', 'tertiaryColor': '#0d1117', 'clusterBkg': '#0d1117', 'clusterBorder': '#06b6d4'}}}%%
flowchart TB
    subgraph PLATFORM["JOB-RADAR PLATFORM"]
        direction TB

        subgraph SKILLS["CLAUDE CODE SKILLS — ~/.claude/commands/"]
            direction LR
            RADAR["/job-radar<br/>━━━━━━━━━━<br/>Daily ATS scan<br/>Top pick + 3 backups"]
            LINKEDIN["/job-radar-linkedin<br/>━━━━━━━━━━<br/>Gmail alert ingest<br/>Warm-line capture"]
            FIRECRAWL["/job-radar-firecrawl<br/>━━━━━━━━━━<br/>Paid broad-web<br/>10-15 credits/run"]
            WARMLINE["/warm-line<br/>━━━━━━━━━━<br/>Tier 1-4 outreach<br/>Pre-apply leverage"]
            APPLY["/apply<br/>━━━━━━━━━━<br/>JD → render → submit<br/>Browser MCP"]
        end

        subgraph ENGINE["PYTHON ENGINE — ~/.job-radar/engine/"]
            direction LR
            CONFIG["profile.yml<br/>━━━━━━━━━━<br/>lanes, blocklist<br/>comp floor, targets"]
            SCORER["scorer.py<br/>━━━━━━━━━━<br/>Title-first classify<br/>0-100 score"]
            DISCOVER["discover.py<br/>━━━━━━━━━━<br/>ATS scrapers<br/>3 adapters"]
            BRIEFING["briefing.py<br/>━━━━━━━━━━<br/>One-screen report<br/>History-aware"]
            INGEST["linkedin_ingest.py<br/>━━━━━━━━━━<br/>Subject parser<br/>Idempotent dedup"]
        end

        subgraph ATS["ATS ADAPTERS"]
            direction LR
            GH["Greenhouse<br/>━━━━━━━━━━<br/>boards-api.greenhouse.io<br/>No auth"]
            LV["Lever<br/>━━━━━━━━━━<br/>api.lever.co<br/>No auth"]
            AS["Ashby<br/>━━━━━━━━━━<br/>api.ashbyhq.com<br/>No auth"]
        end

        subgraph DATA["DATA LAYER — ~/.job-radar/"]
            DB[("radar.db<br/>━━━━━━━━━━<br/>SQLite + WAL<br/>6 tables, local")]
            BRIEFINGS["briefings/<br/>━━━━━━━━━━<br/>YYYY-MM-DD.md<br/>audit trail"]
            VISA["visa/lca.db<br/>━━━━━━━━━━<br/>OPTIONAL<br/>H-1B annotation"]
        end
    end

    OPERATOR(("OPERATOR"))
    GMAIL["Gmail MCP<br/>(LinkedIn alerts)"]

    OPERATOR <==>|"Claude Code CLI"| RADAR
    OPERATOR <==>|"Claude Code CLI"| LINKEDIN
    OPERATOR <==>|"Claude Code CLI"| WARMLINE
    OPERATOR <==>|"Claude Code CLI"| APPLY
    LINKEDIN -.->|"subject parse"| GMAIL
    RADAR --> DISCOVER
    RADAR --> BRIEFING
    LINKEDIN --> INGEST
    DISCOVER --> ATS
    DISCOVER --> SCORER
    INGEST --> SCORER
    SCORER --> CONFIG
    DISCOVER -.->|"writes"| DB
    INGEST -.->|"writes"| DB
    BRIEFING -.->|"reads"| DB
    BRIEFING -.->|"writes"| BRIEFINGS
    WARMLINE -.->|"reads/writes"| DB
    APPLY -.->|"reads/writes"| DB
    APPLY -.->|"opt"| VISA

    style PLATFORM fill:#0d1117,stroke:#06b6d4,stroke-width:3px
    style SKILLS fill:#1a1a2e,stroke:#06b6d4,stroke-width:2px
    style ENGINE fill:#1a1a2e,stroke:#a855f7,stroke-width:2px
    style ATS fill:#1a1a2e,stroke:#8b5cf6,stroke-width:2px
    style DATA fill:#16213e,stroke:#06b6d4,stroke-width:2px
    style OPERATOR fill:#06b6d4,stroke:#fff,stroke-width:2px,color:#0d1117
    style GMAIL fill:#a855f7,stroke:#fff,stroke-width:2px,color:#fff
```

<sub>Five skills, one engine, one SQLite file. Your data stays local.</sub>

</div>

<br/>

<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553ee.gif" width="100%"/>

<br/>

## The Five Skills

<table>
<tr>
<td width="20%" align="center" valign="top">
<h3>/job-radar</h3>
<b>Daily ATS scan</b>
<p>Scrapes target companies, scores against your lane regex, outputs one top pick + 3 backups. No wall of options.</p>
</td>
<td width="20%" align="center" valign="top">
<h3>/job-radar-linkedin</h3>
<b>Free Premium replacement</b>
<p>Ingests LinkedIn job-alert emails from Gmail, parses subject-line cards, auto-captures warm-line connections.</p>
</td>
<td width="20%" align="center" valign="top">
<h3>/job-radar-firecrawl</h3>
<b>Broad-web discovery</b>
<p>Paid variant using Firecrawl search across the live web. Same scoring brain. 10-15 credits per run.</p>
</td>
<td width="20%" align="center" valign="top">
<h3>/warm-line</h3>
<b>Pre-apply leverage</b>
<p>Surfaces Tier 1-4 connections, drafts ready-to-paste outreach, halts cold-applies when ATS dedup risk exists.</p>
</td>
<td width="20%" align="center" valign="top">
<h3>/apply</h3>
<b>End-to-end submit</b>
<p>JD URL to confirmation. WebFetch the JD, tailor resume + cover, render to PDF, browser-MCP submit through Greenhouse / Lever / Ashby.</p>
</td>
</tr>
</table>

<br/>

## Why this exists

<div align="center">

| | Default flow | Job-radar flow |
|---|---|---|
| **Discovery** | Open LinkedIn, scroll, refresh | Five sources auto-scanned daily |
| **Filtering** | Eye-balling titles | Title regex + blocklist + comp floor |
| **Ranking** | Most recent first | Lane fit + warm-line + history-aware |
| **Warm-line** | Forgotten until after applying | Mandatory pre-apply check, drafts ready |
| **Submission** | Manual paste, ~80 tool calls | ~35 tool calls, browser-automated |
| **Persistence** | Tabs and screenshots | SQLite, your data, your machine |

</div>

<br/>

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

That's the whole loop. Skills auto-discover the profile at `~/.job-radar/profile.yml`. The DB initializes on first run.

<br/>

## Project Structure

```
job-radar-production/
├── README.md                       ← this file
├── LICENSE                         ← MIT
├── install.sh                      ← idempotent installer
├── profile.example.yml             ← annotated full schema reference
├── skills/                         ← the 5 Claude Code skills
│   ├── job-radar.md
│   ├── job-radar-linkedin.md
│   ├── job-radar-firecrawl.md
│   ├── warm-line.md
│   └── apply.md
├── engine/                         ← Python engine, ~1500 LOC
│   ├── config.py                   ← profile.yml loader
│   ├── scorer.py                   ← config-driven lane scorer
│   ├── discover.py                 ← ATS pipeline orchestrator
│   ├── briefing.py                 ← daily one-screen report
│   ├── linkedin_ingest.py          ← Gmail alert → DB
│   ├── db.py                       ← SQLite connection helper
│   ├── schema.sql                  ← 6-table schema
│   └── adapters/
│       ├── greenhouse.py           ← boards-api.greenhouse.io
│       ├── lever.py                ← api.lever.co
│       └── ashby.py                ← api.ashbyhq.com
├── visa/                           ← OPTIONAL H-1B LCA annotation
│   └── lca_lookup.py
├── examples/                       ← starter profiles
│   ├── profile.revops.yml
│   ├── profile.partner-ops.yml
│   └── profile.generic.yml
└── demo/                           ← static showcase page
    └── index.html
```

<br/>

## Configuration: profile.yml

Everything is driven by one YAML file. Starter profiles cover common lanes:

<table>
<tr>
<td width="33%" align="center" valign="top">
<h3>profile.revops.yml</h3>
<b>Revenue Operations</b>
<p>IC / Manager track. SFDC, deal desk, GTM systems, pipeline hygiene. Comp floor $110K.</p>
</td>
<td width="33%" align="center" valign="top">
<h3>profile.partner-ops.yml</h3>
<b>Partner / Alliances</b>
<p>Cloud alliances, co-sell motion, deal registration, hyperscaler ecosystems. Comp floor $130K.</p>
</td>
<td width="33%" align="center" valign="top">
<h3>profile.generic.yml</h3>
<b>Scaffolding</b>
<p>Empty template with placeholder regex. Fill in your lane signals and target companies.</p>
</td>
</tr>
</table>

Inside any profile:

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

See [`profile.example.yml`](profile.example.yml) for the full annotated schema.

<br/>

## How the Scorer Works

<div align="center">

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#06b6d4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#06b6d4', 'lineColor': '#a855f7', 'secondaryColor': '#1a1a2e', 'tertiaryColor': '#0d1117'}}}%%
flowchart LR
    POSTING([Job Posting])
    BLOCK{Title<br/>blocklisted?}
    LANE{Title matches<br/>a lane regex?}
    SCORE[Baseline 45<br/>+ desc green flags<br/>− desc red flags<br/>+ location +10<br/>− comp floor]
    CLAMP[Clamp 0-100]
    OUT([lane, score, reasons])

    POSTING --> BLOCK
    BLOCK -->|yes| UNFIT[lane=unfit, score=0]
    BLOCK -->|no| LANE
    LANE -->|no match| NOLANE[lane=unfit, score=10]
    LANE -->|match| SCORE
    SCORE --> CLAMP
    CLAMP --> OUT

    style POSTING fill:#06b6d4,color:#0d1117,stroke:#fff,stroke-width:2px
    style BLOCK fill:#1a1a2e,stroke:#a855f7,stroke-width:2px,color:#fff
    style LANE fill:#1a1a2e,stroke:#a855f7,stroke-width:2px,color:#fff
    style SCORE fill:#1a1a2e,stroke:#06b6d4,stroke-width:2px,color:#fff
    style CLAMP fill:#1a1a2e,stroke:#6366f1,stroke-width:2px,color:#fff
    style OUT fill:#06b6d4,color:#0d1117,stroke:#fff,stroke-width:2px
    style UNFIT fill:#7c3aed,color:#fff,stroke:#fff
    style NOLANE fill:#7c3aed,color:#fff,stroke:#fff
```

</div>

1. **Title-first classification.** A posting's title must match a lane's `title_signals` regex. No match = `unfit`.
2. **Blocklist check.** Any posting matching `title_blocklist` is dropped to `unfit` regardless of other signals.
3. **Baseline of 45** for a lane match.
4. **Description scan** applies green/red flag deltas from your profile.
5. **Location scan** boosts (+10) for whitelist, penalizes (-8) for off-whitelist, drops (-100) for blacklist.
6. **Comp floor scan** penalizes if posted comp is below your floor.
7. Final score clamped to 0-100. Shortlist threshold (default 60) gates the briefing output.

All 150 lines of this logic live in [`engine/scorer.py`](engine/scorer.py).

<br/>

## Database

One SQLite file at `~/.job-radar/radar.db`. Six tables:

<div align="center">

| Table | What it holds |
|---|---|
| `target_companies` | Seeded from `profile.targets` on first run |
| `job_postings` | All discovered postings, deduped by `(company, external_id, source)` |
| `applications` | Your submitted apps (logged manually or via `/apply`) |
| `contacts` | Warm-line graph |
| `outreach` | Every drafted/sent DM, recruiter email, referral |
| `radar_runs` | Run history |

</div>

Schema is plain SQL in [`engine/schema.sql`](engine/schema.sql). Backup is `cp ~/.job-radar/radar.db ~/Desktop/radar-backup.db`.

<br/>

## Daily Loop

```bash
/loop 24h /job-radar           # daily ATS scan + one pick
/loop 24h /job-radar-linkedin  # ingest LinkedIn alerts (free, no Premium needed)
```

Output is one screen per run. Briefings persist at `~/.job-radar/briefings/YYYY-MM-DD.md` for audit.

<br/>

## The Visa Module (optional)

Most users are citizens or permanent residents and ignore this. If you need work auth in a country where you aren't a citizen (TN, H-1B, O-1), set `profile.visa.enabled: true` and the scorer annotates companies with LCA filing counts.

Build the LCA database once from DOL's public H-1B disclosure data:

```bash
# https://www.dol.gov/agencies/eta/foreign-labor/performance
python3 visa/build_lca_db.py H-1B_Disclosure_Data_FYxxxx.csv
```

The visa module never runs for citizens / PRs. Clean opt-in.

<br/>

## Tuning Your Scoring (the actual moat)

The skeleton is generic. The **value** is in the lane regex you write and the green/red flags you add. Start with the closest example profile, run it for a week, then:

- Roles you'd take that surfaced as `unfit`? Lane regex too narrow. Add a pattern.
- Roles that scored high but you'd skip? Add to `title_blocklist` or `description_red_flags`.
- Companies that keep showing in shortlist but ghost you? Bump their `applications` row to `ghosted` — the briefing's history-aware shortlist deprioritizes them.

The starter profiles ship with sane defaults. Your live profile is where YOUR learnings accumulate.

<br/>

## Claude.ai (web/desktop) fallback

Built for Claude Code (CLI). On Claude.ai web/desktop:

1. The Python engine runs locally regardless:
   ```bash
   python3 ~/.job-radar/engine/discover.py        # scan ATS
   python3 ~/.job-radar/engine/briefing.py        # generate briefing
   ```
2. Paste the briefing into a Claude.ai project as knowledge.
3. Use any skill file's body as the system prompt.

Browser-automation parts of `/apply` need MCP tools that only Claude Code has — the rest works as paste-the-briefing-and-discuss.

<br/>

<details>
<summary><b>Roadmap</b></summary>

- [ ] More ATS adapters (Workable, SmartRecruiters, Rippling)
- [ ] JD-keyword extractor v2 (Claude-driven, not regex)
- [ ] Optional Supabase sync for cross-device access
- [ ] Dashboard view (HTML, served from `~/.job-radar/`)
- [ ] More starter profiles (PM, Marketing, Eng, Customer Success)
- [ ] Auto-tune lane regex from `applications` outcomes (rejected vs offered)

PRs welcome. Codebase is intentionally readable: < 1500 lines Python + 5 markdown skills.

</details>

<details>
<summary><b>Uninstall</b></summary>

```bash
bash install.sh --uninstall
```

Removes `~/.job-radar/` and the five skills from `~/.claude/commands/`. Your profile is backed up to `~/job-radar-profile.backup.yml`.

</details>

<details>
<summary><b>What this doesn't do</b></summary>

- **DOCX render** — `/apply` ships PDF only. Most modern ATS accept PDF.
- **Workday adapter** — Workday is opaque per-tenant. Use `/job-radar-firecrawl` for those.
- **Mobile** — Claude Code is desktop-first.
- **Multi-user / hosted** — single-user, self-hosted by design. Your data stays local.

</details>

<br/>

<img src="https://user-images.githubusercontent.com/74038190/212284115-f47cd8ff-2ffb-4b04-b5bf-4d1c14c0247f.gif" width="100%"/>

<br/>

## Credits

<div align="center">

Built and battle-tested by [**Dico Angelo**](https://dicoangelo.metaventionsai.com).<br/>
Productized so anyone can run the loop without rebuilding the toolchain.

Part of the [**Metaventions AI**](https://metaventionsai.com) ecosystem.<br/>
Sovereign agent infrastructure for individuals.

<br/>

[![Star this repo](https://img.shields.io/github/stars/Dicoangelo/job-radar-production?style=for-the-badge&logo=github&logoColor=white&labelColor=0d1117&color=06b6d4)](https://github.com/Dicoangelo/job-radar-production)
[![Follow author](https://img.shields.io/github/followers/Dicoangelo?style=for-the-badge&logo=github&logoColor=white&labelColor=0d1117&color=a855f7&label=Follow)](https://github.com/Dicoangelo)

</div>

<br/>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:06b6d4,50:6366f1,100:a855f7&height=120&section=footer" width="100%" alt="Footer"/>
</p>

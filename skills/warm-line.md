---
name: warm-line
description: Route every job application through a warm-line check before cold-applying. Pulls Gmail recruiter history, radar.db contacts, and LinkedIn connection signal, ranks by leverage tier, and drafts ready-to-send outreach.
---

# Warm-line First

Cold applications have low response rates in most lanes (track your own — `profile.warm_line.cold_conversion_rate` records yours). Warm-line conversions are dramatically higher. This skill produces a one-screen warm-line check before any cold submission.

## Input

`/warm-line <job-url-or-company>` accepts:
- LinkedIn job URL (`https://www.linkedin.com/jobs/view/...`)
- Direct ATS URL (Greenhouse / Lever / Ashby)
- Company name with role (`Anthropic / Partner Operations Manager`)
- Bare company name (will prompt for role if needed)

## Pre-flight

Reads `profile.yml` for:
- `identity` — your name, current title, links (used in drafts)
- `warm_line.cold_conversion_rate` — your tracked baseline
- `warm_line.ats_block_threshold` — when to halt cold-applies
- `warm_line.poisoned_contacts` — names to exclude from outreach

## What to do

### 1. Parse input

Extract `{company}`, `{role}`, `{url}` from the input. If only a company name is given and the role is missing, ask once before continuing.

### 2. Run 3 parallel intel pulls

Fire these in a single tool batch — they're independent.

**Pull A — Gmail recruiter history** via `mcp__claude_ai_Gmail__search_threads`:
```
from:{company-domain} OR (subject:"connections work here" subject:{company}) newer_than:1y
```
If results return, follow up with `get_thread` on the top 3 to extract sender, title, and ask. Note any thread where the user already replied — that's a live recruiter line, not a fresh one.

**Pull B — radar.db lookup** via `sqlite3`:
```bash
DB=~/.job-radar/radar.db

# Existing contacts at the company
sqlite3 "$DB" "SELECT name, role, relationship, email, linkedin, last_contact, notes
  FROM contacts
  WHERE company LIKE '%{company}%'
  ORDER BY last_contact DESC;"

# Prior applications at the company (ATS dedup check)
sqlite3 "$DB" "SELECT role, status, date_applied, source, referral_contact, job_url
  FROM applications
  WHERE company LIKE '%{company}%'
  ORDER BY date_applied DESC;"

# Prior outreach (warm-line history)
sqlite3 "$DB" "SELECT o.channel, o.direction, o.subject, o.status, o.sent_at, c.name
  FROM outreach o LEFT JOIN contacts c ON o.contact_id = c.id
  WHERE c.company LIKE '%{company}%'
  ORDER BY o.sent_at DESC LIMIT 10;"
```

**Pull C — LinkedIn connection signal** (only if Claude Code has chrome-devtools MCP):
- `mcp__chrome-devtools__new_page` (background: true) to the LinkedIn job URL or `linkedin.com/company/{company}/people/`.
- `mcp__chrome-devtools__take_snapshot` and read for:
  - Connection count badge ("X connections work here")
  - First-degree connection names (usually 3 surfaced in "Your network at {company}")
  - Hiring manager / recruiter name if posted on the JD
- If not logged in, tell the user to log in once and retry. Do NOT navigate to login automatically.

### 3. Rank potential warm-lines by leverage

| Tier | Definition | Why |
|---|---|---|
| **T1** | Hiring manager or recruiter for the specific req | Decision power |
| **T2** | 1st-degree connection at target company in same function | Scope match, credibility |
| **T3** | 1st-degree connection at target company, any function | Internal referral path |
| **T4** | 2nd-degree connection via a strong mutual | Needs intro request first |

If a contact appears in radar.db **and** as a 1st-degree LinkedIn connection, prefer the radar.db relationship label — it's higher signal than raw 1st-degree.

Cap output at top 3 per tier. Exclude any name listed in `profile.warm_line.poisoned_contacts`.

### 4. Draft outreach for each tier

Drafts must be ready-to-paste. Apply these constraints to every draft:

- **No filler language.** No "passionate," "synergy," "10x," "rockstar." Alignment, clarity, execution — gap-first framing.
- **Anchor on the user's actual current role.** Pull `profile.identity.current_title` and `profile.identity.current_company` for the proof point.
- **Mirror the JD's vocabulary.** If the JD says "deal registration," use "deal registration." If it says "co-sell motion," use that.

**Tier 1 template — direct DM to hiring manager / recruiter:**
```
Hi {name}, saw the {role} req at {company}. Quick fit check:
at {current_company} I work in {current_function} ({1-2 concrete scope
points lifted from the user's resume or experience ledger}).

Open to a 15-minute chat this week or next? Happy to send context first.
```

**Tier 2 template — peer note to same-function 1st-degree:**
```
Hey {name}, hope you're well. Saw {company} is hiring {role}, looks
aligned with what I do at {current_company}. Would you be willing to
refer me, or point me to the right person on the {function} side?
Happy to send a 1-pager.
```

**Tier 3 template — soft ask to any-function 1st-degree:**
```
Hey {name}, quick one: do you know who runs {function} at {company}?
Looking at the {role} req and trying to find the right internal contact
before I apply through the portal. Any pointer appreciated.
```

**Tier 4 template — connection request via mutual:**
```
Hi {name}, we're both connected to {mutual}. I'm looking at a {role}
opening at {company} and would value 10 minutes to understand how the
{function} org is structured. Open to connecting?
```

### 5. ATS-block detection

If radar.db `applications` shows >= `profile.warm_line.ats_block_threshold` prior applications at the same company, ATS dedupe is almost certainly active. Surface as a hard block:

> ATS dedup risk: {N} prior applications at {company}. Cold path through the portal will likely auto-reject. **Force warm-line path** — do not apply through the JD until a Tier 1 or Tier 2 contact replies.

### 6. Output structure (markdown, single screen)

```
### {company} / {role}
{job-url}

**Scope-fit verdict:** {PASS / SKIP / VERIFY} — {one-line reason}

### Connection signal
- LinkedIn: {N} connections work here
- Top names: {name} ({tier}), {name} ({tier}), {name} ({tier})
- radar.db contacts: {N} ({list with relationship label})
- Prior recruiter email: {sender, last contact date} or "none"

### Drafted outreach
**Tier 1 — {name}, {title}**
{draft}

**Tier 2 — {name}, {title}**
{draft}

(omit empty tiers)

### Direct apply path
{Either:}
- WARM-LINE FIRST: send Tier {N} draft, wait 3 business days, then cold-apply if no reply.
- ATS BLOCK: {N} prior apps. Do NOT cold-apply. Wait for warm-line reply.
- COLD OK: no warm line surfaced. Apply through {portal} but log it as low-conviction.
```

## DB writes

Default: **draft only, do not commit**. Show the SQL the skill would run, ask for confirmation before executing.

When approved, run:
```bash
sqlite3 ~/.job-radar/radar.db <<SQL
INSERT INTO contacts (name, company, role, relationship, linkedin, context, last_contact, notes)
VALUES ('{name}', '{company}', '{title}', '{tier}', '{linkedin-url}',
        'Surfaced via /warm-line on {date}', '{date}', '{1-line context}');

INSERT INTO outreach (contact_id, channel, direction, subject, message_text, status, sent_at)
VALUES (last_insert_rowid(), 'linkedin_message', 'outbound',
        'Re: {role} at {company}', '{draft text}', 'draft', datetime('now'));
SQL
```

Never insert a row marked `sent` until the user confirms they actually sent it. Use status `draft` until told otherwise.

## Notes for Claude

- **Never send DMs autonomously.** This skill drafts. The user sends.
- **Cap names at 3 per tier.** A 20-name dump is not actionable.
- **Lead with the net action.** Every output ends with one sentence: "Send Tier 1 draft to {name} now," or "Wait, ATS-blocked," or "Cold OK but low-conviction."
- **Don't surface poisoned contacts.** Filter `profile.warm_line.poisoned_contacts` before ranking.
- This skill is per-job, not recurring. Do not loop or schedule.

## Common questions

- **"Who do I know at {company}?"** — Run pull B + pull C, output the Connection signal block only.
- **"Should I apply cold or wait?"** — Output the Direct apply path block.
- **"Draft me a note to {name}"** — Pick tier from radar.db relationship label, generate matching template.
- **"How many times have I applied to {company}?"** — Run the applications query, surface ATS-block status.

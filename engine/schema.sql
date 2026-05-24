-- job-radar-production schema
-- One SQLite file per user, lives at ~/.job-radar/radar.db
--
-- Tables:
--   target_companies  — seeded from profile.yml on first run
--   job_postings      — all discovered postings, deduped via UNIQUE(company, external_id, source)
--   applications      — submitted applications (manually logged or via /apply)
--   contacts          — warm-line graph
--   outreach          — every touchpoint (warm-line drafts, sends, responses)
--   radar_runs        — run history for the dashboard

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS target_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    ats_type TEXT CHECK(ats_type IN ('greenhouse','lever','ashby','workday','custom','manual')),
    ats_slug TEXT,
    priority INTEGER DEFAULT 3,
    lane TEXT,
    notes TEXT,
    active INTEGER DEFAULT 1,
    last_checked TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    url TEXT NOT NULL,
    location TEXT,
    remote_policy TEXT,
    comp_min INTEGER,
    comp_max INTEGER,
    comp_currency TEXT,
    years_min INTEGER,
    years_max INTEGER,
    -- lane is a free-text column (no CHECK constraint) because lanes are
    -- defined per-user in profile.yml. The scorer assigns whatever the user
    -- has configured, plus the reserved value 'unfit'.
    lane TEXT,
    score INTEGER,
    score_reasons TEXT,
    description_text TEXT,
    posted_at TEXT,
    discovered_at TEXT DEFAULT (datetime('now')),
    last_seen_at TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'new' CHECK(status IN ('new','reviewed','shortlist','applied','ignored','stale')),
    application_id INTEGER REFERENCES applications(id),
    source TEXT,
    raw_json TEXT,
    UNIQUE(company, external_id, source)
);

CREATE INDEX IF NOT EXISTS idx_postings_status ON job_postings(status, score DESC);
CREATE INDEX IF NOT EXISTS idx_postings_company ON job_postings(company);
CREATE INDEX IF NOT EXISTS idx_postings_discovered ON job_postings(discovered_at DESC);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'researching', 'preparing', 'applied', 'screening',
        'interviewing', 'offer', 'accepted', 'rejected', 'withdrawn', 'ghosted'
    )),
    date_applied TEXT,
    date_updated TEXT,
    source TEXT,
    referral_contact TEXT,
    job_url TEXT,
    salary_range TEXT,
    location TEXT,
    remote_policy TEXT,
    warm_line TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company TEXT,
    role TEXT,
    relationship TEXT,
    email TEXT,
    linkedin TEXT,
    phone TEXT,
    context TEXT,
    last_contact TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER REFERENCES contacts(id),
    channel TEXT NOT NULL CHECK(channel IN (
        'linkedin_connect', 'linkedin_inmail', 'linkedin_message',
        'email', 'phone', 'website_registration', 'referral',
        'meeting', 'conference', 'other'
    )),
    direction TEXT NOT NULL CHECK(direction IN ('outbound', 'inbound')),
    subject TEXT,
    message_text TEXT,
    status TEXT DEFAULT 'draft' CHECK(status IN (
        'draft', 'sent', 'delivered', 'opened', 'replied', 'no_response',
        'meeting_scheduled', 'rejected', 'follow_up_needed'
    )),
    follow_up_date TEXT,
    response_text TEXT,
    outcome TEXT,
    sent_at TEXT DEFAULT (datetime('now')),
    responded_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach(status);

CREATE TABLE IF NOT EXISTS radar_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT DEFAULT (datetime('now')),
    postings_discovered INTEGER DEFAULT 0,
    postings_new INTEGER DEFAULT 0,
    errors TEXT,
    duration_ms INTEGER
);

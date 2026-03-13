#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# migrate.sh — Kompresorinė Platform schema migration
#
# Safe, idempotent. Runs on any version of the DB and brings it up to the
# current schema. Never drops data. Run as many times as you like.
#
# Usage:
#   chmod +x migrate.sh
#   ./migrate.sh                          # uses default DB path
#   ./migrate.sh /path/to/kompresorine.db # explicit path
#
# Requirements: sqlite3 must be installed.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Locate the database ───────────────────────────────────────────────────────
if [ -n "${1:-}" ]; then
    DB="$1"
else
    # Try the standard Flask instance path
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    DB="$SCRIPT_DIR/instance/kompresorine.db"
fi

if [ ! -f "$DB" ]; then
    echo "ERROR: Database not found at: $DB"
    echo "Usage: $0 [/path/to/kompresorine.db]"
    exit 1
fi

command -v sqlite3 >/dev/null 2>&1 || { echo "ERROR: sqlite3 is not installed."; exit 1; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Kompresorinė Platform — Database Migration"
echo "  DB: $DB"
echo "  $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Backup ────────────────────────────────────────────────────────────────────
BACKUP="${DB%.db}.bak.$(date +%Y%m%d_%H%M%S).db"
cp "$DB" "$BACKUP"
echo "✓ Backup created: $BACKUP"
echo ""

# ── Helper: add a column if it doesn't exist ─────────────────────────────────
# Pass column name unquoted; it will be double-quoted in the DDL automatically.
add_column() {
    local table="$1"
    local column="$2"        # bare column name (no quotes), used for pragma check
    local definition="$3"   # e.g. "TEXT DEFAULT ''"

    # Strip any surrounding quotes from column name for the pragma lookup
    local bare_column="${column//\"/}"
    local exists
    exists=$(sqlite3 "$DB" "SELECT COUNT(*) FROM pragma_table_info('$table') WHERE name='$bare_column';")
    if [ "$exists" -eq 0 ]; then
        sqlite3 "$DB" "ALTER TABLE \"$table\" ADD COLUMN \"$bare_column\" $definition;"
        echo "  + $table.$bare_column"
    fi
}

# ── Helper: create a table if it doesn't exist ───────────────────────────────
create_table() {
    local table="$1"
    local ddl="$2"

    local exists
    exists=$(sqlite3 "$DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='$table';")
    if [ "$exists" -eq 0 ]; then
        sqlite3 "$DB" "$ddl"
        echo "  + table: $table"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# TABLE-BY-TABLE MIGRATIONS
# ─────────────────────────────────────────────────────────────────────────────

echo "── Core tables ──────────────────────────────────────────"

# user — base table, should exist. Ensure role column.
create_table "user" "
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member'
);"
add_column "user" "role" "VARCHAR(50) NOT NULL DEFAULT 'member'"

# institution
create_table "institution" "
CREATE TABLE IF NOT EXISTS institution (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(80) NOT NULL,
    contact_person VARCHAR(120) DEFAULT '',
    contact_email VARCHAR(120) DEFAULT '',
    notes TEXT DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "institution" "contact_person" "VARCHAR(120) DEFAULT ''"
add_column "institution" "contact_email"  "VARCHAR(120) DEFAULT ''"
add_column "institution" "notes"          "TEXT DEFAULT ''"
add_column "institution" "created_by_id"  "INTEGER REFERENCES user(id)"

# partnership
create_table "partnership" "
CREATE TABLE IF NOT EXISTS partnership (
    id INTEGER PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institution(id),
    status VARCHAR(50) NOT NULL DEFAULT 'prospective',
    objective TEXT NOT NULL DEFAULT '',
    requested_support TEXT DEFAULT '',
    timeline VARCHAR(120) DEFAULT '',
    intellectual_contributions TEXT DEFAULT '',
    renewal_intention VARCHAR(50) DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "partnership" "requested_support"        "TEXT DEFAULT ''"
add_column "partnership" "timeline"                 "VARCHAR(120) DEFAULT ''"
add_column "partnership" "intellectual_contributions" "TEXT DEFAULT ''"
add_column "partnership" "renewal_intention"        "VARCHAR(50) DEFAULT ''"
add_column "partnership" "created_by_id"            "INTEGER REFERENCES user(id)"

echo ""
echo "── Research tables ──────────────────────────────────────"

# research_project
create_table "research_project" "
CREATE TABLE IF NOT EXISTS research_project (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    lead VARCHAR(120) NOT NULL,
    phase VARCHAR(50) NOT NULL DEFAULT 'pilot',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    research_question TEXT NOT NULL DEFAULT '',
    methods TEXT DEFAULT '',
    outputs TEXT DEFAULT '',
    start_date DATE,
    end_date DATE,
    budget_allocation FLOAT DEFAULT 0.0,
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "research_project" "methods"          "TEXT DEFAULT ''"
add_column "research_project" "outputs"          "TEXT DEFAULT ''"
add_column "research_project" "start_date"       "DATE"
add_column "research_project" "end_date"         "DATE"
add_column "research_project" "budget_allocation" "FLOAT DEFAULT 0.0"
add_column "research_project" "created_by_id"   "INTEGER REFERENCES user(id)"

# research_session
create_table "research_session" "
CREATE TABLE IF NOT EXISTS research_session (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES research_project(id),
    session_date DATE NOT NULL,
    facilitator VARCHAR(120) NOT NULL DEFAULT '',
    participants TEXT DEFAULT '',
    methods_used TEXT DEFAULT '',
    observations TEXT DEFAULT '',
    open_questions TEXT DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "research_session" "facilitator"    "VARCHAR(120) NOT NULL DEFAULT ''"
add_column "research_session" "participants"   "TEXT DEFAULT ''"
add_column "research_session" "methods_used"   "TEXT DEFAULT ''"
add_column "research_session" "observations"   "TEXT DEFAULT ''"
add_column "research_session" "open_questions" "TEXT DEFAULT ''"
add_column "research_session" "created_by_id"  "INTEGER REFERENCES user(id)"

# project_membership
create_table "project_membership" "
CREATE TABLE IF NOT EXISTS project_membership (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES research_project(id),
    user_id INTEGER NOT NULL REFERENCES user(id),
    role VARCHAR(80) DEFAULT 'contributor'
);"
add_column "project_membership" "role" "VARCHAR(80) DEFAULT 'contributor'"

# milestone
create_table "milestone" "
CREATE TABLE IF NOT EXISTS milestone (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES research_project(id),
    title VARCHAR(200) NOT NULL,
    target_date DATE,
    status VARCHAR(30) DEFAULT 'pending',
    description TEXT DEFAULT '',
    url VARCHAR(500) DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "milestone" "target_date"    "DATE"
add_column "milestone" "status"         "VARCHAR(30) DEFAULT 'pending'"
add_column "milestone" "description"    "TEXT DEFAULT ''"
add_column "milestone" "url"            "VARCHAR(500) DEFAULT ''"
add_column "milestone" "created_by_id"  "INTEGER REFERENCES user(id)"

echo ""
echo "── Booking & Facilities ─────────────────────────────────"

# facility
create_table "facility" "
CREATE TABLE IF NOT EXISTS facility (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT DEFAULT '',
    capacity INTEGER DEFAULT 0,
    floor_area VARCHAR(30) DEFAULT '',
    location VARCHAR(200) DEFAULT '',
    modes TEXT DEFAULT '',
    characteristics TEXT DEFAULT '',
    status VARCHAR(30) DEFAULT 'active',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "facility" "description"     "TEXT DEFAULT ''"
add_column "facility" "capacity"        "INTEGER DEFAULT 0"
add_column "facility" "floor_area"      "VARCHAR(30) DEFAULT ''"
add_column "facility" "location"        "VARCHAR(200) DEFAULT ''"
add_column "facility" "modes"           "TEXT DEFAULT ''"
add_column "facility" "characteristics" "TEXT DEFAULT ''"
add_column "facility" "status"          "VARCHAR(30) DEFAULT 'active'"
add_column "facility" "created_by_id"   "INTEGER REFERENCES user(id)"

# booking
create_table "booking" "
CREATE TABLE IF NOT EXISTS booking (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES research_project(id),
    space VARCHAR(100) NOT NULL,
    booking_type VARCHAR(100) NOT NULL,
    start_dt DATETIME NOT NULL,
    end_dt DATETIME NOT NULL,
    lead_name VARCHAR(120) NOT NULL DEFAULT '',
    notes TEXT DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "booking" "lead_name"      "VARCHAR(120) NOT NULL DEFAULT ''"
add_column "booking" "notes"          "TEXT DEFAULT ''"
add_column "booking" "created_by_id"  "INTEGER REFERENCES user(id)"

# equipment
create_table "equipment" "
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    portable BOOLEAN DEFAULT 1,
    status VARCHAR(50) DEFAULT 'available',
    owner VARCHAR(120) DEFAULT 'Ideas Block / LMTA partnership',
    transfer_plan TEXT DEFAULT '',
    facility_id INTEGER REFERENCES facility(id),
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "equipment" "portable"       "BOOLEAN DEFAULT 1"
add_column "equipment" "status"         "VARCHAR(50) DEFAULT 'available'"
add_column "equipment" "owner"          "VARCHAR(120) DEFAULT 'Ideas Block / LMTA partnership'"
add_column "equipment" "transfer_plan"  "TEXT DEFAULT ''"
add_column "equipment" "facility_id"    "INTEGER REFERENCES facility(id)"
add_column "equipment" "created_by_id"  "INTEGER REFERENCES user(id)"

echo ""
echo "── Budget ───────────────────────────────────────────────"

# budget_item
create_table "budget_item" "
CREATE TABLE IF NOT EXISTS budget_item (
    id INTEGER PRIMARY KEY,
    category VARCHAR(80) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    amount FLOAT NOT NULL,
    note TEXT DEFAULT '',
    item_date DATE,
    project_id INTEGER REFERENCES research_project(id),
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "budget_item" "note"          "TEXT DEFAULT ''"
add_column "budget_item" "item_date"     "DATE"
add_column "budget_item" "project_id"    "INTEGER REFERENCES research_project(id)"
add_column "budget_item" "created_by_id" "INTEGER REFERENCES user(id)"

echo ""
echo "── Governance ───────────────────────────────────────────"

# working_group (must exist before meeting FK)
create_table "working_group" "
CREATE TABLE IF NOT EXISTS working_group (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT DEFAULT '',
    focus VARCHAR(200) DEFAULT '',
    status VARCHAR(30) DEFAULT 'active',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "working_group" "description"  "TEXT DEFAULT ''"
add_column "working_group" "focus"        "VARCHAR(200) DEFAULT ''"
add_column "working_group" "status"       "VARCHAR(30) DEFAULT 'active'"
add_column "working_group" "created_by_id" "INTEGER REFERENCES user(id)"

# working_group_membership
create_table "working_group_membership" "
CREATE TABLE IF NOT EXISTS working_group_membership (
    id INTEGER PRIMARY KEY,
    wg_id INTEGER NOT NULL REFERENCES working_group(id),
    user_id INTEGER NOT NULL REFERENCES user(id),
    role VARCHAR(80) DEFAULT 'member'
);"
add_column "working_group_membership" "role" "VARCHAR(80) DEFAULT 'member'"

# meeting
create_table "meeting" "
CREATE TABLE IF NOT EXISTS meeting (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    meeting_date DATE NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    decisions TEXT DEFAULT '',
    meeting_type VARCHAR(80) DEFAULT 'steering',
    working_group_id INTEGER REFERENCES working_group(id),
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "meeting" "decisions"        "TEXT DEFAULT ''"
add_column "meeting" "meeting_type"     "VARCHAR(80) DEFAULT 'steering'"
add_column "meeting" "working_group_id" "INTEGER REFERENCES working_group(id)"
add_column "meeting" "created_by_id"   "INTEGER REFERENCES user(id)"

# proposal_record
create_table "proposal_record" "
CREATE TABLE IF NOT EXISTS proposal_record (
    id INTEGER PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meeting(id),
    proposal_text TEXT NOT NULL DEFAULT '',
    proposer VARCHAR(120) NOT NULL DEFAULT '',
    outcome VARCHAR(30) NOT NULL DEFAULT 'pending',
    votes_for INTEGER DEFAULT 0,
    votes_against INTEGER DEFAULT 0,
    dissenting_notes TEXT DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "proposal_record" "outcome"         "VARCHAR(30) NOT NULL DEFAULT 'pending'"
add_column "proposal_record" "votes_for"       "INTEGER DEFAULT 0"
add_column "proposal_record" "votes_against"   "INTEGER DEFAULT 0"
add_column "proposal_record" "dissenting_notes" "TEXT DEFAULT ''"
add_column "proposal_record" "created_by_id"   "INTEGER REFERENCES user(id)"

echo ""
echo "── Governance documents ─────────────────────────────────"

# policy_document
create_table "policy_document" "
CREATE TABLE IF NOT EXISTS policy_document (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    version VARCHAR(20) DEFAULT '1.0',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "policy_document" "version"       "VARCHAR(20) DEFAULT '1.0'"
add_column "policy_document" "created_by_id" "INTEGER REFERENCES user(id)"

# risk_register
create_table "risk_register" "
CREATE TABLE IF NOT EXISTS risk_register (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    owner VARCHAR(120) NOT NULL DEFAULT '',
    mitigation TEXT NOT NULL DEFAULT '',
    status VARCHAR(30) DEFAULT 'open',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "risk_register" "status"       "VARCHAR(30) DEFAULT 'open'"
add_column "risk_register" "created_by_id" "INTEGER REFERENCES user(id)"

# roadmap_item
create_table "roadmap_item" "
CREATE TABLE IF NOT EXISTS roadmap_item (
    id INTEGER PRIMARY KEY,
    phase VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    year INTEGER NOT NULL,
    owner VARCHAR(120) NOT NULL DEFAULT '',
    status VARCHAR(50) NOT NULL DEFAULT 'planned',
    details TEXT DEFAULT '',
    start_date DATE,
    end_date DATE,
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "roadmap_item" "details"       "TEXT DEFAULT ''"
add_column "roadmap_item" "start_date"    "DATE"
add_column "roadmap_item" "end_date"      "DATE"
add_column "roadmap_item" "created_by_id" "INTEGER REFERENCES user(id)"

# protocol_rule
create_table "protocol_rule" "
CREATE TABLE IF NOT EXISTS protocol_rule (
    id INTEGER PRIMARY KEY,
    principle VARCHAR(150) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    implementation TEXT DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "protocol_rule" "implementation" "TEXT DEFAULT ''"
add_column "protocol_rule" "created_by_id"  "INTEGER REFERENCES user(id)"

# constitution_document
create_table "constitution_document" "
CREATE TABLE IF NOT EXISTS constitution_document (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(80) NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    version VARCHAR(20) DEFAULT '1.0',
    effective_date DATE,
    status VARCHAR(30) DEFAULT 'active',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "constitution_document" "version"        "VARCHAR(20) DEFAULT '1.0'"
add_column "constitution_document" "effective_date" "DATE"
add_column "constitution_document" "status"         "VARCHAR(30) DEFAULT 'active'"
add_column "constitution_document" "created_by_id"  "INTEGER REFERENCES user(id)"

echo ""
echo "── Program ──────────────────────────────────────────────"

# dissemination_event
create_table "dissemination_event" "
CREATE TABLE IF NOT EXISTS dissemination_event (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    event_date DATE NOT NULL,
    format VARCHAR(100) NOT NULL DEFAULT '',
    audience VARCHAR(120) DEFAULT 'public',
    linked_project VARCHAR(150) DEFAULT '',
    project_id INTEGER REFERENCES research_project(id),
    notes TEXT DEFAULT '',
    location VARCHAR(200) DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "dissemination_event" "audience"       "VARCHAR(120) DEFAULT 'public'"
add_column "dissemination_event" "linked_project" "VARCHAR(150) DEFAULT ''"
add_column "dissemination_event" "project_id"     "INTEGER REFERENCES research_project(id)"
add_column "dissemination_event" "notes"          "TEXT DEFAULT ''"
add_column "dissemination_event" "location"       "VARCHAR(200) DEFAULT ''"
add_column "dissemination_event" "created_by_id"  "INTEGER REFERENCES user(id)"

# monthly_report
create_table "monthly_report" "
CREATE TABLE IF NOT EXISTS monthly_report (
    id INTEGER PRIMARY KEY,
    month VARCHAR(20) NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "monthly_report" "created_at"    "DATETIME DEFAULT CURRENT_TIMESTAMP"
add_column "monthly_report" "created_by_id" "INTEGER REFERENCES user(id)"

echo ""
echo "── Polls ────────────────────────────────────────────────"

# poll
create_table "poll" "
CREATE TABLE IF NOT EXISTS poll (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    poll_type VARCHAR(20) DEFAULT 'single',
    status VARCHAR(30) DEFAULT 'open',
    deadline DATETIME,
    is_public BOOLEAN DEFAULT 0,
    public_token VARCHAR(64) UNIQUE,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "poll" "description"  "TEXT DEFAULT ''"
add_column "poll" "poll_type"    "VARCHAR(20) DEFAULT 'single'"
add_column "poll" "status"       "VARCHAR(30) DEFAULT 'open'"
add_column "poll" "deadline"     "DATETIME"
add_column "poll" "is_public"    "BOOLEAN DEFAULT 0"
add_column "poll" "public_token" "VARCHAR(64)"
add_column "poll" "entity_type"  "VARCHAR(50)"
add_column "poll" "entity_id"    "INTEGER"
add_column "poll" "created_by_id" "INTEGER REFERENCES user(id)"

# poll_option
create_table "poll_option" "
CREATE TABLE IF NOT EXISTS poll_option (
    id INTEGER PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES poll(id),
    option_text VARCHAR(300) NOT NULL,
    \"order\" INTEGER DEFAULT 0
);"
add_column "poll_option" "order" "INTEGER DEFAULT 0"

# poll_vote
create_table "poll_vote" "
CREATE TABLE IF NOT EXISTS poll_vote (
    id INTEGER PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES poll(id),
    option_id INTEGER NOT NULL REFERENCES poll_option(id),
    user_id INTEGER REFERENCES user(id),
    anon_token VARCHAR(64),
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);"
add_column "poll_vote" "anon_token" "VARCHAR(64)"
add_column "poll_vote" "voted_at"   "DATETIME DEFAULT CURRENT_TIMESTAMP"

# poll_token
create_table "poll_token" "
CREATE TABLE IF NOT EXISTS poll_token (
    id INTEGER PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES poll(id),
    token VARCHAR(64) NOT NULL UNIQUE,
    label VARCHAR(200) DEFAULT '',
    used BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    used_at DATETIME
);"
add_column "poll_token" "label"      "VARCHAR(200) DEFAULT ''"
add_column "poll_token" "used"       "BOOLEAN DEFAULT 0"
add_column "poll_token" "created_at" "DATETIME DEFAULT CURRENT_TIMESTAMP"
add_column "poll_token" "used_at"    "DATETIME"

echo ""
echo "── Task & Legacy ────────────────────────────────────────"

# task
create_table "task" "
CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    status VARCHAR(30) DEFAULT 'todo',
    priority VARCHAR(20) DEFAULT 'normal',
    due_date DATE,
    assigned_to_id INTEGER REFERENCES user(id),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    milestone_id INTEGER REFERENCES milestone(id),
    url VARCHAR(500) DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "task" "description"    "TEXT DEFAULT ''"
add_column "task" "status"         "VARCHAR(30) DEFAULT 'todo'"
add_column "task" "priority"       "VARCHAR(20) DEFAULT 'normal'"
add_column "task" "due_date"       "DATE"
add_column "task" "assigned_to_id" "INTEGER REFERENCES user(id)"
add_column "task" "entity_type"    "VARCHAR(50)"
add_column "task" "entity_id"      "INTEGER"
add_column "task" "milestone_id"   "INTEGER REFERENCES milestone(id)"
add_column "task" "url"            "VARCHAR(500) DEFAULT ''"
add_column "task" "created_by_id"  "INTEGER REFERENCES user(id)"

# legacy_task
create_table "legacy_task" "
CREATE TABLE IF NOT EXISTS legacy_task (
    id INTEGER PRIMARY KEY,
    category VARCHAR(80) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    owner VARCHAR(120) NOT NULL DEFAULT '',
    deadline DATE,
    status VARCHAR(30) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    notes TEXT DEFAULT '',
    url VARCHAR(500) DEFAULT '',
    created_by_id INTEGER REFERENCES user(id)
);"
add_column "legacy_task" "description"   "TEXT DEFAULT ''"
add_column "legacy_task" "owner"         "VARCHAR(120) NOT NULL DEFAULT ''"
add_column "legacy_task" "deadline"      "DATE"
add_column "legacy_task" "status"        "VARCHAR(30) DEFAULT 'pending'"
add_column "legacy_task" "priority"      "VARCHAR(20) DEFAULT 'normal'"
add_column "legacy_task" "notes"         "TEXT DEFAULT ''"
add_column "legacy_task" "url"           "VARCHAR(500) DEFAULT ''"
add_column "legacy_task" "created_by_id" "INTEGER REFERENCES user(id)"

echo ""
echo "── Audit & Attachments ──────────────────────────────────"

# audit_log
create_table "audit_log" "
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    user_id INTEGER REFERENCES user(id),
    action VARCHAR(30) NOT NULL,
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);"
add_column "audit_log" "field_changed" "VARCHAR(100)"
add_column "audit_log" "old_value"     "TEXT"
add_column "audit_log" "new_value"     "TEXT"
add_column "audit_log" "timestamp"     "DATETIME DEFAULT CURRENT_TIMESTAMP"

# attachment
create_table "attachment" "
CREATE TABLE IF NOT EXISTS attachment (
    id INTEGER PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    uploaded_by_id INTEGER REFERENCES user(id),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);"
add_column "attachment" "original_name"   "VARCHAR(255) NOT NULL DEFAULT ''"
add_column "attachment" "uploaded_by_id"  "INTEGER REFERENCES user(id)"
add_column "attachment" "uploaded_at"     "DATETIME DEFAULT CURRENT_TIMESTAMP"

# ─────────────────────────────────────────────────────────────────────────────
# VERIFY
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── Verification ─────────────────────────────────────────"

EXPECTED_TABLES=(
    user institution partnership
    research_project research_session project_membership
    booking facility equipment budget_item
    working_group working_group_membership
    meeting proposal_record
    policy_document risk_register roadmap_item protocol_rule constitution_document
    dissemination_event monthly_report
    poll poll_option poll_vote poll_token
    task legacy_task milestone
    audit_log attachment
)

ALL_OK=true
for t in "${EXPECTED_TABLES[@]}"; do
    count=$(sqlite3 "$DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='$t';")
    if [ "$count" -eq 1 ]; then
        printf "  ✓ %-35s\n" "$t"
    else
        printf "  ✗ %-35s  MISSING!\n" "$t"
        ALL_OK=false
    fi
done

echo ""
if [ "$ALL_OK" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✓ Migration complete. All tables present."
    echo "  Backup kept at: $BACKUP"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✗ Some tables are still missing. Check errors above."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi

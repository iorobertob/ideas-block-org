# Kompresorinė Governance Platform

A working Flask web application that turns the LMTA + Ideas Block – Kompresorinė proposal into a practical online governance and operations platform.

## What it covers

- role-based login with seeded demo users
- governance log for steering, operations, curatorial, and partnership meetings
- research project registry
- room booking with conflict detection
- portable equipment inventory and transfer planning
- budget ledger for pilot and continuation phases
- institution and partnership pipeline
- Kompresorinė Protocol registry and policy library
- risk register
- Phase I / Phase II roadmap tracker
- public dissemination event tracker
- monthly reports archive
- calls & deadlines tracker (conferences, journals, festivals, residencies) with subscription and email reminders

## Tech stack

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Migrate (Alembic — schema migrations)
- SQLite (default) — switchable to PostgreSQL via `DATABASE_URL` env var
- Bootstrap 5

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:

```
http://127.0.0.1:5004
```

The database is created automatically on first run at `instance/kompresorine.db` and seeded with demo data.

## Demo accounts

| Email | Password | Role |
|---|---|---|
| `admin@example.com` | `admin123` | Admin |
| `director@example.com` | `director123` | Director |
| `coordinator@example.com` | `coord123` | Coordinator |
| `researcher@example.com` | `research123` | Member |

## Environment variables

All optional — the app runs with defaults if none are set.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | SQLite in `instance/` | Override to use PostgreSQL: `postgresql://user:pass@host/dbname` |
| `MAIL_SERVER` | _(empty — console logging)_ | SMTP host for email notifications |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USE_TLS` | `1` | Set to `0` to disable TLS |
| `MAIL_USERNAME` | _(empty)_ | SMTP login |
| `MAIL_PASSWORD` | _(empty)_ | SMTP password |
| `MAIL_FROM` | `noreply@kompresorine.local` | Sender address |

## Schema migrations

The project uses **Flask-Migrate** (Alembic) for schema changes. The database is always at `instance/kompresorine.db` (SQLite) or wherever `DATABASE_URL` points.

### Making a schema change

1. Edit `app/models.py` to add/modify a column or table.
2. Generate a migration:
   ```bash
   FLASK_APP=app.py flask db migrate -m "short description of change"
   ```
3. Review the generated file in `migrations/versions/`.
4. Apply it:
   ```bash
   FLASK_APP=app.py flask db upgrade
   ```

### On the production server (after pulling new code)

```bash
FLASK_APP=app.py flask db upgrade
```

This is the only command needed after a deploy that includes schema changes. It is idempotent — safe to run even if the DB is already up to date.

### Other useful commands

```bash
# Check current migration version
FLASK_APP=app.py flask db current

# Show pending migrations
FLASK_APP=app.py flask db heads

# Downgrade one step (use with care on production)
FLASK_APP=app.py flask db downgrade
```

### Migrating to PostgreSQL

The ORM models are backend-agnostic. To switch:

1. Install the PostgreSQL driver:
   ```bash
   pip install psycopg2-binary
   ```
2. Set the environment variable before starting the app:
   ```bash
   export DATABASE_URL=postgresql://user:pass@localhost/kompresorine
   ```
3. Run migrations to create the schema on the new DB:
   ```bash
   FLASK_APP=app.py flask db upgrade
   ```
4. Migrate existing data with `pgloader` (handles SQLite → PostgreSQL type translation automatically):
   ```bash
   pgloader sqlite:///instance/kompresorine.db postgresql://user:pass@localhost/kompresorine
   ```

> **Use PostgreSQL, not MySQL/MariaDB.** The query layer uses `nullslast()` ordering which works natively in PostgreSQL but not in MySQL.

## File structure

```
ORG_GOVERNANCE_V2/
├── app.py                  # entry point — flask run target
├── requirements.txt
├── README.md
├── migrate.sh              # legacy — kept for reference only, do not use
├── instance/               # git-ignored — runtime files
│   └── kompresorine.db     # SQLite database (auto-created)
├── migrations/             # Alembic migration history — committed to git
│   └── versions/
└── app/
    ├── __init__.py         # app factory + Flask-Migrate init
    ├── models.py           # SQLAlchemy models
    ├── routes.py           # all routes
    ├── seed.py             # demo data seeding
    └── templates/
```

## TODOs

- There should also be predefined formats/types on the events. Options are set by the admin dashboard: exhibitions, concerts, talk, workshop, discussion, colloquia, staff meeting, other. and the capacity to add, edit or remove these types.
- In budget, capability to save, categorise and archive per rubric and time and project and executer, invoices both outgoing or incoming.
- Beautify the whole interface to make it more calling to use by having a more modern, contemporary, aesthetic, minimalistic, state of the art UX and UI.
- Journal entries, should be able to be expanded into their own page with detailed information when clicking on them from wherever they are listed.
- add UX and UI for file uploads to say show to the user the upload progress. On file download link/icon show the size of the file.
- uploaded files to journal sessions should be shown in the listing of the session or its card, so user can quickly click and open them.
- the +log session, or + New meeting, or +New Working group, in the projects or in the governance, or anywhere needed, should open a richer page where to create a new entry, with all the fields and file upload ux available.
- capability to upload files to working groups, meetings, sessions and projects, or all relevant items.
- Participants on the logged sessions should be able to be selected in the text box from the registered users in the platform by using a type and autocomplete UX, but also be able to be typed in, in case they are not registered in the platform.
- There should be UX and UI for establishing governance and working groups periodic meetings, with all the required fields for good governance practice.
- relate voting to projects, meetings, journal sessions, and working groups, and to be able to launch them from there.
- items and facilities should be able to be booked from the list where they appear or from their detail page.

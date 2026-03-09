# Kompresorinė Governance Platform

A working Flask web application that turns the LMTA Mokslo centras + Ideas Block – Kompresorinė proposal into a practical online governance and operations platform.

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

## Tech stack

- Python 3
- Flask
- Flask-SQLAlchemy
- SQLite
- Bootstrap 5

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Demo accounts

- `admin@example.com` / `admin123`
- `director@example.com` / `director123`
- `coordinator@example.com` / `coord123`
- `researcher@example.com` / `research123`

## File structure

```text
kompresorine_platform/
├── app.py
├── requirements.txt
├── README.md
├── instance/
└── app/
    ├── __init__.py
    ├── models.py
    ├── routes.py
    ├── seed.py
    └── templates/
```

## Notes

This is a real local web app, not just mockup screens. It is intended as a strong prototype / MVP that you can extend into a production platform with richer permissions, file uploads, email notifications, and analytics.

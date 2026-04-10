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


## Important upgrade note

This version adds record-detail pages and owner-based editing. Delete any old SQLite database before first run so the new schema is created:

```bash
rm -f instance/kompresorine.db
```

## TODOs
- There should also be predefined formats/types on the events. Options areset by the admin dashboard: exhibitions, concerts, talk, workshop, discussion, colloquia, staff meeting, other. and the capacity to add, edit or remove these types. 
- In budget, capability to save, categorise and archive per rubric and time and project and executer, invoices both outgoing or incoming.
- Beautify the whole interface to make it more calling to use by having a more modern, contemporary, aesthetic, minimalistic , state of the art UX and UI. 
- Journal entries, should be able to be expanded into their own page with detailed information when clicking on them from wherever they are listed. 
- add UX and UI for file uploads to say show to the user the upload progress. On file download link/icon show the size of the file. 
- uploaded files to journal sessions should be shown in the listing of the session or its card, so user can quickly clidk and open them. 
- the +log session, or + New meeting, or +New Working group,  in the projects or in the governance, or anywhere needed,  should open a richer page where to create a new entry, with all the fields and file upload ux available.
- capatility to upload files to working groups, meetings, sessions and projects, or all relevant items.  
- Participants on the logged sessions should be able to be selected in the text box from the regiestered useres in teh platform by using a type and autocomplete UX, but also be able to be typed in, in case they are not registered in the platform. 
- There should be UX and UI for establishing governance and working groups periodic meetings, with all the required fields for good governance practice. 
- relate voting to projects, meetins, journal sessions, and working gropus, and to be able to launche them from there
- items and facilities should be able to be booked from the list where they appear or from their detail page

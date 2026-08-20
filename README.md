# NextWise Education — Demo_Repo

NCLEX-RN/PN preparation platform. Phase 1, Milestone 1 (Foundation & Schema): Django REST API, auth, and the NGN-ready question bank schema.

## Repo layout

```
backend/    Django project (see backend/README below for setup)
docs/       Architecture diagram, content-team question template
render.yaml Render Blueprint (web + PostgreSQL services)
```

## Local setup

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env   # fill in SECRET_KEY, DATABASE_URL, etc.

.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Requires a running PostgreSQL instance — point `DATABASE_URL` in `.env` at it. Emails (verification, password reset) print to the console in local dev, no SendGrid key required.

## Tests

```bash
cd backend
.venv/bin/python manage.py test
```

## Docs

- [`docs/architecture.md`](docs/architecture.md) — system diagram
- [`docs/content_team_question_template.md`](docs/content_team_question_template.md) — CSV format for question writers

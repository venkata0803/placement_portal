# Placement Portal Application

A full-stack campus placement management system built for the IIT Madras BS Degree **Modern Application Development II (MAD-II)** project.

Admins approve companies and drives, manage blacklists, and receive monthly reports. Companies create placement drives and manage applicants. Students browse eligible drives, apply, and track application status.

---

## Project Overview

| Role | Capabilities |
|------|----------------|
| **Admin** | Dashboard stats, approve/reject companies & drives, blacklist/activate students & companies, profile, monthly email report |
| **Company** | Profile, create/edit/close drives, review applicants, schedule interviews, CSV export |
| **Student** | Profile + resume, browse/search drives, apply, track applications, CSV export |

---

## Technologies Used

### Backend
- **Flask** – Python web framework
- **Flask-SQLAlchemy** – ORM
- **Flask-Migrate** – Database migrations
- **Flask-CORS** – Frontend ↔ backend CORS
- **Flask-JWT-Extended** – JWT authentication
- **Flask-Caching** – Redis response caching
- **Flask-Mail** – Email via MailHog (local SMTP for reminders + monthly report)
- **Celery** – Background tasks (reminders, reports, CSV export)
- **Redis** – Cache + Celery broker/result backend
- **SQLite** – Database

### Frontend
- **Vue 3** – SPA framework
- **Vite** – Dev server & build
- **Vue Router** – Client-side routing
- **Axios** – HTTP client
- **Bootstrap 5** – UI styling

---

## Project Structure

```
placement_portal_application_23f1000054/
├── backend/                   # Flask API, models, Celery, Redis cache, Mail
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── celery_app.py
│   ├── celery_worker.py
│   ├── tasks.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── uploads/resumes/
│   └── exports/
├── frontend/                  # Vue 3 + Vite SPA
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── README.md
├── requirements.txt           # Python dependencies
├── api.yaml                   # OpenAPI documentation
├── Project_Report.pdf
├── .gitignore
└── .env.example               # Copy to backend/.env before running
```

---

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (local, default port `6379`)
- MailHog (local SMTP on port `1025`, UI on `8025`) — no real email account needed

---

## Backend Setup

```bash
# From project root
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt

# Copy env file into backend (Flask loads backend/.env)
copy .env.example backend\.env   # Windows
# cp .env.example backend/.env   # macOS / Linux

cd backend
python app.py
```

Edit `backend/.env` for JWT secret, Redis URL, and MailHog settings (defaults work for local demos).

Backend: http://localhost:5000/  
Expected: `{"message": "Placement Portal Backend Running"}`

On first start the app creates SQLite tables and a default admin user.

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173/

Production build:

```bash
npm run build
```

---

## Redis

Redis is required for:
- Flask-Caching (dashboard / drive list caching)
- Celery broker and result backend

Start Redis (examples):

```bash
# Windows (if installed as a service or via Memurai/WSL)
redis-server

# Docker
docker run -d -p 6379:6379 redis:7
```

Default URL in `.env`: `REDIS_URL=redis://localhost:6379/0`

---

## Celery Worker

From the `backend` folder with the venv active and Redis running:

```bash
cd backend

# Windows
python -m celery -A celery_worker:celery worker --loglevel=info --pool=solo

# macOS / Linux
python -m celery -A celery_worker:celery worker --loglevel=info
```

Handles: daily reminders, monthly report, CSV exports, `/test-celery` demo task.

---

## Celery Beat

Schedules periodic jobs (daily reminders + monthly report):

```bash
cd backend
python -m celery -A celery_worker:celery beat --loglevel=info
```

- Daily reminders: 9:00 AM Asia/Kolkata (or every minute if `CELERY_BEAT_TEST_MODE=true`)
- Monthly report: 1st of each month at 09:00 Asia/Kolkata

Admin can also trigger manually:
- `POST /admin/test-reminder`
- `POST /admin/test-monthly-report`

---

## MailHog

All project emails (daily reminders, interview reminders, monthly HTML reports) are sent through **MailHog**, a local SMTP catcher. **No real email account is required.**

### Start MailHog

```bash
# Docker (recommended)
docker run -d --name mailhog -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Or download a binary from https://github.com/mailhog/MailHog/releases
```

### MailHog UI

Open http://localhost:8025 to view captured emails (HTML formatting is preserved).

### SMTP

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `1025` |
| TLS / SSL | Off |
| Auth | None |

Configured in `backend/.env` (see root `.env.example`):

```
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USE_SSL=False
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=placement-portal@localhost
MAIL_SUPPRESS_SEND=false
```

Keep `MAIL_SUPPRESS_SEND=false` so emails appear in MailHog. Trigger reminders/reports via Celery Beat or admin endpoints `POST /admin/test-reminder` and `POST /admin/test-monthly-report`.

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@placementportal.com` | `admin123` |

Student and company accounts: register via the UI. Companies must be **Approved** by admin before login.

---

## Project Features

- JWT role-based auth (admin / student / company)
- Student registration, profile, resume upload, drive search & apply
- Company registration (pending approval), profile, drive CRUD, applicant workflow, interviews
- Admin dashboard, company/drive approval, student & company blacklist
- Admin & company profile editing
- Redis caching with invalidation on writes
- Celery: interview reminders, **current-month** placement report email, async CSV export
- Bootstrap UI with role-specific sidebars

---

## Architecture

```
Vue 3 (Vite)  --Axios/JWT-->  Flask REST API  -->  SQLite
                                   |
                    Redis (cache + Celery broker)
                                   |
                         Celery Worker / Beat
                                   |
                         MailHog (Flask-Mail → :1025)
```

1. Frontend stores JWT after login and sends `Authorization: Bearer <token>`.
2. Role decorators protect `/admin/*`, `/student/*`, `/company/*`.
3. Cache stores selected GET responses; mutations invalidate related keys.
4. Heavy / scheduled work runs in Celery workers.

---

## API Information

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/register/student` | Student signup |
| POST | `/register/company` | Company signup |
| POST | `/login` | Get JWT |
| POST | `/logout` | Logout |
| GET | `/me` | Current user |

### Admin (JWT admin)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/dashboard` | Summary stats |
| GET | `/admin/students` | List students |
| PUT | `/admin/student/<id>/blacklist` | Blacklist student |
| PUT | `/admin/student/<id>/unblacklist` | Activate student |
| GET | `/admin/companies` | List companies |
| PUT | `/admin/company/<id>/approve` | Approve company |
| PUT | `/admin/company/<id>/reject` | Reject company |
| PUT | `/admin/company/<id>/blacklist` | Blacklist company |
| PUT | `/admin/company/<id>/unblacklist` | Activate company |
| GET | `/admin/drives` | List drives |
| PUT | `/admin/drives/<id>/approve` | Approve drive |
| PUT | `/admin/drives/<id>/reject` | Reject drive |
| GET/PUT | `/admin/profile` | Admin profile |
| POST | `/admin/test-reminder` | Queue reminders |
| POST | `/admin/test-monthly-report` | Queue monthly report |
| GET | `/test-celery` | Celery hello task (admin only) |

### Company (JWT company)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/company/dashboard` | Dashboard |
| GET/PUT | `/company/profile` | Company profile |
| GET/POST | `/company/drives` | List / create drives |
| PUT | `/company/drives/<id>` | Update drive |
| PATCH | `/company/drives/<id>/close` | Close drive |
| GET | `/company/drives/<id>/applications` | Applicants |
| PUT | `/company/application/<id>/status` | Update status |
| PUT | `/company/application/<id>/interview` | Schedule interview |
| GET | `/company/application/<id>/resume` | Download resume |
| POST | `/company/export/<drive_id>` | Queue CSV export |
| GET | `/company/export/download/<filename>` | Download CSV |

### Student (JWT student)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/student/dashboard` | Dashboard |
| GET/PUT | `/student/profile` | Profile |
| POST | `/student/upload-resume` | Resume PDF |
| GET | `/student/drives` | Browse/search approved drives |
| POST | `/student/apply/<drive_id>` | Apply |
| GET | `/student/applications` | My applications |
| POST | `/student/export` | Queue CSV export |
| GET | `/student/export/download/<filename>` | Download CSV |

---

## Quick Start (Evaluator)

1. Extract the ZIP so you get a single folder `placement_portal_application_23f1000054/`.
2. **Redis:** start Redis on port 6379.
3. **MailHog:** `docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog` (UI: http://localhost:8025).
4. **Backend:**
   ```bash
   cd placement_portal_application_23f1000054
   python -m venv venv
   # activate venv
   pip install -r requirements.txt
   copy .env.example backend\.env
   cd backend
   python app.py
   ```
5. **Celery worker:**
   ```bash
   cd backend
   python -m celery -A celery_worker:celery worker --loglevel=info --pool=solo
   ```
6. **Celery beat (optional for scheduled jobs):**
   ```bash
   cd backend
   python -m celery -A celery_worker:celery beat --loglevel=info
   ```
7. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
8. Open http://localhost:5173/ and login as admin (`admin@placementportal.com` / `admin123`).

---

## Known Limitations

- SQLite is used for local/demo deployment (not multi-writer production scale).
- JWT logout is client-side only (no server token blacklist).
- Monthly report “Selected this month” uses application date + current status (no separate status-change timestamp).
- Company “approved this month” is approximated via registration month of approved companies (no separate `approved_at` column).
- Emails are captured by MailHog locally (no external SMTP); start MailHog before triggering reminder/report jobs.
- Resume uploads are stored on the local filesystem under `backend/uploads/resumes/`.

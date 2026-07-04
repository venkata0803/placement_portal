# Placement Portal Application

A web application for managing campus placements. Built as part of the IIT Madras BS Degree App Dev 2 project.

## Tech Stack

### Backend
- **Flask** – Python web framework
- **Flask-SQLAlchemy** – Database ORM
- **Flask-Migrate** – Database migrations
- **Flask-CORS** – Cross-origin requests (frontend ↔ backend)
- **Flask-JWT-Extended** – JWT authentication (for later)
- **SQLite** – Database
- **Redis** – Caching / message broker (for later)
- **Celery** – Background tasks (for later)

### Frontend
- **Vue 3** – JavaScript framework
- **Vite** – Build tool and dev server
- **Vue Router** – Page navigation
- **Axios** – HTTP requests to backend
- **Bootstrap 5** – UI styling

## Folder Structure

```
placement_portal/
├── backend/
│   ├── app.py              # Flask app entry point
│   ├── config.py           # Configuration settings
│   ├── extensions.py       # Flask extensions (db, cors, jwt, etc.)
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Example environment variables
│   ├── models/             # Database models (later)
│   ├── routes/             # API routes (later)
│   ├── services/           # Business logic (later)
│   ├── utils/              # Helper functions (later)
│   ├── tasks/              # Celery tasks (later)
│   ├── templates/          # HTML templates (if needed)
│   └── static/             # Static files (if needed)
├── frontend/
│   ├── src/
│   │   ├── assets/         # Images, icons
│   │   ├── components/     # Reusable Vue components (later)
│   │   ├── views/          # Page components (Home.vue)
│   │   ├── router/         # Vue Router setup
│   │   └── services/       # API calls (Axios)
│   └── public/             # Public static files
├── README.md
└── .gitignore
```

## How to Run the Backend

1. Open a terminal and go to the backend folder:

   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file and edit if needed:

   ```bash
   copy .env.example .env
   ```

5. Start the Flask server:

   ```bash
   python app.py
   ```

6. Test the backend in a browser or with curl:

   - URL: http://localhost:5000/
   - Expected response: `{"message": "Placement Portal Backend Running"}`

## How to Run the Frontend

1. Open a **new** terminal and go to the frontend folder:

   ```bash
   cd frontend
   ```

2. Install Node.js dependencies (only needed the first time):

   ```bash
   npm install
   ```

3. Start the Vite development server:

   ```bash
   npm run dev
   ```

4. Open the URL shown in the terminal (usually http://localhost:5173/)

5. The home page will show **Placement Portal Application**, **Backend Status**, and a button to check the backend again.

## Notes

- Run **both** backend and frontend for the status check to show "Online".
- Authentication, models, and APIs will be added in later milestones.

# course_reg

Django Course Registration Portal — development setup for local presentation.

## Quick start (for your friend - exact commands)

1. Clone the repo
   git clone https://github.com/<your-username>/course_reg.git
   cd course_reg

2. Create & activate virtualenv
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python -m venv venv
   source venv/bin/activate

3. Install dependencies
   pip install -r requirements.txt

4. Ensure settings are correct
   - This repo uses SQLite by default (db.sqlite3 is ignored).
   - If `AUTH_USER_MODEL` is set to 'courses.User' ensure migrations are present (they are included).
   - For a quick demo you can keep DEBUG=True in `course_reg/settings.py`.

5. Apply migrations
   python manage.py migrate

6. Load demo data (optional but recommended)
   python manage.py loaddata dummy_data.json

7. Create a superuser (to login at /admin)
   python manage.py createsuperuser --email admin@example.com
   # choose a password and remember it

   (Alternatively, use the following demo credentials if you prefer to not create a superuser:
    - email: admin@example.com
    - password: admin123
    But creating a superuser is recommended.)

8. Run the development server
   python manage.py runserver

9. Open the site:
   - Main pages: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin (login with superuser you created)

## Notes
- Do NOT commit `db.sqlite3` or `.env` (they are in `.gitignore`).
- If migrations are missing, run `python manage.py makemigrations` then `python manage.py migrate`.
- If anything fails, check the README troubleshooting section below.

## Troubleshooting
- “ModuleNotFoundError: No module named ...” — ensure virtualenv is active and `pip install -r requirements.txt` ran successfully.
- If `createsuperuser` fails because of `AUTH_USER_MODEL` mismatch, ensure `AUTH_USER_MODEL = 'courses.User'` is set in `course_reg/settings.py` before first migration.
- If loaddata fails due to FK issues, ensure migrations have been applied.

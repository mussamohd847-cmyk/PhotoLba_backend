# ShuleBora Backend

Flask + MySQL backend for the supplied ShuleBora React frontend.

## Install
```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Database
```bash
mysql -u root -p < database/schema.sql
```
If root has no password:
```bash
mysql -u root < database/schema.sql
```

Then:
```bash
python database/seed_admin.py
python run.py
```

API: http://127.0.0.1:5000
Health: http://127.0.0.1:5000/api/health

## SuperAdmin
Email: admin@shulebora.co.tz
Password: Admin@123

Change this password after first login.

## API
Auth: /api/auth/register, /api/auth/login, /api/auth/me
Schools: /api/schools
Activities: /api/activities
Features/Facilities/Qualifications/Contacts: /api/content/{kind}
Images: /api/content/images
Users: /api/users
Messages: /api/contact
Dashboard: /api/dashboard/stats
Likes: /api/dashboard/schools/{id}/like

React API base:
const API_URL = "http://127.0.0.1:5000/api";

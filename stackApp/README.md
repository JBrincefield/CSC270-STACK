
# Hotdog Delivery Application — Quick Start

A Django 6 web app for placing hotdog orders with Firebase email/password authentication, Firestore persistence, and role-based access (users see their own orders; admins see all orders and can update status).

---

## Fast Start (Windows PowerShell)

### 1 — Navigate to the project folder

```powershell
cd C:\NEU\Y3\Q3\CSC270-S2\repository\stackApp
```

### 2 — Create and activate a virtual environment

```powershell
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\.venv\Scripts\Activate.ps1
```

### 3 — Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4 — Apply database migrations (needed for sessions)

```powershell
py manage.py migrate
```

### 5 — Start the server

The `.env` file in this folder already contains all required credentials. Just run:

```powershell
py manage.py runserver
```

### 6 — Open the app

```
http://127.0.0.1:8000/
```

---

## Environment variables (`.env`)

All configuration lives in `stackApp/.env`. The file is already populated for this project:

| Variable | Purpose |
|----------|---------|
| `FIREBASE_CREDENTIALS` | Path to the Firebase Admin SDK service account JSON (relative to `stackApp/`) |
| `FIREBASE_WEB_API_KEY` | Firebase web API key (used by the browser SDK and server-side token verification) |
| `FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `FIREBASE_STORAGE_BUCKET` | Firebase storage bucket |
| `FIREBASE_MESSAGING_SENDER_ID` | Firebase messaging sender ID |
| `FIREBASE_APP_ID` | Firebase app ID |

`settings.py` loads this file automatically via `python-dotenv` on startup.

---

## Authentication

The app uses **Firebase Authentication with email and password**.

- Visiting `/order/` without being signed in redirects to the login page.
- Use **Sign In** to log in with an existing account, or **Create Account** to register.
- After sign-in, the server verifies the Firebase ID token against the Firebase REST API and creates a Django session.
- The navbar shows your name and a **Log Out** button on every page.

### User roles

| Role | What they see | What they can do |
|------|--------------|-----------------|
| Regular user | Their own orders only | Place orders, edit their own orders (hotdog, qty, price, notes). Customer name is locked to their account name. |
| Admin | All orders from all users | Everything above + change order status (including marking as **Completed**) + edit customer name |

### Order statuses

| Status | Meaning |
|--------|---------|
| `pending` | Just placed, awaiting processing |
| `processing` | Being prepared |
| `ready` | Ready for pickup/delivery |
| `delivered` | Delivered to customer |
| `completed` | Admin-confirmed complete — appears on the public Review Wall on the home page |
| `cancelled` | Cancelled |

Only an admin can set an order to **Completed**. Once completed, the order appears on the home page Review Wall where any logged-in user can leave a 👍 or 👎.

### Making a user an admin

1. Sign in at least once so the user exists in Firebase Auth.
2. Find their Firebase UID: **Firebase Console → Authentication → Users → copy the UID** column.
3. Open **Firestore Console → Data → `admins` collection** (create it if it doesn't exist).
4. Add a new document with a single field:
   ```
   uid: <paste-uid-here>   (type: string)
   ```
5. Sign out and sign back in — admin status is checked at login. The navbar will show an **Admin** badge and the Order page will display all users' orders.

> **In-memory fallback (no Firebase):** call `dal.add_admin_uid("<uid>")` in a Django shell to grant admin access for the current server process.

---

## Project structure

```
stackApp/
├── .env                        # credentials and config (loaded automatically)
├── manage.py
├── requirements.txt
├── csc270-stackapp-aa78c-firebase-adminsdk-fbsvc-cb27161275.json   # Admin SDK service account
├── hotdogdelivery/
│   ├── dal.py                  # Firestore or in-memory data access + admin checks
│   ├── views.py                # page views + REST API + auth endpoints
│   ├── context_processors.py   # injects current_user into every template
│   ├── templates/              # HTML templates
│   └── static/                 # CSS and images
└── stackApp/
    ├── settings.py             # Django settings — loads .env on startup
    └── urls.py
```

---

## API endpoints

All order endpoints require an authenticated session (sign in via the UI first).

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/auth/verify/` | Exchange a Firebase ID token for a Django session |
| `POST` | `/api/auth/logout/` | Clear the Django session |
| `GET` | `/api/orders/` | List orders (own orders, or all for admins) |
| `POST` | `/api/orders/` | Create a new order |
| `GET` | `/api/orders/<id>/` | Get a single order |
| `PUT` | `/api/orders/<id>/` | Update an order (status and customerName are admin-only fields) |
| `DELETE` | `/api/orders/<id>/` | Cancel an order |
| `POST` | `/api/orders/<id>/review/` | Like or dislike a completed order (`{"reaction": "like"\|"dislike"}`) |
| `GET` | `/api/kanye/` | Random Kanye quote |

---

## Firebase configuration

Token verification uses the Firebase REST `accounts:lookup` endpoint — only the web API key is required. The Admin SDK service account (`FIREBASE_CREDENTIALS`) is used for Firestore persistence and admin lookups; if it is missing, the app falls back to in-memory storage.

Both backends use the same Firebase project: **csc270-stackapp**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'firebase_admin'` | Activate your venv and run `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'dotenv'` | Activate your venv and run `pip install -r requirements.txt` |
| Orders not persisting after restart | Check that `FIREBASE_CREDENTIALS` in `.env` points to the correct JSON file |
| Sign-in or sign-up shows "Authentication failed" | The Firebase web API key in `.env` may be wrong or Email/Password auth is not enabled in the Firebase Console |
| Sign-in times out | Check your internet connection — token verification calls the Firebase REST API |
| User not recognised as admin after Firestore change | Sign out and sign back in to refresh the session |

---

## Authors
- **Ethan Townsend** [(snxethan)](https://www.ethantownsend.dev)
- **Jacob Brincefield** [(jbrincefield)](https://www.jacobbrincefield.com)
- **Tommy Southerland** [(Tomonator1000)](https://www.weenie.com)

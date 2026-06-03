# Hotdog Delivery Application — Instructor Quick Start

This is a small Django 6 web application for placing playful "hotdog" orders. It supports
two data backends:

- Firestore via the Firebase Admin SDK (persistent) — used when you point the app at a
  service account JSON file via the FIREBASE_CREDENTIALS environment variable.
- An in-memory fallback (non-persistent) used when Firestore is not configured.

This README is streamlined for an instructor who wants to install and run the app locally
— including using the included Firebase credentials JSON to enable persistence.

Checklist:

1. Prepare environment (Python + virtualenv)
2. Install Python dependencies
3. (Optional) Configure Firebase credentials JSON and point the app to it
4. Run the Django development server and verify

If you just want to get the app running quickly, follow the "Fast Start" section. If you
want more explanation about each step, read the subsequent sections.

Fast Start (Windows PowerShell)

1. Open PowerShell and change to the project folder:

```powershell
cd stackApp
```

2. Create and activate a virtual environment (isolates dependencies):

```powershell
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\.venv\Scripts\Activate.ps1
```

3. Install required Python packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. (Optional, to persist orders) Point the app at the included Firebase credentials JSON and start the server.
   - Example (this repository includes `csc270-stackapp-firebase-adminsdk-fbsvc-f472f3aa80.json` at the repo root):

This is an optional step, but required for Phase 3 of CSC270. You can bypass the firebase-setup and use in-memory storage.
This path should work on the root, but if you move the JSON file or want to use your own, update the path accordingly. The key is that the environment variable must be set in the same shell session where you start the server.

```powershell
$env:FIREBASE_CREDENTIALS = "csc270-stackapp-firebase-adminsdk-fbsvc-f472f3aa80.json"
py manage.py runserver
```

5. Without Firebase (in-memory fallback) just run:

```powershell
py manage.py runserver
```

6. Open the app in your browser:

http://127.0.0.1:8000/

What each step does (brief explanations)

- python -m venv .venv — creates an isolated virtual environment so package installs don't affect your system Python.
- Activate.ps1 — activates the venv for the current PowerShell session.
- pip install -r requirements.txt — installs Django, firebase-admin (optional), requests, and any other dependencies listed in the file.
- Setting $env:FIREBASE_CREDENTIALS — tells the app where to find the Firebase service account JSON so the DAL can initialize firebase_admin and connect to Firestore. If this variable is not set or initialization fails, the app uses an in-memory list for orders.
- py manage.py runserver — starts Django's development server on http://127.0.0.1:8000/.

Notes about the included Firebase JSON

- This repository includes `csc270-stackapp-firebase-adminsdk-fbsvc-f472f3aa80.json`. If you set
  FIREBASE_CREDENTIALS to its absolute path before starting the server, the app will use Firestore
  to store orders persistently (they will remain after a server restart).
- Security: in production you should NOT commit secrets to the repository. For this assignment the
  file is included for convenience. If you use your own credentials, store them somewhere safe
  (outside the repo) and point FIREBASE_CREDENTIALS to that file.

Verify Firestore persistence (quick test)

1. Start the server with FIREBASE_CREDENTIALS set (see Fast Start step 4).
2. Create an order in the web UI or with this PowerShell command in another shell:

```powershell
$body = @{
  customerName = "Test User"
  hotdogName = "Chicago"
  unitPrice = 5.99
  quantity = 2
  notes = "Extra mustard"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/orders/" -Method POST -Body $body -ContentType "application/json"
```

3. Open the Firebase Console -> Firestore and inspect the `orders` collection — you should see the test order.
4. Stop the server (Ctrl+C) and restart it; the order should still be present if Firestore was used.

Project structure (important files)

```
stackApp/
├── manage.py
├── requirements.txt
├── hotdogdelivery/
│   ├── dal.py            # data access layer: Firestore or in-memory
│   ├── views.py          # routes and API endpoints
│   ├── templates/        # HTML templates
│   └── static/           # static assets (images, CSS)
└── stackApp/             # Django project settings
```

API endpoints (useful for testing)

- GET /api/orders/ — list all orders
- POST /api/orders/ — create a new order
- GET /api/orders/<id>/ — view one order
- PUT /api/orders/<id>/ — update one order
- DELETE /api/orders/<id>/ — delete one order
- GET /api/kanye/ — returns a Kanye quote (or fallback)

Data behavior summary

- If FIREBASE_CREDENTIALS is set and firebase_admin initializes successfully, orders are
  stored in Firestore and persist across server restarts.
- If FIREBASE_CREDENTIALS is not set or initialization fails, the DAL uses an in-memory list and
  orders are lost when the server restarts. The API and UI behave the same in either case.

Troubleshooting (common problems and quick fixes)

- "ModuleNotFoundError: No module named 'firebase_admin'" — activate your venv and run `pip install -r requirements.txt`.
- Server logs show Firestore initialization errors — check the value of `$env:FIREBASE_CREDENTIALS` in the same shell where you started the server and ensure the path is absolute and readable.
- Still seeing in-memory behavior despite setting FIREBASE_CREDENTIALS — ensure the var is set in the _same_ shell session before starting the server (environment variables are read at process start).

Extras (make FIREBASE_CREDENTIALS persistent)

- Persist for your user (Windows):

```powershell
setx FIREBASE_CREDENTIALS "C:\path\to\your\service-account.json"
# then open a new PowerShell session for the change to take effect
```

- Or create a small startup script `run-with-firebase.ps1` in `stackApp` that sets the env var, activates the venv, and starts the server.

If you'd like, I can also:

- Add a short `run-with-firebase.ps1` into the repository that uses the included JSON (for instructor convenience), or
- Produce a one-page cheat sheet with the exact PowerShell commands tailored to your machine.

# Authors

- **Ethan Townsend** [(snxethan)](https://www.ethantownsend.dev)
- **Jacob Brincefield** [(jbrincefield)](https://www.jacobbrincefield.com)
- **Tommy Southerland** [(Tomonator1000)](https://www.weenie.com)

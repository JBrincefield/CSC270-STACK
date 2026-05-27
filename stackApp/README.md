# Hotdog Delivery Application

A Django 6 web app for browsing a playful hotdog brand, reading the mission page, and placing hotdog orders with optional persistent storage via Firebase Firestore.

---

## ⚡ Quick Start for Professor

**This project includes a Firebase Admin SDK credentials file** to enable order persistence. Follow these steps to get the app running:

### Minimal Setup (2–3 minutes)

1. **Install Python 3.8+** if not already installed
   - Check: `python --version`
   - If needed, download from [python.org](https://www.python.org/)

2. **Navigate to the project folder:**
   ```powershell
   cd <unzipped-project>\stackApp
   ```

3. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
   .\.venv\Scripts\Activate.ps1
   ```

4. **Install dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Run the development server:**
   ```powershell
   py manage.py runserver
   ```

6. **Open your browser to:**
   ```
   http://127.0.0.1:8000/
   ```

✅ **That's it!** The app runs with **in-memory storage by default** (orders reset on server restart). Orders persist across server restarts if you set up the Firebase credentials (optional—see below).

### Using the Included Firebase JSON File (Optional)

If you want orders to persist across server restarts:

1. **Set the environment variable** to point to the included Firebase credentials file:
   ```powershell
   $env:FIREBASE_CREDENTIALS = "<unzipped-project>\csc270-stackapp-firebase-adminsdk-fbsvc-f472f3aa80.json"
   ```

2. **Restart the server:**
   ```powershell
   py manage.py runserver
   ```

3. **Test persistence:**
   - Create an order through the UI
   - Stop the server (Ctrl+C)
   - Restart the server
   - The order is still there ✓

**Note:** The included JSON file is configured for a specific Firebase project. If you use it, orders will be stored in that cloud project. You can always revert to in-memory storage by unsetting the environment variable or omitting it.

### App Features

- **Home page**: Browse the hotdog brand with a Kanye West quote card
- **Mission page**: Learn about hotdogs vs. sausages
- **Order page**: Place orders, view and manage them in real-time
- **REST API**: JSON endpoints for orders (`/api/orders/`)
- **Search & filter**: Live client-side search on the order page

---

## What changed recently

**Phase 4 (Persistence)**

The application now supports persistent order storage through a Data Access Layer (DAL):

- **Data Access Layer (`dal.py`)**: abstraction that supports both Firestore (persistent) and in-memory (fallback) storage
- **Firebase Firestore integration**: orders persist across server restarts when configured
- **Graceful fallback**: runs with in-memory storage if Firebase is not configured, so development is never blocked
- **Unchanged API**: all existing endpoints work the same; the storage backend is transparent to the frontend

**Previous features**

- the home, mission, and order pages use shared templates and static assets
- orders are created, viewed, updated, and deleted through JSON endpoints
- the Kanye quote callout now fails gracefully if the quote service is unavailable
- the mission page includes a more structured hotdog-vs-sausage explanation and contact section

## Project structure

```
stackApp/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── README.md
├── hotdogdelivery/
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py
│   ├── dal.py                      # Data Access Layer (Firebase/in-memory)
│   ├── static/hotdogdelivery/
│   │   ├── contactIcon.png
│   │   ├── hotdog.png
│   │   ├── jones.png
│   │   ├── kanye.png
│   │   └── styles.css
│   └── templates/hotdogdelivery/
│       ├── _contact_fragment.html
│       ├── _footer.html
│       ├── _navbar.html
│       ├── base.html
│       ├── home.html
│       ├── mission.html
│       └── order.html
└── stackApp/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

## Requirements

- Python 3.8 or newer
- `pip`

### Python dependencies

Listed in `requirements.txt`:

- `django==6.0.5` — web framework
- `requests>=2.31.0` — API calls (used for Kanye quote service)
- `firebase-admin>=6.0.0` — enables Firestore persistence (optional, but included in requirements)

**Note:** `firebase-admin` is included by default but only used if you configure Firebase credentials. If credentials are not provided, the app falls back to in-memory storage and continues to work normally.

## Features

- **Home page**: landing page with the hotdog brand and a Kanye quote card
- **Mission page**: stacked, vertically flowing content with the hotdog vs sausage story
- **Order page**: order form, live order list, cancellation, and client-side search
- **REST API**: JSON endpoints for managing orders (CRUD: Create, Read, Update, Delete)
- **Persistent or in-memory storage**: 
  - Configure Firebase Firestore for orders that persist across server restarts
  - Or use in-memory storage (orders cleared on restart) for development without setup
- **Graceful degradation**: the app switches to in-memory storage if Firebase is misconfigured, maintaining uptime
- **Quote endpoint**: a lightweight `/api/kanye/` route that returns a quote or fallback text
- **Shared UI**: reusable navbar, footer, and contact fragment templates

## API endpoints

- `GET /api/orders/` — list all orders
- `POST /api/orders/` — create a new order
- `GET /api/orders/<id>/` — view one order
- `PUT /api/orders/<id>/` — update one order
- `DELETE /api/orders/<id>/` — cancel one order
- `GET /api/kanye/` — fetch a Kanye quote

**Persistence behavior:**
- If Firebase Firestore is configured (via `FIREBASE_CREDENTIALS` env var), orders persist in the database.
- If Firebase is not configured, orders are stored in memory and cleared when the server restarts.
- Either way, the API behaves identically; the backend storage is transparent to the client.

## Setup

### Initial installation (Windows PowerShell)

1. Open PowerShell and navigate to the project:

   ```powershell
   cd C:\NEU\Y3\Q3\CSC270-S2\repository\stackApp
   ```

2. Create and activate a virtual environment:

   ```powershell
   # Create virtual environment
   python -m venv .venv
   
   # Activate it (allow script execution for this session)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
   .\.venv\Scripts\Activate.ps1
   ```

   If `python` is not found, install Python 3.8+ from [python.org](https://www.python.org/downloads/windows/) and ensure "Add Python to PATH" is selected.

3. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Verify the installation:

   ```powershell
   py manage.py check
   ```

5. Start the development server:

   ```powershell
   py manage.py runserver
   ```

6. Open the app in your browser:

   ```
   http://127.0.0.1:8000/
   ```

### Running without Firebase (in-memory storage)

If you just want to test the app without setting up Firebase, run the server as above. Orders will be stored in memory and cleared on restart.

```powershell
# Activate venv (if not already active)
.\.venv\Scripts\Activate.ps1

# Run server (uses in-memory fallback)
py manage.py runserver
```

## Configure Firebase Firestore (optional)

Follow these steps to enable persistent order storage using Firebase Firestore. **This is optional** — the app works fine without it (using in-memory storage).

### Step 1: Create a Firebase project

1. Go to [Firebase Console](https://console.firebase.google.com/).
2. Click "Create a project" or select an existing project.
3. Enter a project name (e.g., "Hotdog Delivery App") and click "Continue".
4. Accept the defaults for analytics and click "Create project".
5. Wait for the project to be provisioned, then click "Continue".

### Step 2: Enable Firestore

1. In the Firebase Console, go to **Build > Firestore Database**.
2. Click "Create Database".
3. Choose "Start in test mode" (for development only; use production mode in a real app).
4. Select the closest region and click "Enable".
5. You now have a Firestore database. The DAL will automatically create an `orders` collection with documents as needed.

### Step 3: Create a service account and download credentials

1. In the Firebase Console, go to **Project Settings** (gear icon, top-left).
2. Click the **Service Accounts** tab.
3. Click **Generate New Private Key** (or "Generate a new private key").
4. A JSON file will download automatically (e.g., `hotdog-delivery-key.json`). **Keep this file secure** — it contains credentials.
5. Do not commit this file to version control.

### Step 4: Store the credentials file

Place the downloaded JSON file in a **secure location outside your repo** (not in the project folder):

**Example paths:**
- `C:\Users\<YourUsername>\.credentials\hotdog-firebase-key.json`
- `C:\Users\<YourUsername>\AppData\Local\hotdog-firebase-key.json`
- Any folder you control, as long as only you can read it

**Add to `.gitignore`** to prevent accidental commits:

```gitignore
# Firebase service account (NEVER commit this!)
*-key.json
serviceAccountKey.json
*.json
```

### Step 5: Set the environment variable and run the app

Open PowerShell in the `stackApp` folder and run:

```powershell
# Set the environment variable to point to your credentials file
$env:FIREBASE_CREDENTIALS = 'C:\Users\<YourUsername>\.credentials\hotdog-firebase-key.json'

# Activate the virtual environment
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\.venv\Scripts\Activate.ps1

# Start the server
py manage.py runserver
```

**Replace** `C:\Users\<YourUsername>\.credentials\hotdog-firebase-key.json` with your actual file path.

### Step 6: Verify Firestore is connected

1. After starting the server, create a test order through the UI or API:

   ```powershell
   # In another PowerShell window:
   $body = @{
       customerName = "Test User"
       hotdogName = "Chicago"
       unitPrice = 5.99
       quantity = 2
       notes = "Extra mustard"
   } | ConvertTo-Json
   
   Invoke-WebRequest -Uri "http://localhost:8000/api/orders/" -Method POST -Body $body -ContentType "application/json"
   ```

2. Go to the [Firebase Console > Firestore Database](https://console.firebase.google.com/project/_/firestore/data).
3. You should see a new `orders` collection with a document containing your test order.
4. Restart the server — the order should still be there (because it's in Firestore, not in-memory).

### Step 7 (Optional): Make the env var persistent

To avoid setting the env var every time, use one of these approaches:

**Option A: Set it permanently for your user (Windows)**

```powershell
# This will persist the env var across all new PowerShell sessions
setx FIREBASE_CREDENTIALS "C:\Users\<YourUsername>\.credentials\hotdog-firebase-key.json"

# Close and reopen PowerShell, then just activate the venv and run the server
.\.venv\Scripts\Activate.ps1
py manage.py runserver
```

**Option B: Create a startup script**

Create a file called `run-with-firebase.ps1` in the `stackApp` folder:

```powershell
# run-with-firebase.ps1
$env:FIREBASE_CREDENTIALS = 'C:\Users\<YourUsername>\.credentials\hotdog-firebase-key.json'
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\.venv\Scripts\Activate.ps1
py manage.py runserver
```

Then run:

```powershell
.\run-with-firebase.ps1
```

### Data Access Layer (DAL)

The app uses a **Data Access Layer** (`hotdogdelivery/dal.py`) that abstracts storage:

- **Firestore mode** (when `FIREBASE_CREDENTIALS` is set): orders persist in Firestore's `orders` collection.
- **In-memory mode** (when `FIREBASE_CREDENTIALS` is not set or init fails): orders stored in a Python list, cleared on restart.

The DAL is transparent to the API — routes use the same endpoints either way. The frontend never sees the difference.

### Troubleshooting

**Issue: "firebase_admin not found" or import errors**

- Ensure you activated the virtual environment and ran `pip install -r requirements.txt`.
- Run `pip list` to verify `firebase-admin` is installed.

**Issue: "Order not found" or 404 when calling Firestore with an ID**

- Ensure the `FIREBASE_CREDENTIALS` env var is set correctly before starting the server.
- Verify the credentials file path is absolute (not relative) and readable.
- Check the Firebase Console to see if orders are being written to Firestore.

**Issue: Orders disappear after server restart (using in-memory fallback)**

- This is expected if `FIREBASE_CREDENTIALS` is not configured. Set the env var and restart to enable persistence.

**Issue: Connection refused or "Permission denied" from Firebase**

- Verify the service account has Firestore permissions. In Firebase Console, go to **IAM & Admin > Service Accounts** and ensure the account has the `Editor` role (or at minimum `Cloud Datastore User`).
- Ensure Firestore is enabled in your Firebase project (go to **Build > Firestore Database**).

**Issue: Still seeing in-memory behavior even with env var set**

- Verify the env var is set in your current shell: `echo $env:FIREBASE_CREDENTIALS`
- Verify the file path exists and is readable: `Test-Path "C:\path\to\file.json"`
- Check the server logs for errors related to firebase-admin initialization.

## About the Firebase Credentials File

**File location (in this zipped project):**
```
csc270-stackapp-firebase-adminsdk-fbsvc-f472f3aa80.json
```

This is a **Firebase Admin SDK service account key** that allows the app to connect to a Google Cloud Firestore database for persistent order storage. 

**What it does:**
- Enables the app to store orders in a cloud database instead of just in memory
- Orders created in the app persist even after the server restarts
- The Data Access Layer (`dal.py`) automatically uses it if the `FIREBASE_CREDENTIALS` environment variable points to this file

**How to use it:**
1. Use it as described in the "Using the Included Firebase JSON File" section above
2. Or just run the app without it — in-memory storage (non-persistent) works fine for simple testing

**Security note:**
- This file contains credentials to a Firebase project
- In a real production scenario, you would **never commit this to version control**
- For this submission, it's included for your convenience to test the full persistence feature
- If you want to revoke these credentials later, delete the service account in the [Firebase Console](https://console.firebase.google.com/)

---

## Notes

- The Kanye quote request has a timeout and fallback message so the pages render even if the external API is unavailable.
- Static files are served from `hotdogdelivery/static/hotdogdelivery/` during development.
- **Security**: never commit the Firebase credentials JSON to version control. Use `.gitignore` and environment variables only.

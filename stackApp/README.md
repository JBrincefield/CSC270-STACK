# Hotdog Delivery Application

Hotdog Delivery is a Django 6 app with Firebase Authentication, Django session management, Firestore storage, and owner-scoped order access. When a user signs in, they only see and edit their own orders unless their Firebase account has the `admin` custom claim.

## Fastest Start: Firebase Auth Mode

Use this if you want the app running in the intended full-auth mode from the start.

1. Open PowerShell in the repo root: `cd CSC270-STACK`
2. Paste this whole block and replace the placeholder Firebase values with your own Web App config from Firebase Console:

```powershell
Set-Location stackApp

@'
FIREBASE_CREDENTIALS=csc270-stackapp-firebase-adminsdk-fbsvc-f472f3aa80.json
FIREBASE_WEB_API_KEY=IzaSyCpqDmP4pWuPnT16n5MAg-LusP0wkqxcxA
FIREBASE_AUTH_DOMAIN=csc270-stackapp.firebaseapp.com
FIREBASE_PROJECT_ID=csc270-stackapp
FIREBASE_STORAGE_BUCKET=csc270-stackapp.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=84724347125
FIREBASE_APP_ID=1:84724347125:web:76094dfe6ccedc3e6a95bc
'@ | Set-Content .env -NoNewline

python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
py manage.py runserver
```

3. Open the app at `http://127.0.0.1:8000/`
4. Use the `Auth` page to register or sign in with Firebase Email/Password.
5. If you want one account to see everything, set that user’s Firebase custom claim to `admin`.

## Where the Firebase values come from

In Firebase Console:

1. Open your project.
2. Go to Project settings.
3. In the General tab, add a Web app if you do not already have one.
4. Copy the Web app config Firebase shows you.
5. Put those values into `.env` using these names:

- `apiKey` -> `FIREBASE_WEB_API_KEY`
- `authDomain` -> `FIREBASE_AUTH_DOMAIN`
- `projectId` -> `FIREBASE_PROJECT_ID`
- `storageBucket` -> `FIREBASE_STORAGE_BUCKET`
- `messagingSenderId` -> `FIREBASE_MESSAGING_SENDER_ID`
- `appId` -> `FIREBASE_APP_ID`

The `.env` file is local only and ignored by git.

## What the app does

- Firebase Email/Password handles registration, login, and logout.
- Django stores the session after Firebase verifies the ID token.
- Normal users can only see and edit their own orders.
- Admin users can see every order and update order status.
- Orders support likes and messages as simple user interactions.

## Admin Role

Grant or remove the admin claim with:

```powershell
cd stackApp
py manage.py set_admin_role <firebase-uid>
py manage.py set_admin_role <firebase-uid> --remove
```

## If you just want the app running without auth

The project still supports a non-auth fallback for development, but the main path is Firebase Auth mode. If you follow the quick start above, you are using the intended full project setup.

## Project Layout

```text
stackApp/
├── manage.py
├── requirements.txt
├── .env
├── hotdogdelivery/
│   ├── auth_utils.py
│   ├── dal.py
│   ├── views.py
│   ├── templates/
│   └── static/
└── stackApp/
    └── settings.py
```

## API Endpoints

- `GET /api/orders/` - list the signed-in user’s orders
- `POST /api/orders/` - create a new order for the signed-in user
- `GET /api/orders/<id>/` - view one visible order
- `PUT /api/orders/<id>/` - update one visible order
- `DELETE /api/orders/<id>/` - delete one visible order
- `POST /api/orders/<id>/like/` - toggle a like on one visible order
- `POST /api/orders/<id>/messages/` - add a message to one visible order
- `GET /api/kanye/` - returns a Kanye quote or fallback

## Troubleshooting

- If the app says it cannot find `firebase_admin`, rerun `pip install -r requirements.txt` inside the virtual environment.
- If Firebase login does not work, confirm the `.env` file exists in `stackApp/` and the Firebase Web App values are correct.
- If the app cannot reach Firestore, verify `FIREBASE_CREDENTIALS` points to the included service account JSON file.

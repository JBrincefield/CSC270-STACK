# Hotdog Delivery Application

A Django-based web application for ordering hotdogs and learning about the differences between hotdogs and sausages.

## Project Structure

```
stackApp/
├── db.sqlite3                 # SQLite database
├── manage.py                  # Django management script
├── hotdogdelivery/           # Main application
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py              # View logic
│   ├── static/
│   │   └── hotdogdelivery/
│   │       └── styles.css    # Application styles
│   └── templates/
│       └── hotdogdelivery/
│           ├── contact.html
│           ├── home.html
│           └── hotdogs_vs_sausages.html
└── stackApp/                 # Project configuration
    ├── __init__.py
    ├── asgi.py               # ASGI configuration
    ├── settings.py           # Django settings
    ├── urls.py               # URL routing
    └── wsgi.py               # WSGI configuration
```

## Prerequisites

- Python 3.8+
- Django 3.2+
- pip (Python package manager)

## Setup Instructions

1. **Clone or download the project**

   ```bash
   cd stackApp
   ```

2. **Install dependencies**

   ```bash
   pip install django
   ```

3. **Run migrations** (if needed)

   ```bash
   python manage.py migrate
   ```

4. **Start the development server**

   ```bash
   python manage.py runserver
   ```

5. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:8000/`

## Features

- **Home Page**: Main landing page for the application
- **Contact**: Contact information and messaging
- **Hotdogs vs Sausages**: Educational content about the differences between hotdogs and sausages
- **Responsive Design**: CSS styling for a better user experience

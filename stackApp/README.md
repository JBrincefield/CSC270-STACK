# Hotdog Delivery Application

A Django-based web application for ordering hotdogs and learning about the differences between hotdogs and sausages.

## Project Structure

```
stackApp/
├── manage.py                  # Django management script
├── hotdogdelivery/            # Main application
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py               # View logic and API handlers
│   ├── static/
│   │   └── hotdogdelivery/
│   │       ├── hotdog.png
│   │       ├── jones.png
│   │       ├── kanye.png
│   │       └── styles.css
│   └── templates/
│       └── hotdogdelivery/
│           ├── _contact_fragment.html
│           ├── _footer.html
│           ├── _navbar.html
│           ├── base.html
│           ├── home.html
│           ├── mission.html
│           └── order.html
└── stackApp/                  # Project configuration
    ├── __init__.py
    ├── asgi.py                # ASGI configuration
    ├── settings.py            # Django settings
    ├── urls.py                # URL routing
    └── wsgi.py                # WSGI configuration
```

## Prerequisites

- Python 3.8+
- Django 3.2+
- pip (Python package manager)

## REST API Overview

This project uses an in-memory REST API for hotdog orders. It does **not** persist order data to a database.

- `GET /api/orders/` — list all orders
- `POST /api/orders/` — create a new purchase/order
- `GET /api/orders/<id>/` — view a single order
- `PUT /api/orders/<id>/` — update an order
- `DELETE /api/orders/<id>/` — cancel an order

## Setup Instructions

1. **Clone or download the project**

   ```bash
   cd stackApp
   ```

2. **Install dependencies**

   ```bash
   pip install django
   ```

3. **Run a quick project check**

   ```bash
   py manage.py check
   ```

4. **Start the development server**

   ```bash
   python manage.py runserver
   ```

5. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:8000/`

> Note: The hotdog order API keeps data in memory only. Restarting the server clears all orders.

## Features

- **Home Page**: Main landing page with the Kanye quote callout
- **Mission Page**: Vertical, centered content with the hotdog vs sausage explanation
- **Order Page**: Mascot-themed hotdog checkout with live in-memory purchases
- **Reusable Components**: Shared navbar, footer, and contact fragment templates
- **Responsive Design**: CSS styling for a better user experience

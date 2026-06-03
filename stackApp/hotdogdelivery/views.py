"""HTTP views for the Hotdog Delivery app.

This module contains simple Django views and a tiny API used by the
frontend. It delegates persistence to the data access layer in
`hotdogdelivery.dal` and keeps the presentation logic lightweight.

Where external services are used (e.g. the Kanye REST API) this module
handles errors gracefully to avoid degrading the user experience.

Authentication is handled via Firebase Auth (Google Sign-In). The frontend
obtains a Firebase ID token and POSTs it to /api/auth/verify/, where the
server verifies it with the Firebase Admin SDK and stores the user info in
a Django session. All order endpoints then require a valid session.
"""

from django.shortcuts import render, redirect
import requests
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
import logging

# Data access layer (can use Firebase/Firestore or fall back to in-memory)
from . import dal

# Initialize the DAL (will fall back to in-memory if Firebase isn't configured)
dal.init_app()

# Module logger
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _get_current_user(request):
    """Return the authenticated user dict from the session, or None."""
    uid = request.session.get('user_uid')
    if not uid:
        return None
    return {
        'uid': uid,
        'email': request.session.get('user_email', ''),
        'name': request.session.get('user_name', ''),
        'is_admin': request.session.get('is_admin', False),
    }


@csrf_exempt
def verify_token(request):
    """POST: Verify a Firebase ID token and establish a Django session."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken', '').strip()
        if not id_token:
            return JsonResponse({'error': 'ID token required'}, status=400)

        from django.conf import settings as _settings
        api_key = _settings.FIREBASE_WEB_CONFIG.get('apiKey', '')
        if not api_key:
            return JsonResponse({'error': 'Firebase not configured on server'}, status=503)

        # Verify the token via Firebase REST API — no Admin SDK credentials required
        lookup = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}',
            json={'idToken': id_token},
            timeout=10,
        )
        if not lookup.ok:
            logger.warning('Firebase token lookup failed: %s', lookup.text)
            return JsonResponse({'error': 'Authentication failed'}, status=401)

        users = lookup.json().get('users', [])
        if not users:
            return JsonResponse({'error': 'Authentication failed'}, status=401)

        user_info = users[0]
        uid = user_info.get('localId', '')
        email = user_info.get('email', '')
        name = user_info.get('displayName', '') or email

        admin_status = dal.is_admin(uid)

        request.session['user_uid'] = uid
        request.session['user_email'] = email
        request.session['user_name'] = name
        request.session['is_admin'] = admin_status
        request.session.modified = True

        return JsonResponse({'success': True, 'isAdmin': admin_status, 'name': name})
    except requests.exceptions.Timeout:
        logger.warning('Firebase token lookup timed out')
        return JsonResponse({'error': 'Token verification timed out — please try again'}, status=504)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as exc:
        logger.exception('Token verification failed: %s', exc)
        return JsonResponse({'error': 'Authentication failed'}, status=401)


@csrf_exempt
def logout_view(request):
    """POST: Clear the Django session (sign the user out server-side)."""
    request.session.flush()
    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_kanye_quote():
    """Fetch a Kanye quote and degrade gracefully when the API is unavailable."""
    try:
        response = requests.get('https://api.kanye.rest', timeout=5)
        response.raise_for_status()
        return response.json().get('quote') or "Kanye's wisdom is currently unavailable"
    except (requests.exceptions.RequestException, ValueError, KeyError) as exc:
        logger.exception('Failed to fetch Kanye quote: %s', exc)
        return "Kanye's wisdom is currently unavailable"


def _kanye_quote_context():
    return {'kanye_quote': fetch_kanye_quote()}


def _order_summary(order):
    total = round(order['unitPrice'] * order['quantity'], 2)
    return {
        'id': order['id'],
        'userId': order.get('userId', ''),
        'customerName': order['customerName'],
        'hotdogName': order['hotdogName'],
        'quantity': order['quantity'],
        'unitPrice': order['unitPrice'],
        'totalPrice': total,
        'notes': order['notes'],
        'status': order['status'],
    }


# ---------------------------------------------------------------------------
# Page views
# ---------------------------------------------------------------------------

def our_mission(request):
    return render(request, 'hotdogdelivery/mission.html', _kanye_quote_context())


def login_page(request):
    """Show the sign-in / create-account page. Redirects away if already authenticated."""
    if _get_current_user(request):
        next_url = request.GET.get('next', '/order/')
        return redirect(next_url)
    return render(request, 'hotdogdelivery/login.html', {
        'next': request.GET.get('next', '/order/'),
    })


def order(request):
    """Render the order page. Requires authentication — redirects to login otherwise."""
    user = _get_current_user(request)
    if not user:
        return redirect(f'/login/?next=/order/')

    if user['is_admin']:
        orders = dal.get_all_orders()
    else:
        orders = dal.get_orders_by_user(user['uid'])

    context = _kanye_quote_context()
    context['orders'] = [_order_summary(o) for o in orders]
    return render(request, 'hotdogdelivery/order.html', context)


def home(request):
    user = _get_current_user(request)
    context = _kanye_quote_context()

    completed = dal.get_completed_orders()
    completed_with_reviews = []
    for o in completed:
        reviews = dal.get_reviews_for_order(o['id'])
        likes = sum(1 for r in reviews if r['reaction'] == 'like')
        dislikes = sum(1 for r in reviews if r['reaction'] == 'dislike')
        user_reaction = dal.get_user_review(o['id'], user['uid']) if user else None
        entry = _order_summary(o)
        entry['likes'] = likes
        entry['dislikes'] = dislikes
        entry['userReaction'] = user_reaction
        completed_with_reviews.append(entry)
    context['completed_orders'] = completed_with_reviews

    if user:
        context['user_orders'] = [_order_summary(o) for o in dal.get_orders_by_user(user['uid'])]

    return render(request, 'hotdogdelivery/home.html', context)


# ---------------------------------------------------------------------------
# Order API endpoints
# ---------------------------------------------------------------------------

@csrf_exempt
def api_orders_list(request):
    """GET: list orders for current user (all for admins).
    POST: create a new order owned by the current user.
    Both require an authenticated session.
    """
    user = _get_current_user(request)

    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Customer name always comes from the authenticated session, not the request body
            customer_name = user['name'] or user['email']
            hotdog_name = data.get('hotdogName', '').strip()
            unit_price = data.get('unitPrice')
            quantity = data.get('quantity', 1)
            notes = data.get('notes', '').strip()

            if not customer_name:
                return JsonResponse({'error': 'Customer name is required'}, status=400)
            if not hotdog_name:
                return JsonResponse({'error': 'Hotdog selection is required'}, status=400)

            try:
                quantity_int = int(quantity)
                if quantity_int < 1:
                    return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Quantity must be a valid whole number'}, status=400)

            try:
                price_float = float(unit_price)
                if price_float < 0:
                    return JsonResponse({'error': 'Unit price must be positive'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Unit price must be a valid number'}, status=400)

            order_payload = {
                'userId': user['uid'],
                'customerName': customer_name,
                'hotdogName': hotdog_name,
                'unitPrice': price_float,
                'quantity': quantity_int,
                'notes': notes,
                'status': 'pending',
            }

            created = dal.create_order(order_payload)
            return JsonResponse(_order_summary(created), status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # GET — return orders visible to this user
    if user['is_admin']:
        orders = dal.get_all_orders()
    else:
        orders = dal.get_orders_by_user(user['uid'])

    return JsonResponse({'orders': [_order_summary(o) for o in orders]})


@csrf_exempt
def api_order_detail(request, order_id):
    """GET / PUT / DELETE a specific order.

    Ownership rules:
    - Regular users may only access their own orders.
    - Admins may access any order.
    - Regular users may not change the `status` field.
    """
    user = _get_current_user(request)
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    order = dal.get_order_by_id(order_id)
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    # Ownership check — admins bypass this
    if not user['is_admin'] and order.get('userId') != user['uid']:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        return JsonResponse(_order_summary(order))

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            updates = {}

            if 'customerName' in data:
                if not user['is_admin']:
                    return JsonResponse({'error': 'Only admins can change the customer name'}, status=403)
                val = data['customerName'].strip()
                if not val:
                    return JsonResponse({'error': 'Customer name cannot be empty'}, status=400)
                updates['customerName'] = val

            if 'hotdogName' in data:
                val = data['hotdogName'].strip()
                if not val:
                    return JsonResponse({'error': 'Hotdog name cannot be empty'}, status=400)
                updates['hotdogName'] = val

            if 'notes' in data:
                updates['notes'] = data['notes'].strip()

            if 'quantity' in data:
                try:
                    q = int(data['quantity'])
                    if q < 1:
                        return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
                    updates['quantity'] = q
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Quantity must be a valid whole number'}, status=400)

            if 'unitPrice' in data:
                try:
                    p = float(data['unitPrice'])
                    if p < 0:
                        return JsonResponse({'error': 'Unit price must be positive'}, status=400)
                    updates['unitPrice'] = p
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Unit price must be a valid number'}, status=400)

            if 'status' in data:
                if not user['is_admin']:
                    return JsonResponse({'error': 'Only admins can change order status'}, status=403)
                updates['status'] = data['status']

            updated = dal.update_order(order_id, updates)
            if not updated:
                return JsonResponse({'error': 'Order not found'}, status=404)
            return JsonResponse(_order_summary(updated))
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid request'}, status=400)

    elif request.method == 'DELETE':
        success = dal.delete_order(order_id)
        if success:
            return JsonResponse({'message': 'Order cancelled'}, status=200)
        return JsonResponse({'error': 'Order not found'}, status=404)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_kanye_quote(request):
    """A tiny API endpoint returning a Kanye quote (used by the frontend)."""
    return JsonResponse({'quote': fetch_kanye_quote()})


@csrf_exempt
def api_order_review(request, order_id):
    """POST: Submit or update a like/dislike on a completed order."""
    user = _get_current_user(request)
    if not user:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    order = dal.get_order_by_id(order_id)
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    if order.get('status') != 'completed':
        return JsonResponse({'error': 'Only completed orders can be reviewed'}, status=400)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        reaction = data.get('reaction', '').strip().lower()
        if reaction not in ('like', 'dislike'):
            return JsonResponse({'error': 'Reaction must be "like" or "dislike"'}, status=400)
        dal.upsert_review(order_id, user['uid'], reaction)
        reviews = dal.get_reviews_for_order(order_id)
        likes = sum(1 for r in reviews if r['reaction'] == 'like')
        dislikes = sum(1 for r in reviews if r['reaction'] == 'dislike')
        return JsonResponse({'likes': likes, 'dislikes': dislikes, 'userReaction': reaction})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

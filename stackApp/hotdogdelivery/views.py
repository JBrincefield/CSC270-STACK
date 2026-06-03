"""HTTP views for the Hotdog Delivery app.

This module contains the public pages plus the JSON API used by the
frontend. Firebase Authentication is used for membership, and the Django
session stores the signed-in user so the rest of the app can enforce
ownership and role-based access.
"""

from __future__ import annotations

import json
import logging

import requests
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from . import auth_utils
from . import dal


dal.init_app()

logger = logging.getLogger(__name__)


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


def _viewer(request):
    return auth_utils.get_session_user(request)


def _viewer_response(request):
    viewer = _viewer(request)
    if viewer:
        return viewer, None
    return None, JsonResponse({'error': 'Authentication required'}, status=401)


def _order_summary(order, viewer=None):
    total = round(order['unitPrice'] * order['quantity'], 2)
    viewer_uid = viewer.get('uid') if viewer else None
    is_owner = bool(viewer_uid and order.get('ownerUid') == viewer_uid)
    can_edit = bool(viewer and (viewer.get('isAdmin') or is_owner))
    messages = list(order.get('messages', []))
    liked_by = list(order.get('likedBy', []))

    return {
        'id': order['id'],
        'customerName': order.get('customerName', ''),
        'ownerUid': order.get('ownerUid', ''),
        'ownerEmail': order.get('ownerEmail', ''),
        'ownerDisplayName': order.get('ownerDisplayName', order.get('customerName', '')),
        'hotdogName': order.get('hotdogName', ''),
        'quantity': order.get('quantity', 1),
        'unitPrice': order.get('unitPrice', 0.0),
        'totalPrice': total,
        'notes': order.get('notes', ''),
        'status': order.get('status', 'pending'),
        'likes': int(order.get('likes', len(liked_by))),
        'likedBy': liked_by,
        'messages': messages,
        'messageCount': len(messages),
        'isOwner': is_owner,
        'canEdit': can_edit,
        'canMessage': bool(viewer),
        'likedByMe': bool(viewer_uid and viewer_uid in liked_by),
    }


def _orders_for_viewer(viewer):
    return dal.get_orders_for_user(viewer['uid'], include_all=viewer.get('isAdmin', False))


def _order_context(request):
    viewer = _viewer(request)
    if not viewer:
        return {'orders': []}

    orders = _orders_for_viewer(viewer)
    return {
        'orders': [_order_summary(order, viewer) for order in orders],
        'viewer_uid': viewer['uid'],
        'viewer_is_admin': viewer.get('isAdmin', False),
        'viewer_label': auth_utils.user_label(viewer),
    }


def our_mission(request):
    return render(request, 'hotdogdelivery/mission.html', _kanye_quote_context())


def order(request):
    viewer = _viewer(request)
    if not viewer:
        next_path = request.get_full_path()
        return redirect(f"{reverse('auth_page')}?next={next_path}")

    context = _order_context(request)
    context.update(_kanye_quote_context())
    return render(request, 'hotdogdelivery/order.html', context)


def home(request):
    return render(request, 'hotdogdelivery/home.html', _kanye_quote_context())


def auth_page(request):
    if _viewer(request):
        return redirect('order')

    return render(
        request,
        'hotdogdelivery/auth.html',
        {
            'next_url': request.GET.get('next') or reverse('order'),
        },
    )


@csrf_exempt
def auth_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    token = payload.get('idToken', '')
    if not token:
        return JsonResponse({'error': 'Missing Firebase token'}, status=400)

    try:
        decoded = auth_utils.verify_id_token(token)
        user = auth_utils.set_session_user(request, decoded)
        return JsonResponse({'user': user})
    except Exception as exc:
        logger.exception('Failed to establish Firebase session: %s', exc)
        return JsonResponse({'error': 'Unable to sign in'}, status=401)


def auth_logout(request):
    auth_utils.clear_session_user(request)
    next_url = request.POST.get('next') or reverse('home')
    return redirect(next_url)


@csrf_exempt
def api_orders_list(request):
    """GET: List the current user's orders, POST: Create a new hotdog purchase."""
    viewer, error_response = _viewer_response(request)
    if error_response:
        return error_response

    if request.method == 'POST':
        try:
            data = json.loads(request.body or '{}')
            hotdog_name = data.get('hotdogName', '').strip()
            unit_price = data.get('unitPrice')
            quantity = data.get('quantity', 1)
            notes = data.get('notes', '').strip()

            if not hotdog_name:
                return JsonResponse({'error': 'Hotdog selection is required'}, status=400)

            try:
                quantity_int = int(quantity)
                if quantity_int < 1:
                    return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'Quantity must be a valid whole number'}, status=400)

            try:
                price_float = float(unit_price)
                if price_float < 0:
                    return JsonResponse({'error': 'Unit price must be positive'}, status=400)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'Unit price must be a valid number'}, status=400)

            order_payload = {
                'customerName': auth_utils.user_label(viewer),
                'ownerUid': viewer['uid'],
                'ownerEmail': viewer.get('email', ''),
                'ownerDisplayName': viewer.get('displayName', ''),
                'hotdogName': hotdog_name,
                'unitPrice': price_float,
                'quantity': quantity_int,
                'notes': notes,
                'status': 'pending',
                'likes': 0,
                'likedBy': [],
                'messages': [],
            }

            created = dal.create_order(order_payload)
            return JsonResponse(_order_summary(created, viewer), status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    orders = _orders_for_viewer(viewer)
    return JsonResponse({'orders': [_order_summary(order, viewer) for order in orders]})


@csrf_exempt
def api_order_detail(request, order_id):
    """GET/UPDATE/DELETE a specific order."""
    viewer, error_response = _viewer_response(request)
    if error_response:
        return error_response

    order = dal.get_order_by_id(order_id)
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    can_edit = viewer.get('isAdmin') or order.get('ownerUid') == viewer['uid']
    if not can_edit:
        return JsonResponse({'error': 'Order not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(_order_summary(order, viewer))

    if request.method == 'PUT':
        try:
            data = json.loads(request.body or '{}')
            updates = {}

            if 'hotdogName' in data:
                updates['hotdogName'] = data.get('hotdogName', order['hotdogName']).strip()
            if 'notes' in data:
                updates['notes'] = data.get('notes', order['notes']).strip()
            if 'quantity' in data:
                quantity_int = int(data['quantity'])
                if quantity_int < 1:
                    return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
                updates['quantity'] = quantity_int
            if 'unitPrice' in data:
                price_float = float(data['unitPrice'])
                if price_float < 0:
                    return JsonResponse({'error': 'Unit price must be positive'}, status=400)
                updates['unitPrice'] = price_float
            if 'status' in data:
                if not viewer.get('isAdmin'):
                    return JsonResponse({'error': 'Only admins can change order status'}, status=403)
                updates['status'] = data['status']

            updated = dal.update_order(order_id, updates)
            if not updated:
                return JsonResponse({'error': 'Order not found'}, status=404)
            return JsonResponse(_order_summary(updated, viewer))
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid request'}, status=400)

    if request.method == 'DELETE':
        if not viewer.get('isAdmin') and order.get('ownerUid') != viewer['uid']:
            return JsonResponse({'error': 'Order not found'}, status=404)
        if dal.delete_order(order_id):
            return JsonResponse({'message': 'Order cancelled'}, status=200)
        return JsonResponse({'error': 'Order not found'}, status=404)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_order_like(request, order_id):
    viewer, error_response = _viewer_response(request)
    if error_response:
        return error_response

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    order = dal.get_order_by_id(order_id)
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    if not viewer.get('isAdmin') and order.get('ownerUid') != viewer['uid']:
        return JsonResponse({'error': 'Order not found'}, status=404)

    updated = dal.toggle_order_like(order_id, viewer)
    return JsonResponse(_order_summary(updated, viewer))


@csrf_exempt
def api_order_messages(request, order_id):
    viewer, error_response = _viewer_response(request)
    if error_response:
        return error_response

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    order = dal.get_order_by_id(order_id)
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    if not viewer.get('isAdmin') and order.get('ownerUid') != viewer['uid']:
        return JsonResponse({'error': 'Order not found'}, status=404)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    message = (payload.get('message') or '').strip()
    if not message:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    updated = dal.add_order_message(order_id, viewer, message)
    return JsonResponse(_order_summary(updated, viewer), status=201)


def get_kanye_quote(request):
    """A tiny API endpoint returning a Kanye quote (used by the frontend)."""
    return JsonResponse({'quote': fetch_kanye_quote()})

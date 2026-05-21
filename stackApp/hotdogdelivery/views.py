from django.shortcuts import render
import requests
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

# In-memory storage for orders (no database)
orders_store = []
order_id_counter = [1]  # Using list to make it mutable in nested functions


def fetch_kanye_quote():
    """Fetch a Kanye quote and degrade gracefully when the API is unavailable."""
    try:
        response = requests.get('https://api.kanye.rest', timeout=5)
        response.raise_for_status()
        return response.json().get('quote') or "Kanye's wisdom is currently unavailable"
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return "Kanye's wisdom is currently unavailable"


def _kanye_quote_context():
    return {'kanye_quote': fetch_kanye_quote()}


def _order_summary(order):
    total = round(order['unitPrice'] * order['quantity'], 2)
    return {
        'id': order['id'],
        'customerName': order['customerName'],
        'hotdogName': order['hotdogName'],
        'quantity': order['quantity'],
        'unitPrice': order['unitPrice'],
        'totalPrice': total,
        'notes': order['notes'],
        'status': order['status'],
    }


def _order_context():
    return {'orders': [_order_summary(order) for order in orders_store]}

def our_mission(request):
    """Render the About / Our Mission page (keeps the hotdog vs sausage comparison).

    We preserve the Kanye quote call but degrade gracefully if the API is unavailable.
    """
    return render(request, 'hotdogdelivery/mission.html', _kanye_quote_context())


def order(request):
    context = _order_context()
    context.update(_kanye_quote_context())
    return render(request, 'hotdogdelivery/order.html', context)

def home(request):
    return render(request, 'hotdogdelivery/home.html', _kanye_quote_context())


@csrf_exempt
def api_orders_list(request):
    """GET: List all hotdog orders, POST: Create a new hotdog purchase."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name = data.get('customerName', '').strip()
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

            order = {
                'id': order_id_counter[0],
                'customerName': customer_name,
                'hotdogName': hotdog_name,
                'unitPrice': price_float,
                'quantity': quantity_int,
                'notes': notes,
                'status': 'pending'
            }
            order_id_counter[0] += 1
            orders_store.append(order)

            return JsonResponse(_order_summary(order), status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # GET: Return all orders
    return JsonResponse({'orders': [_order_summary(order) for order in orders_store]})


@csrf_exempt
def api_order_detail(request, order_id):
    """GET/UPDATE/DELETE a specific order."""
    order = next((item for item in orders_store if item['id'] == order_id), None)

    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(_order_summary(order))

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            if 'customerName' in data:
                order['customerName'] = data.get('customerName', order['customerName']).strip()
            if 'hotdogName' in data:
                order['hotdogName'] = data.get('hotdogName', order['hotdogName']).strip()
            if 'notes' in data:
                order['notes'] = data.get('notes', order['notes']).strip()
            if 'quantity' in data:
                quantity_int = int(data['quantity'])
                if quantity_int < 1:
                    return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
                order['quantity'] = quantity_int
            if 'unitPrice' in data:
                price_float = float(data['unitPrice'])
                if price_float < 0:
                    return JsonResponse({'error': 'Unit price must be positive'}, status=400)
                order['unitPrice'] = price_float
            if 'status' in data:
                order['status'] = data['status']

            return JsonResponse(_order_summary(order))
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid request'}, status=400)

    elif request.method == 'DELETE':
        orders_store.remove(order)
        return JsonResponse({'message': 'Order cancelled'}, status=200)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_kanye_quote(request):
    return JsonResponse({'quote': fetch_kanye_quote()})

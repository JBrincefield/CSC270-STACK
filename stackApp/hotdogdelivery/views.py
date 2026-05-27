from django.shortcuts import render
import requests
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

# Data access layer (can use Firebase/Firestore or fall back to in-memory)
from . import dal

# Initialize the DAL (will fall back to in-memory if Firebase isn't configured)
dal.init_app()


# fetches random kanye quote
def fetch_kanye_quote():
    """Fetch a Kanye quote and degrade gracefully when the API is unavailable."""
    try:
        response = requests.get('https://api.kanye.rest', timeout=5)
        response.raise_for_status()
        return response.json().get('quote') or "Kanye's wisdom is currently unavailable"
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return "Kanye's wisdom is currently unavailable"

#creates dictionary with kanye quote for later use
def _kanye_quote_context():
    return {'kanye_quote': fetch_kanye_quote()}


# formats and summarizes a single order
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

#used to pass order data into the template
def _order_context():
    return {'orders': [_order_summary(order) for order in dal.get_all_orders()]}

def our_mission(request):
    """Render the About / Our Mission page (keeps the hotdog vs sausage comparison).

    We preserve the Kanye quote call but degrade gracefully if the API is unavailable.
    """
    return render(request, 'hotdogdelivery/mission.html', _kanye_quote_context())

#runders the order.html and passes both orders and kanye quotes to the frontend
def order(request):
    context = _order_context()
    context.update(_kanye_quote_context())
    return render(request, 'hotdogdelivery/order.html', context)

def home(request):
    return render(request, 'hotdogdelivery/home.html', _kanye_quote_context())


#GET: retrieves all information from order_store
#POST: Extracts data from incoming order and validates it, gives it an ID, 
# and sets a status before appending it to orders_store
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

            order_payload = {
                'customerName': customer_name,
                'hotdogName': hotdog_name,
                'unitPrice': price_float,
                'quantity': quantity_int,
                'notes': notes,
                'status': 'pending'
            }

            created = dal.create_order(order_payload)
            return JsonResponse(_order_summary(created), status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # GET: Return all orders
    return JsonResponse({'orders': [_order_summary(order) for order in dal.get_all_orders()]})


#GET: Finds order by ID in orders_store, returns formatted orders
#PUT: Finds order by ID, updates any information, and returns updated formatted order
#DELETE: deletes the order
@csrf_exempt
def api_order_detail(request, order_id):
    """GET/UPDATE/DELETE a specific order."""
    order = dal.get_order_by_id(order_id)

    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    # Get Functionality
    if request.method == 'GET':
        return JsonResponse(_order_summary(order))

    # put functionality
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            updates = {}
            if 'customerName' in data:
                updates['customerName'] = data.get('customerName', order['customerName']).strip()
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
                updates['status'] = data['status']

            updated = dal.update_order(order_id, updates)
            if not updated:
                return JsonResponse({'error': 'Order not found'}, status=404)
            return JsonResponse(_order_summary(updated))
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid request'}, status=400)

    # delete functionality
    elif request.method == 'DELETE':
        success = dal.delete_order(order_id)
        if success:
            return JsonResponse({'message': 'Order cancelled'}, status=200)
        return JsonResponse({'error': 'Order not found'}, status=404)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_kanye_quote(request):
    return JsonResponse({'quote': fetch_kanye_quote()})

from django.shortcuts import render
import requests
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

# In-memory storage for hotdogs (no database)
hotdogs_store = []
hotdog_id_counter = [1]  # Using list to make it mutable in nested functions


def fetch_kanye_quote():
    """Fetch a Kanye quote and degrade gracefully when the API is unavailable."""
    try:
        response = requests.get('https://api.kanye.rest', timeout=5)
        response.raise_for_status()
        return response.json().get('quote') or "Kanye's wisdom is currently unavailable"
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return "Kanye's wisdom is currently unavailable"

def our_mission(request):
    """Render the About / Our Mission page (keeps the hotdog vs sausage comparison).

    We preserve the Kanye quote call but degrade gracefully if the API is unavailable.
    """
    context = {'kanye_quote': fetch_kanye_quote()}
    return render(request, 'hotdogdelivery/mission.html', context)


def order(request):
    return render(request, 'hotdogdelivery/order.html')

def home(request):
    return render(request, 'hotdogdelivery/home.html', {'kanye_quote': fetch_kanye_quote()})

def contact(request):
    return render(request, 'hotdogdelivery/contact.html')


# ==================== Hotdog CRUD API ====================

def create_hotdog_page(request):
    """Render the create hotdog page with all existing hotdogs."""
    context = {'hotdogs': hotdogs_store}
    return render(request, 'hotdogdelivery/create_hotdog.html', context)


@csrf_exempt
def api_hotdogs_list(request):
    """GET: List all hotdogs, POST: Create a new hotdog."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            hotdog_name = data.get('hotdogName', '').strip()
            hotdog_price = data.get('hotdogPrice')
            description = data.get('description', '').strip()
            
            # Validation
            if not hotdog_name:
                return JsonResponse({'error': 'Hotdog name is required'}, status=400)
            
            try:
                price_float = float(hotdog_price)
                if price_float < 0:
                    return JsonResponse({'error': 'Price must be positive'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Price must be a valid number'}, status=400)
            
            # Create hotdog
            hotdog = {
                'id': hotdog_id_counter[0],
                'hotdogName': hotdog_name,
                'hotdogPrice': price_float,
                'description': description
            }
            hotdog_id_counter[0] += 1
            hotdogs_store.append(hotdog)
            
            return JsonResponse(hotdog, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # GET: Return all hotdogs
    return JsonResponse({'hotdogs': hotdogs_store})


@csrf_exempt
def api_hotdog_detail(request, hotdog_id):
    """GET/UPDATE/DELETE a specific hotdog."""
    hotdog = next((h for h in hotdogs_store if h['id'] == hotdog_id), None)
    
    if not hotdog:
        return JsonResponse({'error': 'Hotdog not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse(hotdog)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            hotdog['hotdogName'] = data.get('hotdogName', hotdog['hotdogName']).strip()
            hotdog['description'] = data.get('description', hotdog['description']).strip()
            
            if 'hotdogPrice' in data:
                price_float = float(data['hotdogPrice'])
                if price_float < 0:
                    return JsonResponse({'error': 'Price must be positive'}, status=400)
                hotdog['hotdogPrice'] = price_float
            
            return JsonResponse(hotdog)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid request'}, status=400)
    
    elif request.method == 'DELETE':
        hotdogs_store.remove(hotdog)
        return JsonResponse({'message': 'Hotdog deleted'}, status=200)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_kanye_quote(request):
    try:
        response = requests.get('https://api.kanye.rest')
        data = response.json()
        return JsonResponse(data)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

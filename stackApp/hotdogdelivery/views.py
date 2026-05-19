from django.shortcuts import render
import requests
from django.http import JsonResponse


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


# def hotdogs_vs_sausages(request):
#     # legacy route kept for compatibility — render mission page
#     return our_mission(request)


def order(request):
    return render(request, 'hotdogdelivery/order.html')

def home(request):
    return render(request, 'hotdogdelivery/home.html', {'kanye_quote': fetch_kanye_quote()})

def contact(request):
    return render(request, 'hotdogdelivery/contact.html')


def get_kanye_quote(request):
    try:
        response = requests.get('https://api.kanye.rest')
        data = response.json()
        return JsonResponse(data)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

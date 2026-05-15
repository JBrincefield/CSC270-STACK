from django.shortcuts import render
import requests
from django.http import JsonResponse

def our_mission(request):
    """Render the About / Our Mission page (keeps the hotdog vs sausage comparison).

    We preserve the Kanye quote call but degrade gracefully if the API is unavailable.
    """
    kanye_quote = None
    try:
        response = requests.get('https://api.kanye.rest')
        kanye_quote = response.json().get('quote')
    except requests.exceptions.RequestException:
        kanye_quote = "Kanye's wisdom is currently unavailable"

    context = {'kanye_quote': kanye_quote}
    return render(request, 'hotdogdelivery/mission.html', context)


# def hotdogs_vs_sausages(request):
#     # legacy route kept for compatibility — render mission page
#     return our_mission(request)


def order(request):
    return render(request, 'hotdogdelivery/order.html')

def home(request):
    return render(request, 'hotdogdelivery/home.html')

def contact(request):
    return render(request, 'hotdogdelivery/contact.html')


def get_kanye_quote(request):
    try:
        response = requests.get('https://api.kanye.rest')
        data = response.json()
        return JsonResponse(data)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

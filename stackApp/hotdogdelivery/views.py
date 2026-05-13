from django.shortcuts import render

def hotdogs_vs_sausages(request):
    return render(request, 'hotdogdelivery/hotdogs_vs_sausages.html')

def home(request):
    return render(request, 'hotdogdelivery/home.html')

def contact(request):
    return render(request, 'hotdogdelivery/contact.html')
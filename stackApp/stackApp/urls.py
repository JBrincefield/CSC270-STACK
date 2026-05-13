"""
URL configuration for stackApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

"""
1. User visits: http://localhost:8000/hotdogs/

2. Django checks stackApp/urls.py
    "Does this URL match any patterns?"
    → Found: path('hotdogs/', views.hotdogs_vs_sausages)

3. Django calls the view function:
    views.hotdogs_vs_sausages(request)

4. View renders the HTML template:
    render(request, 'comparison/hotdogs_vs_sausages.html')

5. HTML is sent back to browser
    User sees your page! :hotdog: 🥵🐕 🌭🌭 
"""

from django.contrib import admin
from django.urls import path
from hotdogdelivery import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('hotdogs/', views.hotdogs_vs_sausages, name='hotdogs_vs_sausages'),
]

"""URL configuration for stackApp."""

from django.contrib import admin
from django.urls import path
from hotdogdelivery import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('mission/', views.our_mission, name='mission'),
    path('order/', views.order, name='order'),
    path('api/orders/', views.api_orders_list, name='api_orders_list'),
    path('api/orders/<int:order_id>/', views.api_order_detail, name='api_order_detail'),
    path('api/kanye/', views.get_kanye_quote, name='kanye_quote'),
]

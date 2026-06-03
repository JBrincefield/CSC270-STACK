"""URL configuration for stackApp."""

from django.contrib import admin
from django.urls import path
from hotdogdelivery import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('auth/', views.auth_page, name='auth_page'),
    path('auth/session/', views.auth_session, name='auth_session'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('mission/', views.our_mission, name='mission'),
    path('order/', views.order, name='order'),
    
    #api/order endpoints are for CRUD on orders
    path('api/orders/', views.api_orders_list, name='api_orders_list'),
    path('api/orders/<int:order_id>/', views.api_order_detail, name='api_order_detail'),
    path('api/orders/<int:order_id>/like/', views.api_order_like, name='api_order_like'),
    path('api/orders/<int:order_id>/messages/', views.api_order_messages, name='api_order_messages'),

    path('api/kanye/', views.get_kanye_quote, name='kanye_quote'),
]

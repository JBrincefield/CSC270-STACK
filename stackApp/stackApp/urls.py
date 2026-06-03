"""URL configuration for stackApp."""

from django.contrib import admin
from django.urls import path
from hotdogdelivery import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path('mission/', views.our_mission, name='mission'),
    path('order/', views.order, name='order'),
    
    #api/order endpoints are for CRUD on orders
    path('api/orders/', views.api_orders_list, name='api_orders_list'),
    path('api/orders/<int:order_id>/', views.api_order_detail, name='api_order_detail'),
    path('api/orders/<int:order_id>/review/', views.api_order_review, name='api_order_review'),

    path('api/kanye/', views.get_kanye_quote, name='kanye_quote'),

    # Firebase Auth endpoints
    path('api/auth/verify/', views.verify_token, name='verify_token'),
    path('api/auth/logout/', views.logout_view, name='logout'),
]

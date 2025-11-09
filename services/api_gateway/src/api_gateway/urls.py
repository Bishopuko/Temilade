from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.send_notification, name='send_notification'),
    path('health/', views.health_check, name='health_check'),
]

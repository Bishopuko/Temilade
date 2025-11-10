from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.send_notification, name='send_notification'),
    path('notifications/<str:request_id>/status/', views.get_notification_status, name='notification_status'),
    path('health/', views.health_check, name='health_check'),
]

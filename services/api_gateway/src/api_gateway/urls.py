from django.urls import path, include
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('v1/users/', views.UserRegistrationView.as_view(), name='user_registration'),
    path('v1/notifications/', views.send_notification, name='send_notification'),
    path('v1/notifications/<str:request_id>/status/', views.get_notification_status, name='notification_status'),
    path('health/', views.health_check, name='health_check'),

    # OpenAPI documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # JWT authentication endpoints
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', views.CustomTokenVerifyView.as_view(), name='token_verify'),
]

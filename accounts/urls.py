from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import EmailTokenObtainPairView, MeView

urlpatterns = [
    path("auth/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("accounts/me/", MeView.as_view(), name="me"),
]

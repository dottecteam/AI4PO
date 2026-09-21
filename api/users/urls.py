from django.urls import path
from .views import LoginView, LogoutView, MeView, AdminOnlyView

urlpatterns = [
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", MeView.as_view()),
    path("admin-only/", AdminOnlyView.as_view()), # Rota de teste
]
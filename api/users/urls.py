from django.urls import path
from .views import (
    LoginView, LogoutView, MeView, AdminOnlyView,
    AdminUserListView, AdminUserDetailView,
)

urlpatterns = [
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", MeView.as_view()),
    path("admin-only/", AdminOnlyView.as_view()),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users-list"),
    path("admin/users/<int:id_po>/", AdminUserDetailView.as_view(), name="admin-users-detail"),
]
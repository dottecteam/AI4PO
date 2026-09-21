# api/users/permissions.py
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Permite acesso apenas para usuários que são administradores (is_staff=True).
    """
    def has_permission(self, request, view):
        # Verifica se o usuário existe, está autenticado e é staff (Admin)
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
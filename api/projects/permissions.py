from rest_framework.permissions import SAFE_METHODS, BasePermission


def pode_gerenciar_projeto(usuario, projeto):
    """O administrador gerencia todos os projetos; o PO, apenas os que organiza."""
    if not (usuario and usuario.is_authenticated):
        return False
    return bool(usuario.is_staff or projeto.usuario_po_id == usuario.pk)


class PodeGerenciarParticipacao(BasePermission):
    """Task #15-3 — leitura liberada; alterar ou excluir uma participação
    só é permitido ao PO responsável pelo projeto ou a um administrador."""

    message = "Apenas o PO responsável pelo projeto ou um administrador pode alterar este registro."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return pode_gerenciar_projeto(request.user, obj.projeto)

# api/users/permissions.py
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Permite acesso apenas para usuários que são administradores (is_staff=True).
    """
    def has_permission(self, request, view):
        # Verifica se o usuário existe, está autenticado e é staff (Admin)
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


def ve_tudo(usuario):
    """Regra unica de visibilidade, espelhando views_dashboard.py.

    Admin enxerga todos os projetos; PO comum so os proprios. `is_admin` ainda
    nao existe no modelo, entao hoje isto sempre devolve False e o escopo vale
    para todos -- incluir `is_staff` aqui seria mudar o que a demo mostra, e por
    isso fica como decisao de produto pendente.
    """
    return bool(getattr(usuario, "is_admin", False))


def escopo(usuario, campo):
    """Devolve kwargs de filtro para usar em .filter()/get_object_or_404().

    `campo` e o caminho ate o PO dono (ex.: 'usuario_po',
    'projeto__usuario_po', 'pbi__feature__epico__projeto__usuario_po').
    Objeto de outro usuario fica fora do queryset, entao vira 404 -- mesmo
    comportamento que views_busca.py e retrieval.buscar_trechos ja adotam.
    """
    return {} if ve_tudo(usuario) else {campo: usuario}
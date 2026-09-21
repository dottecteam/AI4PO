# Esse arquivo se trata de um painel de admin do django para manipular dados manualmente.

from django.contrib import admin
from .models import User

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Quais colunas vão aparecer na listagem
    list_display = ('id_po', 'nome', 'email', 'is_staff', 'is_active')
    # Adiciona uma barra de pesquisa
    search_fields = ('nome', 'email')
    # Adiciona filtros laterais
    list_filter = ('is_staff', 'is_superuser', 'is_active')


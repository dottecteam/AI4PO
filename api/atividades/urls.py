from django.urls import path
from .views import AtividadesRecentesView

urlpatterns = [
    path("atividades/recentes/", AtividadesRecentesView.as_view(), name="atividades-recentes"),
]
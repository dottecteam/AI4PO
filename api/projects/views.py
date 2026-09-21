from rest_framework import generics
from projects.models import Projeto
from projects.serializers import ProjetoSerializer

class ProjetoListCreateView(generics.ListCreateAPIView):
    queryset = Projeto.objects.all()
    serializer_class = ProjetoSerializer


class ProjetoDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Projeto.objects.all()
    serializer_class = ProjetoSerializer
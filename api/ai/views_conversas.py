from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversa
from .serializers import ConversaDetalheSerializer, ConversaListSerializer


class ConversaListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversas = Conversa.objects.filter(usuario_po=request.user)
        return Response(ConversaListSerializer(conversas, many=True).data)


class ConversaDetalheView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversa_id):
        conversa = get_object_or_404(Conversa, pk=conversa_id, usuario_po=request.user)
        return Response(ConversaDetalheSerializer(conversa).data)
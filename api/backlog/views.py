from rest_framework import generics
from backlog.models import Epico, Feature, PBI, Cenario
from backlog.serializers import EpicoSerializer, FeatureSerializer, PBISerializer, CenarioSerializer
from users.permissions import escopo
from django.db.models import Count


class EpicoListCreateView(generics.ListCreateAPIView):
    serializer_class = EpicoSerializer

    def get_queryset(self):
        queryset = Epico.objects.annotate(
            total_features=Count("features", distinct=True),
            total_pbis=Count("features__pbis", distinct=True),
        ).filter(**escopo(self.request.user, "projeto__usuario_po"))
        id_projeto = self.request.query_params.get('idProjeto')
        if id_projeto is not None:
            queryset = queryset.filter(projeto_id=id_projeto)
        return queryset


class EpicoDataView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EpicoSerializer

    def get_queryset(self):
        # Epico de projeto alheio fica fora do queryset -> 404.
        return Epico.objects.filter(
            **escopo(self.request.user, "projeto__usuario_po")
        )


class FeatureListCreateView(generics.ListCreateAPIView):
    serializer_class = FeatureSerializer

    def get_queryset(self):
        queryset = Feature.objects.annotate(
            total_pbis = Count("pbis", distinct=True)
        ).filter(**escopo(self.request.user, "epico__projeto__usuario_po"))
        id_epico = self.request.query_params.get('idEpico')
        if id_epico is not None:
            queryset = queryset.filter(epico_id=id_epico)
        return queryset


class FeatureDataView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FeatureSerializer

    def get_queryset(self):
        return Feature.objects.filter(
            **escopo(self.request.user, "epico__projeto__usuario_po")
        )


class PBIListCreateView(generics.ListCreateAPIView):
    serializer_class = PBISerializer

    def get_queryset(self):
        queryset = PBI.objects.filter(
            **escopo(self.request.user, "feature__epico__projeto__usuario_po")
        )
        id_feature = self.request.query_params.get('idFeature')
        if id_feature is not None:
            queryset = queryset.filter(feature_id=id_feature)
        return queryset


class PBIDataView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PBISerializer

    def get_queryset(self):
        return PBI.objects.filter(
            **escopo(self.request.user, "feature__epico__projeto__usuario_po")
        )


class CenarioListCreateView(generics.ListCreateAPIView):
    serializer_class = CenarioSerializer

    def get_queryset(self):
        return Cenario.objects.filter(
            **escopo(self.request.user, "pbi__feature__epico__projeto__usuario_po")
        )


class CenarioDataView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CenarioSerializer

    def get_queryset(self):
        return Cenario.objects.filter(
            **escopo(self.request.user, "pbi__feature__epico__projeto__usuario_po")
        )
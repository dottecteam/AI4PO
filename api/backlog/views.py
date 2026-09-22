from rest_framework import generics
from backlog.models import Epico, Feature, PBI, Cenario
from backlog.serializers import EpicoSerializer, FeatureSerializer, PBISerializer, CenarioSerializer


class EpicoListCreateView(generics.ListCreateAPIView):
    serializer_class = EpicoSerializer

    def get_queryset(self):
        queryset = Epico.objects.all()
        id_projeto = self.request.query_params.get('idProjeto')
        if id_projeto is not None:
            queryset = queryset.filter(projeto_id=id_projeto)
        return queryset


class EpicoDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Epico.objects.all()
    serializer_class = EpicoSerializer


class FeatureListCreateView(generics.ListCreateAPIView):
    serializer_class = FeatureSerializer

    def get_queryset(self):
        queryset = Feature.objects.all()
        id_epico = self.request.query_params.get('idEpico')
        if id_epico is not None:
            queryset = queryset.filter(epico_id=id_epico)
        return queryset


class FeatureDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer


class PBIListCreateView(generics.ListCreateAPIView):
    serializer_class = PBISerializer

    def get_queryset(self):
        queryset = PBI.objects.all()
        id_feature = self.request.query_params.get('idFeature')
        if id_feature is not None:
            queryset = queryset.filter(feature_id=id_feature)
        return queryset


class PBIDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PBI.objects.all()
    serializer_class = PBISerializer


class CenarioListCreateView(generics.ListCreateAPIView):
    queryset = Cenario.objects.all()
    serializer_class = CenarioSerializer


class CenarioDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cenario.objects.all()
    serializer_class = CenarioSerializer
from rest_framework import generics
from backlog.models import Epico, Feature, PBI, Cenario
from backlog.serializers import EpicoSerializer, FeatureSerializer, PBISerializer, CenarioSerializer


class EpicoListCreateView(generics.ListCreateAPIView):
    queryset = Epico.objects.all()
    serializer_class = EpicoSerializer


class EpicoDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Epico.objects.all()
    serializer_class = EpicoSerializer


class FeatureListCreateView(generics.ListCreateAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer


class FeatureDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer


class PBIListCreateView(generics.ListCreateAPIView):
    queryset = PBI.objects.all()
    serializer_class = PBISerializer


class PBIDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PBI.objects.all()
    serializer_class = PBISerializer


class CenarioListCreateView(generics.ListCreateAPIView):
    queryset = Cenario.objects.all()
    serializer_class = CenarioSerializer


class CenarioDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cenario.objects.all()
    serializer_class = CenarioSerializer
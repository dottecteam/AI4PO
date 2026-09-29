from django.urls import path
from backlog.views import EpicoDataView, EpicoListCreateView

from django.urls import path
from backlog.views import (
    EpicoListCreateView, EpicoDataView,
    FeatureListCreateView, FeatureDataView,
    PBIListCreateView, PBIDataView,
    CenarioListCreateView, CenarioDataView,
)

urlpatterns = [
    path('epicos/', EpicoListCreateView.as_view(), name='epico-list-create'),
    path('epicos/<int:pk>/', EpicoDataView.as_view(), name='epico-detail'),

    path('features/', FeatureListCreateView.as_view(), name='feature-list-create'),
    path('features/<int:pk>/', FeatureDataView.as_view(), name='feature-detail'),

    path('pbis/', PBIListCreateView.as_view(), name='pbi-list-create'),
    path('pbis/<int:pk>/', PBIDataView.as_view(), name='pbi-detail'),

    path('cenarios/', CenarioListCreateView.as_view(), name='cenario-list-create'),
    path('cenarios/<int:pk>/', CenarioDataView.as_view(), name='cenario-detail'),
]
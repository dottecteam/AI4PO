from django.urls import path

from .views import SimilarityCheckView, chat


urlpatterns = [
    path("chat/", chat, name="chat"),
    path("similarity/", SimilarityCheckView.as_view(), name="similarity-check"),
]

from django.urls import path

from .views import DocumentoUploadView


urlpatterns = [
    path(
        "projects/<int:project_id>/documents/",
        DocumentoUploadView.as_view(),
        name="document-upload",
    ),
]

from django.urls import path
from . import views
urlpatterns = [
    path("upload/", views.upload_document, name="upload_document"),
    path("my-documents/", views.my_documents, name="my_documents"),
]
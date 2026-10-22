
from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_view, name="chat"),
    path("history/", views.chat_history, name="chat_history"),
    path("delete/<int:session_id>/", views.delete_chat, name="delete_chat"),
]

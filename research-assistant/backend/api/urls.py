from django.urls import path
from api import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('chat/', views.chat, name='chat'),
    path('ingest/', views.ingest, name='ingest'),
]

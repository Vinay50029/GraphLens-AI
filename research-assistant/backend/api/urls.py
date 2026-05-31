from django.urls import path
from api import views

urlpatterns = [
    # HTML template views
    path('', views.chat_view, name='chat_dashboard'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # JSON API endpoints
    path('api/health/', views.health, name='health'),
    path('api/chat/', views.chat, name='chat'),
    path('api/ingest/', views.ingest, name='ingest'),
    
    # User Files APIs
    path('api/files/', views.list_files_api, name='list_files'),
    path('api/files/upload/', views.upload_file_api, name='upload_file'),
    path('api/files/delete/<int:file_id>/', views.delete_file_api, name='delete_file'),
]


# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_files, name='list_files'),
    path('download/', views.download_file, name='download_file'),
    path('download_folder_as_zip/', views.download_folder_as_zip, name='download_folder_as_zip'),
]
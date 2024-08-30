from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_files),
    path('generate_answers', views.generate_answers)
]

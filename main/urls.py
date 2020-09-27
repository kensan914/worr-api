from django.urls import path, re_path
import main
from main import views

app_name = 'main'

urlpatterns = [
    path('', views.top, name='top'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
]

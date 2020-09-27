from django.urls import path, re_path
import main
from main import views

app_name = 'api'

urlpatterns = [
    path('', views.top, name='terms_of_service'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
]

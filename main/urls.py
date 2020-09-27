from django.urls import path
from main import views

app_name = 'api'

urlpatterns = [
    path('/', views.top, name='top'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
]

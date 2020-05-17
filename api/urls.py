from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
    path('test/', views.test, name='test'),
]

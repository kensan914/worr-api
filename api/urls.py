from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
router.register('users', views.UserViewSet)
router.register('voices', views.VoiceViewSet)

urlpatterns = [
    path('test/', views.test, name='test'),
    path('', include(router.urls)),
]

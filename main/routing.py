from django.urls import path
from main.consumers import NotificationConsumer


websocket_urlpatterns_main = [
    path('notification/', NotificationConsumer),
]

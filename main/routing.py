from django.urls import path
from main.consumers import NotificationConsumer
from main.v2.consumers import NotificationV2Consumer
from main.v4.consumers import NotificationConsumer as NotificationV4Consumer

websocket_urlpatterns_main = [
    path('notification/', NotificationConsumer),
    path('v2/notification/', NotificationV2Consumer),
    path('v4/notification/', NotificationV4Consumer),
]

from django.urls import path
from chat.consumers import *


websocket_urlpatterns_chat = [
    path('chat/<uuid:room_id>/', ChatConsumer),
]

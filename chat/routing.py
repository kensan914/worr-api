from django.urls import path
from chat.consumers import *


websocket_urlpatterns_chat = [
    path('chat-request/<uuid:user_id>/', ChatRequestConsumer),
    path('chat/<uuid:room_id>/', ChatConsumer),
]

from django.urls import path
from chat.consumers import *
from chat.v2.consumers import ChatConsumerV2


websocket_urlpatterns_chat = [
    path('chat/<uuid:room_id>/', ChatConsumer),
    path('v2/chat/<uuid:room_id>/', ChatConsumerV2),
]

from django.urls import path
from chat.consumers import ChatConsumer
from chat.v2.consumers import ChatConsumerV2
from chat.v4.consumers import ChatConsumer as ChatConsumerV4

websocket_urlpatterns_chat = [
    path('chat/<uuid:room_id>/', ChatConsumer),
    path('v2/chat/<uuid:room_id>/', ChatConsumerV2),
    path('v4/chat/<uuid:room_id>/', ChatConsumerV4)
]

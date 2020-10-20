from rest_framework import serializers
from account.serializers import UserSerializer
from chat.models import Message, Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['room_id', 'user', 'date']

    room_id = serializers.UUIDField(source='id')
    user = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    def get_user(self, obj):
        if obj.request_user.id == self.context['me'].id:
            return UserSerializer(obj.response_user).data
        elif obj.response_user.id == self.context['me'].id:
            return UserSerializer(obj.request_user).data

    def get_date(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%M:%S')


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message_id', 'message', 'is_me', 'time']

    message_id = serializers.UUIDField(source='id')
    message = serializers.CharField(source='content')
    is_me = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    def get_is_me(self, obj):
        return self.context['me'].id == obj.user.id

    def get_time(self, obj):
        return obj.time.strftime('%Y/%m/%d %H:%M:%S')

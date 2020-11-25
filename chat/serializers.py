from rest_framework import serializers
from account.serializers import UserSerializer, MeSerializer
from chat.models import Message, Room, Worry


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['room_id', 'user', 'date', 'worried_user_id']

    room_id = serializers.UUIDField(source='id')
    user = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    worried_user_id = serializers.SerializerMethodField()

    def get_user(self, obj):
        if obj.request_user.id == self.context['me'].id:
            return UserSerializer(obj.response_user).data
        elif obj.response_user.id == self.context['me'].id:
            return UserSerializer(obj.request_user).data

    def get_date(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%M:%S')

    def get_worried_user_id(self, obj):
        if obj.is_worried_request_user:
            return obj.request_user.id
        else:
            return obj.response_user.id


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


class WorrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Worry
        fields = ('id', 'time', 'message', 'user')

    time = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def get_time(self, obj):
        return obj.time.strftime('%Y/%m/%d %H:%M:%S')
    def get_user(self, obj):
        if obj.user.id == self.context['me'].id:
            return MeSerializer(obj.user).data
        return UserSerializer(obj.user).data


class PostWorrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Worry
        fields = ('id', 'time', 'message', 'user')

    time = serializers.SerializerMethodField()
    def get_time(self, obj):
        return obj.time.strftime('%Y/%m/%d %H:%M:%S')

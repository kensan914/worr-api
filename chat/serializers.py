from rest_framework import serializers
from chat.models import Message


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

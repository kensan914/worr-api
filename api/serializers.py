from rest_framework import serializers
from account.serializers import UserSerializer
from main.models import Notification, NotificationType


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = ['recipient']

    subject = UserSerializer()
    message = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    def get_message(self, obj):
        if obj.message:
            return obj.message
        elif obj.type == NotificationType.CHAT_REQUEST:
            return '{}さんからリクエストが届きました。トーク画面で確認しましょう。'.format(obj.subject.username)
        elif obj.type == NotificationType.CHAT_RESPONSE:
            return '{}さんがリクエストに答えました。トークを開始します。'.format(obj.subject.username)

    def get_date(self, obj):
        return obj.date.strftime('%Y/%m/%d %H:%M:%S')

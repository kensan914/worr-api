from django.db.models import Q
from rest_framework import serializers
from account.serializers import GenreOfWorriesSerializer
from account.v2.serializers import MeV2Serializer, UserV2Serializer
from chat.models import Room, TalkTicket, TalkStatus, TalkingRoom, MessageV2


class TalkTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkTicket
        fields = ['id', 'owner', 'worry', 'is_speaker', 'status', 'wait_start_time',
                  'can_talk_heterosexual', 'can_talk_different_job', 'room']

    owner = serializers.SerializerMethodField()
    worry = GenreOfWorriesSerializer()
    status = serializers.SerializerMethodField()
    wait_start_time = serializers.SerializerMethodField()
    room = serializers.SerializerMethodField()

    def get_owner(self, obj):
        if obj.owner.id == self.context['me'].id:
            return MeV2Serializer(obj.owner).data
        else:
            return UserV2Serializer(obj.owner).data

    def get_status(self, obj):
        if obj.status in TalkStatus.values:
            t = TalkStatus(obj.status)
        else:
            t = TalkStatus.STOPPING
        return {'key': t.value, 'name': t.name, 'label': t.label}

    def get_wait_start_time(self, obj):
        if obj.wait_start_time:
            return obj.wait_start_time.strftime('%Y/%m/%d %H:%M:%S')

    def get_room(self, obj):
        if obj.status == TalkStatus.TALKING or obj.status == TalkStatus.FINISHING or obj.status == TalkStatus.APPROVING:
            rooms = TalkingRoom.objects.filter(
                Q(speaker_ticket=obj) | Q(listener_ticket=obj))
            if rooms.exists():
                return TalkingRoomSerializer(rooms.first(), context=self.context).data
        return None


class TalkTicketPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkTicket
        fields = ['is_speaker', 'status',
                  'can_talk_heterosexual', 'can_talk_different_job']


class TalkingRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'user', 'started_at',
                  'ended_at', 'is_alert', 'is_time_out']

    user = serializers.SerializerMethodField()
    started_at = serializers.SerializerMethodField()
    ended_at = serializers.SerializerMethodField()

    def is_me_speaker(self, obj):
        return obj.speaker_ticket.owner.id == self.context['me'].id

    def get_user(self, obj):
        if self.is_me_speaker(obj):
            return UserV2Serializer(obj.listener_ticket.owner).data
        else:
            return UserV2Serializer(obj.speaker_ticket.owner).data

    def get_started_at(self, obj):
        if obj.started_at:
            return obj.started_at.strftime('%Y/%m/%d %H:%M:%S')

    def get_ended_at(self, obj):
        if obj.ended_at:
            return obj.ended_at.strftime('%Y/%m/%d %H:%M:%S')


class MessageV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = MessageV2
        fields = ['message_id', 'message', 'is_me', 'time']

    message_id = serializers.UUIDField(source='id')
    message = serializers.CharField(source='content')
    is_me = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    def get_is_me(self, obj):
        return self.context['me'].id == obj.user.id

    def get_time(self, obj):
        if obj.time:
            return obj.time.strftime('%Y/%m/%d %H:%M:%S')

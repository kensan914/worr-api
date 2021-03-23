from django.db.models import Q
from django.utils import timezone
from rest_framework import views, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from chat.consumers import ChatConsumer
from chat.models import TalkTicket, TalkStatus, TalkingRoom
from chat.v2.serializers import TalkTicketSerializer, TalkTicketPatchSerializer
from fullfii import end_talk_v2, start_matching


class TalkTicketAPIView(views.APIView):
    def post(self, request, *args, **kwargs):
        talk_ticket_id = self.kwargs.get('talk_ticket_id')
        talk_ticket = get_object_or_404(TalkTicket, id=talk_ticket_id)

        if request.data['status'] == TalkStatus.WAITING or request.data['status'] == TalkStatus.STOPPING:
            # shuffle/stopが実行されたとき(waiting or stoppingへの変更)
            serializer = TalkTicketPatchSerializer(
                instance=talk_ticket, data=request.data, partial=True)
            if serializer.is_valid():
                ### params 変更 ###
                serializer.save()
                talk_ticket.wait_start_time = timezone.now()  # reset wait_start_time
                talk_ticket.save()
                ###################

                talking_rooms = TalkingRoom.objects.filter(is_end=False).filter(
                    Q(speaker_ticket=talk_ticket) | Q(listener_ticket=talk_ticket))
                if talking_rooms.exists():
                    talking_room = talking_rooms.first()
                    ChatConsumer.send_end_talk(
                        talking_room.id, sender_id=request.user.id)
                    end_talk_v2(talking_room, ender=request.user)

                response_data = TalkTicketSerializer(
                    talk_ticket, context={'me': request.user}).data
                start_matching(version=3)
                return Response(response_data, status=status.HTTP_200_OK)

        elif request.data['status'] == TalkStatus.TALKING:
            serializer = TalkTicketPatchSerializer(
                instance=talk_ticket, data=request.data, partial=True)
            if serializer.is_valid():
                ### params 変更 ###
                serializer.save()
                ###################

                response_data = TalkTicketSerializer(
                    talk_ticket, context={'me': request.user}).data
                return Response(response_data, status=status.HTTP_200_OK)

        # WAITING・STOPPING・APPROVING以外への変更は不可.
        return Response(TalkTicketSerializer(talk_ticket, context={'me': request.user}).data, status=status.HTTP_409_CONFLICT)


talkTicketAPIView = TalkTicketAPIView.as_view()

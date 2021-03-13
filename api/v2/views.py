from django.db.models import Q
from django.utils import timezone
from rest_framework import views, status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from account.models import GenreOfWorries, Gender, Job
from account.serializers import GenreOfWorriesSerializer
from account.v2.serializers import MeV2Serializer, PatchMeV2Serializer
from account.views import MeAPIView, ProfileImageAPIView
from chat.consumers import ChatConsumer
from chat.models import TalkTicket, TalkStatus, TalkingRoom
from chat.v2.serializers import TalkTicketSerializer, TalkTicketPatchSerializer
from fullfii import end_talk_v2, start_matching, increment_num_of_thunks, create_talk_ticket, end_talk_ticket, \
    activate_talk_ticket
import fullfii
from asgiref.sync import async_to_sync


class ProfileParamsV2APIView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def get_profile_params(self, serializer, model):
        record_obj = {}
        for record in model.objects.all():
            record_data = serializer(record).data
            record_obj[record_data['key']] = record_data
        return record_obj

    def get_text_choices(self, text_choices):
        text_choices_obj = {}

        tc = text_choices
        for name, value, label in zip(tc.names, tc.values, tc.labels):
            text_choices_obj[value] = {
                'key': value,
                'name': name,
                'label': label,
            }
        return text_choices_obj

    def get(self, request, *args, **kwargs):
        # profile params
        genre_of_worries_obj = self.get_profile_params(
            GenreOfWorriesSerializer, GenreOfWorries)

        # text choices
        gender_obj = self.get_text_choices(Gender)
        job_obj = self.get_text_choices(Job)

        return Response({
            'genre_of_worries': genre_of_worries_obj,
            'gender': gender_obj,
            'job': job_obj,
        }, status.HTTP_200_OK)


profileParamsV2APIView = ProfileParamsV2APIView.as_view()


class MeV2APIView(MeAPIView):
    Serializer = MeV2Serializer
    PatchSerializer = PatchMeV2Serializer


meV2APIView = MeV2APIView.as_view()


class ProfileImageV2APIView(ProfileImageAPIView):
    Serializer = MeV2Serializer


profileImageV2APIView = ProfileImageV2APIView.as_view()


class TalkInfoV2APIView(views.APIView):
    def get(self, request, *args, **kwargs):
        talk_tickets = TalkTicket.objects.filter(
            owner=request.user, is_active=True)
        talking_tickets_data = TalkTicketSerializer(
            talk_tickets,
            many=True,
            context={'me': request.user}
        ).data

        return Response({
            'talk_tickets': talking_tickets_data,
        }, status.HTTP_200_OK)


talkInfoV2APIView = TalkInfoV2APIView.as_view()


class TalkTicketAPIView(views.APIView):
    def post(self, request, *args, **kwargs):
        talk_ticket_id = self.kwargs.get('talk_ticket_id')
        talk_ticket = get_object_or_404(TalkTicket, id=talk_ticket_id)

        # talkingへの変更は不可.
        if request.data['status'] == TalkStatus.TALKING or request.data['status'] == TalkStatus.FINISHING:
            return Response(TalkTicketSerializer(talk_ticket, context={'me': request.user}).data, status=status.HTTP_409_CONFLICT)

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
            start_matching()
            return Response(response_data, status=status.HTTP_200_OK)


talkTicketAPIView = TalkTicketAPIView.as_view()


class CloseTalkV2APIView(views.APIView):
    def post(self, request, *args, **kwargs):
        room_id = self.kwargs.get('room_id')
        has_thunks = bool(request.data['has_thunks'])
        room = get_object_or_404(TalkingRoom, id=room_id)

        if request.user.id != room.speaker_ticket.owner.id and request.user.id != room.listener_ticket.owner.id:
            return Response({'type': 'conflict', 'message': 'you are not the room member.'}, status=status.HTTP_409_CONFLICT)

        # check which request or response
        if request.user.id == room.speaker_ticket.owner.id:
            target_user = room.listener_ticket.owner
        else:
            target_user = room.speaker_ticket.owner

        # send thunks
        if has_thunks:
            increment_num_of_thunks(target_user)

            # send fcm(THUNKS)
            async_to_sync(fullfii.send_fcm)(target_user, {
                'type': 'THUNKS',
                'user': request.user,
            })

        return Response({'status': 'success'}, status=status.HTTP_200_OK)


closeTalkV2APIView = CloseTalkV2APIView.as_view()


class WorryAPIView(views.APIView):
    def post(self, request, *args, **kwargs):
        if 'genre_of_worries' in request.data:
            data = GenreOfWorriesSerializer(
                request.data['genre_of_worries'], many=True).data
            will_add_worries = GenreOfWorries.objects.filter(
                key__in=[part_of_data['key'] for part_of_data in data])

            # アクティブのみ
            talk_tickets = TalkTicket.objects.filter(
                owner=request.user, is_active=True)
            # 非アクティブも含む
            all_talk_tickets = TalkTicket.objects.filter(owner=request.user)

            # 追加
            added_talk_tickets = []
            for will_add_worry in will_add_worries:
                # アクティブではない時
                if not talk_tickets.filter(worry=will_add_worry).exists():
                    target_talk_tickets = all_talk_tickets.filter(
                        worry=will_add_worry)
                    # 既にtalk_ticketが存在する時
                    if target_talk_tickets.exists():
                        target_talk_ticket = activate_talk_ticket(
                            target_talk_tickets.first())
                        added_talk_tickets.append(target_talk_ticket)

                    # 未だtalk_ticketが作成されていない時
                    else:
                        added_talk_ticket = create_talk_ticket(
                            request.user, will_add_worry)
                        added_talk_tickets.append(added_talk_ticket)

            # 削除
            removed_talk_ticket_keys = []
            for talk_ticket in talk_tickets:
                if not will_add_worries.filter(key=talk_ticket.worry.key).exists():
                    removed_talk_ticket_keys.append(talk_ticket.worry.key)
                    talk_ticket.is_active = False

                    # end talk
                    end_talk_ticket(talk_ticket)
                    talking_rooms = TalkingRoom.objects.filter(is_end=False).filter(
                        Q(speaker_ticket=talk_ticket) | Q(listener_ticket=talk_ticket))
                    if talking_rooms.exists():
                        talking_room = talking_rooms.first()
                        ChatConsumer.send_end_talk(
                            talking_room.id, sender_id=request.user.id)
                        end_talk_v2(talking_room, ender=request.user)

            response_data = {
                'added_talk_tickets': TalkTicketSerializer(added_talk_tickets, context={'me': request.user}, many=True).data,
                'removed_talk_ticket_keys': removed_talk_ticket_keys,
            }
            start_matching()
            return Response(response_data, status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


worryAPIView = WorryAPIView.as_view()


class GenderAPIView(views.APIView):
    def put(self, request, *args, **kwargs):
        expected_keys = ['female', 'male', 'secret']
        if 'key' in request.data and request.data['key'] in expected_keys:
            if request.data['key'] == 'female' and request.user.gender != Gender.MALE:
                request.user.gender = Gender.FEMALE
                request.user.is_secret_gender = False
            elif request.data['key'] == 'male' and request.user.gender != Gender.FEMALE:
                request.user.gender = Gender.MALE
                request.user.is_secret_gender = False
            elif request.data['key'] == 'secret':
                request.user.is_secret_gender = True
            request.user.save()
            return Response({
                'me': MeV2Serializer(request.user).data,
            }, status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_409_CONFLICT)


genderAPIView = GenderAPIView.as_view()

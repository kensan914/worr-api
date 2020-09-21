import uuid
from django.db.models import Q
from rest_framework import views, status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from account.serializers import UserSerializer, FeaturesSerializer, GenreOfWorriesSerializer, ScaleOfWorriesSerializer, \
    WorriesToSympathizeSerializer
from chat.models import Room
from chat.serializers import RoomSerializer
from fullfii.db.account import get_all_accounts
from account.models import Feature, GenreOfWorries, ScaleOfWorries, WorriesToSympathize, Account
from main.consumers import NotificationConsumer
from main.models import NotificationType


class ProfileParamsAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def get_profile_params(self, serializer, model):
        record_obj = {}
        for record in model.objects.all():
            record_data = serializer(record).data
            record_obj[record_data['key']] = record_data
        return record_obj

    def get(self, request, *args, **kwargs):
        features_obj = self.get_profile_params(FeaturesSerializer, Feature)
        genre_of_worries_obj = self.get_profile_params(GenreOfWorriesSerializer, GenreOfWorries)
        scale_of_worries_obj = self.get_profile_params(ScaleOfWorriesSerializer, ScaleOfWorries)
        worries_to_sympathize_obj = self.get_profile_params(WorriesToSympathizeSerializer, WorriesToSympathize)
        return Response({
            'features': features_obj,
            'genre_of_worries': genre_of_worries_obj,
            'scale_of_worries': scale_of_worries_obj,
            'worries_to_sympathize': worries_to_sympathize_obj,
        }, status.HTTP_200_OK)

profileParamsAPIView = ProfileParamsAPIView.as_view()


class UsersAPIView(views.APIView):
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')

        if user_id:
            users = get_all_accounts(me=request.user).filter(id=user_id)
            if users.exists():
                return Response(UserSerializer(users.first()).data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'not found user'}, status=status.HTTP_404_NOT_FOUND)
        else:
            page = int(self.request.GET.get('page')) if self.request.GET.get('page') is not None else 1
            genre = self.request.GET.get('genre')

            genre_of_worries = GenreOfWorries.objects.filter(value=genre)
            if genre_of_worries.exists():
                users = get_all_accounts(me=request.user).filter(genre_of_worries=genre_of_worries.first())
            else:
                users = get_all_accounts(me=request.user)
            users = users[self.paginate_by * (page - 1): self.paginate_by * page]
            users_data = UserSerializer(users, many=True).data
            return Response(users_data, status=status.HTTP_200_OK)

usersAPIView = UsersAPIView.as_view()


class TalkRequestAPIView(views.APIView):
    def post(self, request, *args, **kwargs):
        target_user_id = self.kwargs.get('user_id')
        room_id = uuid.uuid4()

        # create room
        target_user = get_object_or_404(Account, id=target_user_id)
        if not Room.objects.filter(
                Q(request_user=request.user, response_user=target_user) |
                Q(request_user=target_user, response_user=request.user)).exists():
            room = Room(
                id=room_id,
                request_user=request.user,
                response_user=target_user,
            )
            room.save()
        else:
            return Response({'type': 'conflict', 'message': 'the room already exists'}, status=status.HTTP_409_CONFLICT)

        # set notification to target user
        NotificationConsumer.send_notification(recipient=target_user, subject=request.user, notification_type=NotificationType.TALK_REQUEST, reference_id=room_id)

        target_user_data = UserSerializer(target_user).data
        return Response({'room_id': room_id, 'target_user': target_user_data}, status=status.HTTP_200_OK)

talkRequestAPIView = TalkRequestAPIView.as_view()


class CancelTalkRequestAPIView(views.APIView):
    def post(self, request, *args, **kwargs):
        room_id = self.kwargs.get('room_id')
        room = get_object_or_404(Room, id=room_id)

        # check if the request.user is a room member
        if request.user.id != room.request_user.id:
            return Response({'type': 'conflict', 'message': "you are not the room's request user."}, status=status.HTTP_409_CONFLICT)

        request_user = request.user
        response_user = room.response_user

        # delete room
        room.delete()

        # set notification to target user
        NotificationConsumer.send_notification(recipient=response_user, subject=request_user, notification_type=NotificationType.CANCEL_TALK_REQUEST, reference_id=room_id)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

cancelTalkRequestAPIView = CancelTalkRequestAPIView.as_view()


class TalkInfoAPIView(views.APIView):
    def get(self, request, *args, **kwargs):
        # send objects
        rooms_i_sent = Room.objects.filter(is_start=False, request_user__id=request.user.id)
        rooms_i_sent_data = RoomSerializer(rooms_i_sent, many=True, context={'me': request.user}).data

        # in objects
        rooms_i_received = Room.objects.filter(is_start=False, response_user_id=request.user.id)
        rooms_i_received_data = RoomSerializer(rooms_i_received, many=True, context={'me': request.user}).data

        # talk rooms
        # talking_rooms = Room.objects.filter(Q(request_user__id=request.user.id) | Q(response_user_id=request.user.id), is_start=True)
        # talking_room_ids = [str(talking_room.id) for talking_room in talking_rooms]

        # return Response({'send_objects': rooms_i_sent_data, 'in_objects': rooms_i_received_data, 'talking_room_ids': talking_room_ids}, status=status.HTTP_200_OK)
        return Response({'send_objects': rooms_i_sent_data, 'in_objects': rooms_i_received_data})

talkInfoAPIView = TalkInfoAPIView.as_view()
import uuid

import requests
from django.db.models import Q
from django.utils import timezone
from rest_framework import views, status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

import fullfii
from account.serializers import UserSerializer, FeaturesSerializer, GenreOfWorriesSerializer, ScaleOfWorriesSerializer, \
    WorriesToSympathizeSerializer, MeSerializer
from chat.consumers import ChatConsumer
from chat.models import Room
from chat.serializers import RoomSerializer
from fullfii.db.account import get_all_accounts, increment_num_of_thunks
from account.models import Feature, GenreOfWorries, ScaleOfWorries, WorriesToSympathize, Account, Plan, Iap, IapStatus
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
    permission_classes = (permissions.AllowAny,)
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
        rooms = Room.objects\
            .filter(Q(request_user=request.user, response_user=target_user) | Q(request_user=target_user, response_user=request.user))\
            .exclude(is_end_request=True, is_end_response=True)
        if not rooms.exists():
            room = Room(
                id=room_id,
                request_user=request.user,
                response_user=target_user,
            )
            room.save()
        else:
            if rooms.first().is_end:
                return Response({'type': 'conflict_end', 'message': 'the room already exists'}, status=status.HTTP_409_CONFLICT)
            else:
                return Response({'type': 'conflict', 'message': 'the room already exists'}, status=status.HTTP_409_CONFLICT)

        # set notification to target user
        NotificationConsumer.send_notification(recipient=target_user, subject=request.user, notification_type=NotificationType.TALK_REQUEST, reference_id=room_id)

        target_user_data = UserSerializer(target_user).data
        return Response({'room_id': room_id, 'target_user': target_user_data}, status=status.HTTP_200_OK)


talkRequestAPIView = TalkRequestAPIView.as_view()


class TalkAPIView(views.APIView):
    def validate_request_user(self, request, room):
        # check if the request.user is a room request user
        if request.user.id != room.request_user.id:
            return Response({'type': 'conflict', 'message': "you are not the room's request user."}, status=status.HTTP_409_CONFLICT)

    def validate_room_member(self, request, room):
        # check if the request.user is a room member
        if request.user.id != room.request_user.id and request.user.id != room.response_user.id:
            return Response({'type': 'conflict', 'message': 'you are not the room member.'}, status=status.HTTP_409_CONFLICT)


class CancelTalkAPIView(TalkAPIView):
    def post(self, request, *args, **kwargs):
        room_id = self.kwargs.get('room_id')
        room = get_object_or_404(Room, id=room_id)

        error_response = self.validate_request_user(request, room)
        if error_response:
            return error_response

        if room.is_start:
            return Response({'status': 'conflict_room_has_started', 'message': 'the room has already started.'}, status=status.HTTP_409_CONFLICT)

        request_user = request.user
        response_user = room.response_user

        # delete room
        room.delete()

        # set notification to target user
        NotificationConsumer.send_notification(recipient=response_user, subject=request_user, notification_type=NotificationType.CANCEL_TALK_REQUEST_TO_RES, reference_id=room_id)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


cancelTalkAPIView = CancelTalkAPIView.as_view()


class EndTalkAPIView(TalkAPIView):
    def post(self, request, *args, **kwargs):
        room_id = self.kwargs.get('room_id')
        room = get_object_or_404(Room, id=room_id)

        error_response = self.validate_room_member(request, room)
        if error_response:
            return error_response

        is_first_time = not room.is_end_request and not room.is_end_response

        # end talk for the first time
        if is_first_time:
            room.is_end = True
            room.ended_at = timezone.now()

        # turn on is_end_(req or res)
        if request.user.id == room.request_user.id:
            room.is_end_request = True
        else:
            room.is_end_response = True
        room.save()

        # send end talk
        if is_first_time:
            ChatConsumer.send_end_talk(room_id, sender_id=request.user.id)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


endTalkAPIView = EndTalkAPIView.as_view()


class CloseTalkAPIView(TalkAPIView):
    def post(self, request, *args, **kwargs):
        room_id = self.kwargs.get('room_id')
        has_thunks = bool(request.data['has_thunks'])
        room = get_object_or_404(Room, id=room_id)

        error_response = self.validate_room_member(request, room)
        if error_response:
            return error_response

        # check which request or response
        if request.user.id == room.request_user.id:
            is_request_user = True
            target_user = room.response_user
        else:
            is_request_user = False
            target_user = room.request_user

        # send thunks
        if has_thunks:
            increment_num_of_thunks(target_user)

        # turn on is_closed
        if is_request_user:
            room.is_closed_request = True
        else:
            room.is_closed_response = True

        # close room
        if room.is_closed_request and room.is_closed_response:
            room.delete()
        else:
            room.save()
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


closeTalkAPIView = CloseTalkAPIView.as_view()


class TalkInfoAPIView(views.APIView):
    def get(self, request, *args, **kwargs):
        # send objects
        rooms_i_sent = Room.objects.filter(is_start=False, request_user__id=request.user.id)
        rooms_i_sent_data = RoomSerializer(rooms_i_sent, many=True, context={'me': request.user}).data

        # in objects
        rooms_i_received = Room.objects.filter(is_start=False, response_user_id=request.user.id)
        rooms_i_received_data = RoomSerializer(rooms_i_received, many=True, context={'me': request.user}).data

        # talking rooms
        talking_rooms = Room.objects.filter(Q(request_user__id=request.user.id) | Q(response_user_id=request.user.id), is_start=True, is_end=False)
        talking_room_ids = [str(talking_room.id) for talking_room in talking_rooms]

        # end rooms and end time out rooms
        all_end_rooms = Room.objects.filter(Q(request_user__id=request.user.id, is_end_request=False) | Q(response_user_id=request.user.id, is_end_response=False), is_end=True)

        end_rooms = all_end_rooms.filter(is_time_out=False)
        end_room_ids = [str(end_room.id) for end_room in end_rooms]

        end_time_out_rooms = all_end_rooms.filter(is_time_out=True)
        end_time_out_room_ids = [str(end_time_out_room.id) for end_time_out_room in end_time_out_rooms]

        return Response({
            'send_objects': rooms_i_sent_data,
            'in_objects': rooms_i_received_data,
            'talking_room_ids': talking_room_ids,
            'end_room_ids': end_room_ids,
            'end_time_out_room_ids': end_time_out_room_ids,
        }, status=status.HTTP_200_OK)


talkInfoAPIView = TalkInfoAPIView.as_view()


class PurchaseProductAPIView(views.APIView):
    def post(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        receipt = request.data['receipt']

        # verifyReceipt
        if not product_id in Plan.values:
            return Response({'type': 'not_found', 'message': "not found plan"}, status=status.HTTP_404_NOT_FOUND)

        post_data = {
            'receipt-data': receipt,
            'password': fullfii.IAP_SHARED_SECRET,
            'exclude-old-transactions': True,
        }
        res = requests.post(fullfii.IAP_STORE_API_URL, json=post_data)
        res_json = res.json()

        if res_json['status'] == 21007:  # sandbox
            res = requests.post(fullfii.IAP_STORE_API_URL_SANDBOX, json=post_data)
            res_json = res.json()

        print(res_json)

        if res_json['status'] != 0:
            return Response({'type': 'failed_verify_receipt', 'message': "bad status"}, status=status.HTTP_409_CONFLICT)
        if res_json['receipt']['bundle_id'] != fullfii.BUNDLE_ID:
            return Response({'type': 'failed_verify_receipt', 'message': "bad bundle ID"}, status=status.HTTP_409_CONFLICT)
        if Iap.objects.filter(original_transaction_id=res_json['latest_receipt_info'][0]['original_transaction_id']).exists():
            return Response({'type': 'failed_verify_receipt', 'message': "the original transaction ID already exists"}, status=status.HTTP_409_CONFLICT)
        if Iap.objects.filter(transaction_id=res_json['latest_receipt_info'][0]['transaction_id']).exists():
            return Response({'type': 'failed_verify_receipt', 'message': "the transaction ID already exists"}, status=status.HTTP_409_CONFLICT)

        Iap.objects.create(
            original_transaction_id=res_json['latest_receipt_info'][0]['original_transaction_id'],
            transaction_id=res_json['latest_receipt_info'][0]['transaction_id'],
            user=request.user,
            receipt=res_json['latest_receipt'],
            expires_date=res_json['expires_date'],
            plan=IapStatus.SUBSCRIPTION
        )
        request.user.plan = product_id
        request.user.save()
        return Response({'status': 'success', 'profile': MeSerializer(request.user).data}, status=status.HTTP_200_OK)

purchaseProductAPIView = PurchaseProductAPIView.as_view()


class NoticeFromAppStoreAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        print(request.data)
        n_type = request.data['notification_type']
        if n_type == 'DID_CHANGE_RENEWAL_STATUS':
            print('aaaaaaaaaaaaaaaaaaaaaaaa')
            transaction_id = ''
            if 'latest_receipt_info' in request.data:
                print('bbbbbbbbbbbbbbbbbbbb')
                transaction_id = request.data['latest_receipt_info']['transaction_id']
            elif 'latest_expired_receipt_info' in request.data:
                print('cccccccccccccccccccccc')
                transaction_id = request.data['latest_expired_receipt_info']['transaction_id']

            users = Account.objects.filter(original_transaction_id=transaction_id)
            if users.exists():
                print('fffffffffffffffffffff')
                user = users.first()
                product_id = request.data['auto_renew_product_id']
                user.plan = Plan(product_id)
                user.save()

        return Response(status=status.HTTP_200_OK)


noticeFromAppStoreAPIView = NoticeFromAppStoreAPIView.as_view()
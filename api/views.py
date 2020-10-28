import uuid
from django.db.models import Q
from rest_framework import views, status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
import fullfii
from account.serializers import UserSerializer, FeaturesSerializer, GenreOfWorriesSerializer, ScaleOfWorriesSerializer, MeSerializer
from chat.consumers import ChatConsumer
from chat.models import Room
from chat.serializers import RoomSerializer
from fullfii.db.account import get_all_accounts, increment_num_of_thunks, update_iap
from account.models import Feature, GenreOfWorries, ScaleOfWorries, Account, Plan, Iap, IapStatus
from fullfii.lib.iap import verify_receipt_at_first
from fullfii.lib.support import cvt_tz_str_to_datetime
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
        return Response({
            'features': features_obj,
            'genre_of_worries': genre_of_worries_obj,
            'scale_of_worries': scale_of_worries_obj,
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

            viewable_users = fullfii.get_viewable_accounts(request.user, is_exclude_me=True)
            if genre_of_worries.exists():
                users = viewable_users.filter(genre_of_worries=genre_of_worries.first())
            else:
                users = viewable_users
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


class BlockAPIView(views.APIView):
    def patch(self, request, *args, **kwargs):
        will_block_user_id = self.kwargs.get('user_id')
        will_block_user = get_object_or_404(Account, id=will_block_user_id)

        if request.user.blocked_accounts.all().filter(id=will_block_user.id).exists():
            return Response({'type': 'have_already_blocked', 'message': 'すでに{}さんはブロックされています。'.format(will_block_user.username)}, status=status.HTTP_409_CONFLICT)
        else:
            request.user.blocked_accounts.add(will_block_user)
            return Response(status=status.HTTP_200_OK)


blockAPIView = BlockAPIView.as_view()


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

        fullfii.end_talk(room, is_first_time, request.user)
        me = fullfii.change_status_of_talk(room, user_id=request.user.id)
        me_data = MeSerializer(me).data if me is not None else None

        if is_first_time:
            # send end talk
            ChatConsumer.send_end_talk(room_id, sender_id=request.user.id)
        return Response({'status': 'success', 'profile': me_data}, status=status.HTTP_200_OK)


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

        # verify receipt
        response = verify_receipt_at_first(product_id, receipt, request.user)
        return response

purchaseProductAPIView = PurchaseProductAPIView.as_view()


class RestoreProductAPIView(views.APIView):
    def post(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        receipt = request.data['receipt']

        # verify receipt
        response = verify_receipt_at_first(product_id, receipt, request.user, is_restore=True)
        return response

restoreProductAPIView = RestoreProductAPIView.as_view()


class NoticeFromAppStoreAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        n_type = request.data['notification_type']
        if n_type == 'DID_RECOVER':
            iaps = Iap.objects.filter(original_transaction_id=request.data['latest_receipt_info']['original_transaction_id'])
            if iaps.exists():
                iap = iaps.first()
                if request.data['auto_renew_status'] == 'true':
                    update_iap(
                        iap=iap,
                        transaction_id=request.data['latest_receipt_info']['transaction_id'],
                        receipt=request.data['latest_receipt'],
                        expires_date=cvt_tz_str_to_datetime(request.data['latest_receipt_info']['expires_date_formatted']),
                        status=IapStatus.SUBSCRIPTION,
                    )
                    iap.user.plan = request.data['latest_receipt_info']['product_id']
                    iap.user.save()

        elif n_type == 'DID_CHANGE_RENEWAL_STATUS':
            if 'latest_receipt_info' in request.data:
                original_transaction_id = request.data['latest_receipt_info']['original_transaction_id']
            elif 'unified_receipt' in request.data:
                original_transaction_id = request.data['unified_receipt']['latest_receipt_info'][0]['original_transaction_id']
            else:
                original_transaction_id = ''

            iaps = Iap.objects.filter(original_transaction_id=original_transaction_id)
            if iaps.exists():
                iap = iaps.first()
                # 自動更新成功
                # if request.data['auto_renew_status'] == 'true' and not Iap.objects.filter(transaction_id=request.data['latest_receipt_info']['transaction_id']).exists():
                #     update_iap(
                #         iap=iap,
                #         transaction_id=request.data['latest_receipt_info']['transaction_id'],
                #         receipt=request.data['latest_receipt'],
                #         expires_date=cvt_tz_str_to_datetime(request.data['latest_receipt_info']['expires_date_formatted']),
                #         status=IapStatus.SUBSCRIPTION,
                #     )
                #     iap.user.plan = request.data['auto_renew_product_id']
                #     iap.user.save()
                # 自動更新失敗状態で期限が切れた
                # TODO ユーザが購読終了した時点で、　送られてくるから致命的バグ
                # if request.data['auto_renew_status'] == 'false' and iap.status != IapStatus.EXPIRED:
                #     update_iap(
                #         iap=iap,
                #         status=IapStatus.EXPIRED,
                #     )
                #     iap.user.plan = Plan.FREE
                #     iap.user.save()

        return Response(status=status.HTTP_200_OK)


noticeFromAppStoreAPIView = NoticeFromAppStoreAPIView.as_view()

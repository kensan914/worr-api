from main.v4.consumers import NotificationConsumer
from account.models import Account, Gender
from django.db.models import Q
from rest_framework import views, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from chat.models import RoomV4
from chat.v4.serializers import RoomSerializer
from chat.v4.consumers import ChatConsumer
from fullfii.db.chat import get_created_rooms, get_participating_rooms


class TalkInfoAPIView(views.APIView):
    def get(self, request, *args, **kwargs):
        created_rooms = get_created_rooms(request.user)
        created_rooms_serializer = RoomSerializer(created_rooms, many=True)

        participating_rooms = get_participating_rooms(request.user)
        participating_rooms_serializer = RoomSerializer(participating_rooms, many=True)

        return Response(
            {
                "created_rooms": created_rooms_serializer.data,
                "participating_rooms": participating_rooms_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


talkInfoAPIView = TalkInfoAPIView.as_view()


class RoomsAPIView(views.APIView):
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        """
        10単位でroomを取得. クエリパラメータ"page"でページ指定.
        """
        _page = self.request.GET.get("page")
        page = int(_page) if _page is not None and _page.isdecimal() else 1

        rooms = RoomV4.objects.filter(
            is_active=True,
            is_end=False,
            owner__is_active=True,
        ).exclude(
            Q(owner=request.user)
            | Q(participants=request.user)
            | Q(id__in=request.user.hidden_rooms.all())
            | Q(id__in=request.user.blocked_rooms.all())
        )

        # my gender == 設定済み
        if request.user.gender != Gender.NOTSET and not request.user.is_secret_gender:
            # 異性非表示設定 & オーナー性別設定済 & オーナーと性別が異なる : 除外 (相手が異性非表示設定を設定していた場合, 同性別時のみ表示)
            rooms = rooms.filter(
                Q(is_exclude_different_gender=False)
                | Q(owner__is_secret_gender=True)
                | Q(owner__gender=Gender.NOTSET)
                | Q(owner__gender=request.user.gender)
            )
        # my gender == 未設定 or 秘密
        else:
            # 異性非表示設定 & オーナー性別設定済 : 除外 (相手が異性非表示設定を設定していた場合, 無条件で非表示)
            rooms = rooms.filter(
                Q(is_exclude_different_gender=False)
                | Q(owner__is_secret_gender=True)
                | Q(owner__gender=Gender.NOTSET)
            )

        # 自分と話しているユーザは非表示
        talking_member_ids = []
        created_rooms = get_created_rooms(request.user)
        for created_room in created_rooms:
            talking_member_ids += created_room.participants.values_list("id", flat=True)
        participating_rooms = get_participating_rooms(request.user)
        talking_member_ids += [
            participating_room.owner.id for participating_room in participating_rooms
        ]
        rooms = rooms.exclude(owner__in=talking_member_ids)

        # 凍結されていたら, 女性は表示しない
        if request.user.is_ban:
            rooms = rooms.exclude(
                owner__gender=Gender.FEMALE, owner__is_secret_gender=False
            )

        # ブロックしているユーザ, ブロックされているユーザを表示しない
        rooms = rooms.exclude(
            Q(owner__in=request.user.blocked_accounts.all())
            | Q(owner__in=request.user.block_me_accounts.all())
        )

        # to create id_list will be faster
        id_list = list(
            rooms[self.paginate_by * (page - 1) : self.paginate_by * page].values_list(
                "id", flat=True
            )
        )
        rooms = [rooms.get(id=pk) for pk in id_list]

        serializer = RoomSerializer(rooms, many=True)
        return Response(
            {"rooms": serializer.data, "has_more": not (len(rooms) < self.paginate_by)},
            status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        """
        roomを作成
        """
        # 既に会話中の作成ルームが存在した場合、中断
        if RoomV4.objects.filter(owner=request.user, is_end=False).exists():
            return Response(
                data={
                    "error": {
                        "alert": True,
                        "type": "conflict room post",
                        "title": "ルームを作成できませんでした",
                        "message": "ルームは1つまでしか作成できません。新しいルームを作成するためには、すでにある作成したルームを削除しましょう。",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        post_data = {"owner_id": request.user.id, **request.data}
        room_serializer = RoomSerializer(data=post_data)
        if room_serializer.is_valid():
            room_serializer.save()
            return Response(data=room_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                data=room_serializer.errors, status=status.HTTP_409_CONFLICT
            )


roomsAPIView = RoomsAPIView.as_view()


class RoomAPIView(views.APIView):
    def patch(self, request, *args, **kwargs):
        """
        roomを編集 (room作成者のみ, 既に参加者がいる場合編集禁止)
        """
        room_id = self.kwargs.get("room_id")
        room = get_object_or_404(RoomV4, id=room_id)

        # room作成者か
        if room.owner.id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 参加者がいるか
        if room.participants.count() > 0:
            return Response(
                data={
                    "error": {
                        "alert": True,
                        "type": "conflict room patch",
                        "title": "ルームを修正できませんでした",
                        "message": "このルームには既に参加者がいるため、ルームの修正はできません。",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        room_serializer = RoomSerializer(instance=room, data=request.data, partial=True)
        if room_serializer.is_valid():
            room_serializer.save()
            return Response(data=room_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                data=room_serializer.errors, status=status.HTTP_409_CONFLICT
            )

    def delete(self, request, *args, **kwargs):
        """
        roomを削除 (room作成者のみ)
        """
        room_id = self.kwargs.get("room_id")
        room = get_object_or_404(RoomV4, id=room_id)

        if room.owner.id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        validate_result_member_id = RoomLeftMembersAPIView.validate_member_id(
            request.user.id, room
        )
        if validate_result_member_id is not None:
            # validation error member_id
            return validate_result_member_id

        # left room
        room.left_members.add(request.user.id)
        RoomLeftMembersAPIView.check_and_end_room(room)

        # close room
        room.closed_members.add(request.user.id)
        RoomClosedMembersAPIView.check_and_deactive_room(room)

        return Response(status=status.HTTP_204_NO_CONTENT)


roomAPIView = RoomAPIView.as_view()


class RoomImagesAPIView(views.APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        """
        room imageをPOST
        """
        room_id = self.kwargs.get("room_id")
        room = get_object_or_404(RoomV4, id=room_id)

        if not "image" in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        request_data = {"image_src": request.data["image"]}
        room_serializer = RoomSerializer(instance=room, data=request_data, partial=True)
        if room_serializer.is_valid():
            room_serializer.save()
            return Response(data=RoomSerializer(room).data, status=status.HTTP_200_OK)
        else:
            return Response(
                data=room_serializer.errors, status=status.HTTP_409_CONFLICT
            )


roomImagesAPIView = RoomImagesAPIView.as_view()


class RoomParticipantsAPIView(views.APIView):
    @classmethod
    def validate_account_id(cls, _account_id, request):
        # ユーザが見つからない
        if not Account.objects.filter(id=_account_id).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 他のユーザをroom参加・退出させることはできない仕様 (現段階)
        if str(_account_id) != str(request.user.id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # success
        return

    def post(self, request, *args, **kwargs):
        """
        roomへの参加
        """
        room_id = self.kwargs.get("room_id")
        room = get_object_or_404(RoomV4, id=room_id)

        # 既に終了していた場合、中断
        if room.is_end:
            return Response(
                data={
                    "error": {
                        "alert": True,
                        "type": "conflict room participant post",
                        "title": "このルームは既に終了しています",
                        "message": "",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        # 既に参加ルームが存在した場合、中断
        if room.participants.filter(id=request.user.id).exists():
            return Response(
                data={
                    "error": {
                        "alert": True,
                        "type": "conflict room participant post",
                        "title": "あなたはすでにこのルームに参加しています",
                        "message": "参加ルーム一覧からトークを開始しましょう。",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        # 既に参加ルームが存在した場合、中断
        if RoomV4.objects.filter(participants=request.user, is_end=False).exists():
            return Response(
                data={
                    "error": {
                        "alert": True,
                        "type": "conflict room participant post",
                        "title": "既に参加しているルームを退室してください",
                        "message": "ルームにはひとつまでしか参加できません。",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        # 既に参加人数に達していた場合、中断
        if room.participants.count() >= room.max_num_participants:
            return Response(
                data={
                    "error": {
                        "alert": True,
                        "type": "conflict room participant post",
                        "title": f"このルームは既に参加人数が{room.max_num_participants}人を超えています。",
                        "message": f"",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        if not "account_id" in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        account_id = request.data["account_id"]

        validate_result = RoomParticipantsAPIView.validate_account_id(
            account_id, request
        )
        if validate_result is not None:
            return validate_result

        # owner自身は参加不可
        if str(account_id) == str(room.owner.id):
            return Response(status=status.HTTP_409_CONFLICT)

        room.participants.add(account_id)
        room.save()
        room_data = RoomSerializer(room).data

        # ownerへSOMEONE_PARTICIPATED通知
        NotificationConsumer.send_notification_someone_participated(
            room.owner.id,
            room_data,
            account_id,
            should_start=room.participants.count() == 1,  # 初めての参加者の場合, START_TALKを走らせる
        )

        return Response(data=room_data, status=status.HTTP_200_OK)


roomParticipantsAPIView = RoomParticipantsAPIView.as_view()


class RoomLeftMembersAPIView(views.APIView):
    @classmethod
    def validate_member_id(cls, _member_id, _room):
        # roomのメンバーではない
        if not (
            str(_room.owner.id) == str(_member_id)
            or _room.participants.filter(id=_member_id).exists()
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # success
        return

    @classmethod
    def check_and_end_room(cls, _room):
        # 参加者が1人までという現在の仕様により, 1人でも退室したらルームを終了する
        if not _room.is_end:
            # ルーム終了
            _room.is_end = True
            # メンバー全員にend chat通知
            if _room.participants.count() > 0:
                ChatConsumer.send_end_talk(_room.id, RoomSerializer(_room).data)
        _room.save()

    def post(self, request, *args, **kwargs):
        """
        メンバー(作成者含む)のroomからの退室.
        退室の定義：トークをすることはできないが, フロントにroom情報は保持していてトークが完全に終了した状態ではない.
        """
        room_id = self.kwargs.get("room_id")
        room = get_object_or_404(RoomV4, id=room_id)

        if not "account_id" in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        account_id = request.data["account_id"]

        validate_result_account_id = RoomParticipantsAPIView.validate_account_id(
            account_id, request
        )
        if validate_result_account_id is not None:
            # validation error account_id
            return validate_result_account_id

        validate_result_member_id = RoomLeftMembersAPIView.validate_member_id(
            account_id, room
        )
        if validate_result_member_id is not None:
            # validation error member_id
            return validate_result_member_id

        room.left_members.add(account_id)
        RoomLeftMembersAPIView.check_and_end_room(room)

        # send 退室メッセ―ジ
        leave_message = (
            request.data["leave_message"] if "leave_message" in request.data else None
        )
        if type(leave_message) == str and leave_message and len(leave_message) <= 1000:
            ChatConsumer.send_leave_message(
                room_id=room_id, text=leave_message, sender=request.user
            )

        return Response(data=RoomSerializer(room).data, status=status.HTTP_200_OK)


roomLeftMembersAPIView = RoomLeftMembersAPIView.as_view()


class RoomClosedMembersAPIView(views.APIView):
    @classmethod
    def check_and_deactive_room(cls, _room):
        # 全員クローズしたら, ルームを非活性
        if _room.closed_members.count() == _room.participants.count() + 1:  # 1: 作成者数
            # ルーム非活性
            _room.is_active = False
        _room.save()

    def post(self, request, *args, **kwargs):
        """
        メンバー(作成者含む)のroomのクローズ.
        クローズの定義：フロントからroom情報を完全に削除して相談を完全に終了すること.
        """
        room_id = self.kwargs.get("room_id")
        room = get_object_or_404(RoomV4, id=room_id)

        if not "account_id" in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        account_id = request.data["account_id"]

        validate_result_account_id = RoomParticipantsAPIView.validate_account_id(
            account_id, request
        )
        if validate_result_account_id is not None:
            # validation error account_id
            return validate_result_account_id

        validate_result_member_id = RoomLeftMembersAPIView.validate_member_id(
            account_id, room
        )
        if validate_result_member_id is not None:
            # validation error member_id
            return validate_result_member_id

        room.closed_members.add(account_id)
        RoomClosedMembersAPIView.check_and_deactive_room(room)

        return Response(status=status.HTTP_204_NO_CONTENT)


roomClosedMembersAPIView = RoomClosedMembersAPIView.as_view()

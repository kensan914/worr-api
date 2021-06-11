from django.utils import timezone
from django.db import transaction
from rest_framework import views, permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler


from account.v4.serializers import (
    SignupSerializer,
    AuthUpdateSerializer,
    MeSerializer,
    PatchMeSerializer,
    ProfileImageSerializer,
)
from account.models import Gender, ProfileImage, Account, Job
from chat.models import RoomV4


class SignupAPIView(views.APIView):
    """
    required req data ====> {'username', 'password'} + α(gender, job)
    response ====> {'me': {(account data)}, 'token': '(token)'}

    genre_of_worries等profile params系は、key, value, labelを持つobjectのリストを渡す。
    gender等text choices系は、key(value)のstringを渡す。(ex. "female")
    """

    permission_classes = (permissions.AllowAny,)

    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            me = Account.objects.filter(id=serializer.data["id"]).first()
            if me is not None:
                # # profile params更新
                # _me = MeAPIView.patch_params(request.data, me)
                # if _me is not None:
                #     me = _me

                email_serializer = AuthUpdateSerializer(
                    me, data={"email": "{}@fullfii.com".format(me.id)}, partial=True
                )
                if email_serializer.is_valid():
                    email_serializer.save()
                    # token付与
                    if me.check_password(request.data["password"]):
                        payload = jwt_payload_handler(me)
                        token = jwt_encode_handler(payload)
                        data = {
                            "me": MeSerializer(me).data,
                            "token": str(token),
                        }

                        # fullfii.on_signup_success(me)
                        return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


signupAPIView = SignupAPIView.as_view()


class MeAPIView(views.APIView):
    Serializer = MeSerializer
    PatchSerializer = PatchMeSerializer

    def get(self, request):
        # ログイン処理(loggedin_atの更新)
        request.user.loggedin_at = timezone.now()
        request.user.save()

        serializer = self.Serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        # job filter
        if "job" in request.data and not request.data["job"] in Job.values:
            return Response(status=status.HTTP_409_CONFLICT)

        serializer = self.PatchSerializer(
            instance=request.user, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                self.Serializer(request.user).data, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request.user.is_active = False
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


meAPIView = MeAPIView.as_view()


class ProfileImageAPIView(views.APIView):
    parser_classes = [MultiPartParser]
    Serializer = MeSerializer

    def post(self, request, *args, **kwargs):
        request_data = {"picture": request.data["image"], "user": request.user.id}
        if ProfileImage.objects.filter(user=request.user).exists():
            profile_image_serializer = ProfileImageSerializer(
                instance=request.user.image, data=request_data
            )
        else:
            profile_image_serializer = ProfileImageSerializer(data=request_data)

        if profile_image_serializer.is_valid():
            profile_image_serializer.save()
            return Response(
                self.Serializer(request.user).data, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                profile_image_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


profileImageAPIView = ProfileImageAPIView.as_view()


class ProfileParamsAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def get_profile_params(self, serializer, model):
        record_obj = {}
        for record in model.objects.all():
            record_data = serializer(record).data
            record_obj[record_data["key"]] = record_data
        return record_obj

    def get_text_choices(self, text_choices):
        text_choices_obj = {}

        tc = text_choices
        for name, value, label in zip(tc.names, tc.values, tc.labels):
            text_choices_obj[value] = {
                "key": value,
                "name": name,
                "label": label,
            }
        return text_choices_obj

    def get(self, request, *args, **kwargs):
        # profile params
        # genre_of_worries_obj = self.get_profile_params(
        #     GenreOfWorriesSerializer, GenreOfWorries)

        # text choices
        gender_obj = self.get_text_choices(Gender)
        job_obj = self.get_text_choices(Job)

        return Response(
            {
                # 'genre_of_worries': genre_of_worries_obj,
                "gender": gender_obj,
                "job": job_obj,
            },
            status.HTTP_200_OK,
        )


profileParamsAPIView = ProfileParamsAPIView.as_view()


class GenderAPIView(views.APIView):
    def put(self, request, *args, **kwargs):
        expected_keys = ["female", "male", "secret"]
        if "key" in request.data and request.data["key"] in expected_keys:
            if request.data["key"] == "female" and request.user.gender != Gender.MALE:
                request.user.gender = Gender.FEMALE
                request.user.is_secret_gender = False
            elif request.data["key"] == "male" and request.user.gender != Gender.FEMALE:
                request.user.gender = Gender.MALE
                request.user.is_secret_gender = False
            elif request.data["key"] == "secret":
                request.user.is_secret_gender = True
            request.user.save()
            return Response(
                {
                    "me": MeSerializer(request.user).data,
                },
                status.HTTP_200_OK,
            )
        else:
            return Response(status=status.HTTP_409_CONFLICT)


genderAPIView = GenderAPIView.as_view()


class UsersAPIView(views.APIView):
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        pass  # TODO: 必要性不明
        # user_id = self.kwargs.get('user_id')

        # if user_id:
        #     users = get_all_accounts(me=request.user).filter(id=user_id)
        #     if users.exists():
        #         return Response(UserSerializer(users.first()).data, status=status.HTTP_200_OK)
        #     else:
        #         return Response({'error': 'not found user'}, status=status.HTTP_404_NOT_FOUND)
        # else:
        #     _page = self.request.GET.get('page')
        #     page = int(_page) if _page is not None and _page.isdecimal() else 1
        #     genre = self.request.GET.get('genre')
        #     genre_of_worries = GenreOfWorries.objects.filter(value=genre)

        #     viewable_users = fullfii.get_viewable_accounts(
        #         request.user, is_exclude_me=True)
        #     if genre_of_worries.exists():
        #         users = viewable_users.filter(
        #             genre_of_worries=genre_of_worries.first())
        #     else:
        #         users = viewable_users
        #     users = users[self.paginate_by *
        #                   (page - 1): self.paginate_by * page]
        #     users_data = UserSerializer(users, many=True).data

        #     # paginate_byをクライアントで管理しない手法, v2に見送り
        #     # res_data = {
        #     #     'has_more': len(users_data) >= self.paginate_by,
        #     #     'users': users_data,
        #     # }
        #     # return Response(res_data, status=status.HTTP_200_OK)
        #     return Response(users_data, status=status.HTTP_200_OK)


usersAPIView = UsersAPIView.as_view()


class BlockAPIView(views.APIView):
    def patch(self, request, *args, **kwargs):
        will_block_user_id = self.kwargs.get("user_id")
        will_block_user = get_object_or_404(Account, id=will_block_user_id)

        if request.user.blocked_accounts.all().filter(id=will_block_user.id).exists():
            return Response(
                {
                    "type": "have_already_blocked",
                    "message": "すでに{}さんはブロックされています。".format(will_block_user.username),
                },
                status=status.HTTP_409_CONFLICT,
            )
        else:
            request.user.blocked_accounts.add(will_block_user)
            request.user.save()
            return Response(status=status.HTTP_200_OK)


blockAPIView = BlockAPIView.as_view()


class HiddenRoomsAPIView(views.APIView):
    def patch(self, request, *args, **kwargs):
        """
        roomの非表示
        """
        if not "room_id" in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        room_id = request.data["room_id"]
        room = get_object_or_404(RoomV4, id=room_id)

        # 自身がオーナーのルームは非表示できない
        if str(request.user.id) == str(room.owner.id):
            return Response(status=status.HTTP_409_CONFLICT)

        request.user.hidden_rooms.add(room.id)
        request.user.save()
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        room非表示の全取り消し
        """
        request.user.hidden_rooms.clear()
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


hiddenRoomsAPIView = HiddenRoomsAPIView.as_view()


class BlockedRoomsAPIView(views.APIView):
    def patch(self, request, *args, **kwargs):
        """
        roomのブロック
        """
        if not "room_id" in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        room_id = request.data["room_id"]
        room = get_object_or_404(RoomV4, id=room_id)

        # 自身がオーナーのルームはブロックできない
        if str(request.user.id) == str(room.owner.id):
            return Response(status=status.HTTP_409_CONFLICT)

        request.user.blocked_rooms.add(room.id)
        request.user.save()
        return Response(status=status.HTTP_200_OK)


blockedRoomsAPIView = BlockedRoomsAPIView.as_view()

from django.db import transaction
from rest_framework import views, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

import fullfii
from account.serializers import SignupSerializer, MeSerializer, PatchMeSerializer, ProfileImageSerializer, \
    FeaturesSerializer, GenreOfWorriesSerializer, ScaleOfWorriesSerializer, AuthUpdateSerializer
from account.models import ProfileImage, Feature, GenreOfWorries, ScaleOfWorries, IntroStep, Account
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler

from account.v2.serializers import MeV2Serializer


class SignupAPIView(views.APIView):
    """
    required req data ====> {'username', 'password'} + α(genre_of_worries, gender, )
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
            me = Account.objects.filter(id=serializer.data['id']).first()
            if me is not None:
                # profile params更新
                _me = MeAPIView.patch_params(request.data, me)
                if _me is not None:
                    me = _me

                email_serializer = AuthUpdateSerializer(
                    me, data={'email': '{}@fullfii.com'.format(me.id)}, partial=True)
                if email_serializer.is_valid():
                    email_serializer.save()
                    # token付与
                    if me.check_password(request.data['password']):
                        payload = jwt_payload_handler(me)
                        token = jwt_encode_handler(payload)
                        data = {
                            'me': MeV2Serializer(me).data,
                            'token': str(token),
                        }

                        fullfii.on_signup_success(me)
                        return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


signupAPIView = SignupAPIView.as_view()


class AuthUpdateAPIView(views.APIView):
    def patch(self, request, *args, **kwargs):
        if 'email' in request.data:
            email = request.data['email']
            serializer = AuthUpdateSerializer(
                request.user, data={'email': email}, partial=True)
            if serializer.is_valid():
                serializer.save()
                payload = jwt_payload_handler(request.user)
                token = jwt_encode_handler(payload)
                return Response({'profile': serializer.data, 'token': token}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'password' in request.data and 'prev_password' in request.data:
            password = request.data['password']
            prev_password = request.data['prev_password']
            if not request.user.check_password(prev_password):
                return Response({'error': ['パスワードが正しくありません。']}, status=status.HTTP_400_BAD_REQUEST)
            serializer = AuthUpdateSerializer(
                request.user, data={'password': password}, partial=True)
            if serializer.is_valid():
                serializer.save()
                payload = jwt_payload_handler(request.user)
                token = jwt_encode_handler(payload)
                return Response({'profile': serializer.data, 'token': token}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


authUpdateAPIView = AuthUpdateAPIView.as_view()


class MeAPIView(views.APIView):
    Serializer = MeSerializer
    PatchSerializer = PatchMeSerializer

    def get(self, request):
        serializer = self.Serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        me = self.patch_params(request.data, request.user)
        if me is not None:
            return Response(self.Serializer(me).data, status=status.HTTP_200_OK)

        # result_patch_intro_step = self.patch_intro_step(request.data, request.user)

        serializer = self.PatchSerializer(
            instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(self.Serializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @classmethod
    def patch_params(cls, request_data, request_user):
        _request_user = None
        for patch_type in list(request_data.keys()):
            if patch_type in ['features', 'genre_of_worries', 'scale_of_worries']:
                if patch_type == 'features':
                    record = cls._patch_params(
                        request_data, FeaturesSerializer, Feature, patch_type, many=True)
                    if record is not None:
                        request_user.features.set(record)
                elif patch_type == 'genre_of_worries':
                    record = cls._patch_params(
                        request_data, GenreOfWorriesSerializer, GenreOfWorries, patch_type, many=True)
                    if record is not None:
                        request_user.genre_of_worries.set(record)
                elif patch_type == 'scale_of_worries':
                    record = cls._patch_params(
                        request_data, ScaleOfWorriesSerializer, ScaleOfWorries, patch_type, many=True)
                    if record is not None:
                        request_user.scale_of_worries.set(record)
                request_user.save()
                _request_user = request_user

        return _request_user

    @classmethod
    def _patch_params(cls, request_data, serializer, model, patch_type, many=False):
        if not request_data[patch_type]:
            return request_data[patch_type]
        data = serializer(request_data[patch_type], many=many).data
        if not many:
            if model.objects.get(key=data.key).exists():
                record = model.objects.get(key=data.key)
                return record
            else:
                # sign upが中断されるのを防ぐ
                # raise ValidationError('パラメータが見つかりません')
                return
        else:
            record = model.objects.filter(
                key__in=[part_of_data['key'] for part_of_data in data])
            if not record:
                # raise ValidationError('パラメータが見つかりません')
                return
            else:
                return record

    def patch_intro_step(self, request_data, request_user):
        patch_type = list(request_data.keys())[0]
        if patch_type in ['intro_step']:
            if patch_type == 'intro_step':
                data = request_data[patch_type]
                intro_step_objects = []
                for key, val in data.items():
                    if val:
                        intro_step = IntroStep.objects.filter(key=key)
                        if not intro_step.exists():
                            raise ValidationError('不正な値です')
                        intro_step_objects.append(intro_step.first())
                request_user.intro_step.set(intro_step_objects)
                request_user.save()

    def delete(self, request):
        request.user.is_active = False
        request.user.email = '{}-deleted'.format(request.user.id)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


meAPIView = MeAPIView.as_view()


class ProfileImageAPIView(views.APIView):
    parser_classes = [MultiPartParser]
    Serializer = MeSerializer

    def post(self, request, *args, **kwargs):
        request_data = {
            'picture': request.data['image'], 'user': request.user.id}
        if ProfileImage.objects.filter(user=request.user).exists():
            profile_image_serializer = ProfileImageSerializer(
                instance=request.user.image, data=request_data)
        else:
            profile_image_serializer = ProfileImageSerializer(
                data=request_data)

        if profile_image_serializer.is_valid():
            profile_image_serializer.save()
            return Response(self.Serializer(request.user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(profile_image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


profileImageAPIView = ProfileImageAPIView.as_view()

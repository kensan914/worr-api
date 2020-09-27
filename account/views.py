from django.db import transaction
from rest_framework import views, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from account.serializers import SignupSerializer, MeSerializer, PatchMeSerializer, ProfileImageSerializer, \
    StatusSerializer, FeaturesSerializer, GenreOfWorriesSerializer, ScaleOfWorriesSerializer, \
    WorriesToSympathizeSerializer
from account.models import ProfileImage, Status, Feature, GenreOfWorries, ScaleOfWorries, WorriesToSympathize, Plan


class SignupAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

signupAPIView = SignupAPIView.as_view()


class MeAPIView(views.APIView):
    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        result_patch_params = self.patch_params(request.data, request.user)
        if result_patch_params is not None:
            return result_patch_params

        serializer = PatchMeSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(MeSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch_params(self, request_data, request_user):
        patch_type = list(request_data.keys())[0]
        if patch_type in ['status', 'plan', 'features', 'genre_of_worries', 'scale_of_worries', 'worries_to_sympathize']:
            if patch_type == 'status':
                record = self._patch_params(request_data, StatusSerializer, Status, patch_type)
                request_user.status = record
            elif patch_type == 'plan':
                pass
                # TODO
                # record = self._patch_params(request_data, PlanSerializer, Plan, patch_type)
                # request_user.plan = record
            elif patch_type == 'features':
                record = self._patch_params(request_data, FeaturesSerializer, Feature, patch_type, many=True)
                request_user.features.set(record)
            elif patch_type == 'genre_of_worries':
                record = self._patch_params(request_data, GenreOfWorriesSerializer, GenreOfWorries, patch_type, many=True)
                request_user.genre_of_worries.set(record)
            elif patch_type == 'scale_of_worries':
                record = self._patch_params(request_data, ScaleOfWorriesSerializer, ScaleOfWorries, patch_type, many=True)
                request_user.scale_of_worries.set(record)
            elif patch_type == 'worries_to_sympathize':
                record = self._patch_params(request_data, WorriesToSympathizeSerializer, WorriesToSympathize, patch_type, many=True)
                request_user.worries_to_sympathize.set(record)

            request_user.save()
            return Response(MeSerializer(request_user).data, status=status.HTTP_200_OK)

    def _patch_params(self, request_data, serializer, model, patch_type, many=False):
        if not request_data[patch_type]:
            return request_data[patch_type]
        data = serializer(request_data[patch_type], many=many).data
        if not many:
            if model.objects.get(key=data.key).exists():
                record = model.objects.get(key=data.key)
                return record
            else:
                raise ValidationError('パラメータが見つかりません')
        else:
            record = model.objects.filter(key__in=[part_of_data['key'] for part_of_data in data])
            if not record:
                raise ValidationError('パラメータが見つかりません')
            else:
                return record


meAPIView = MeAPIView.as_view()


class ProfileImageAPIView(views.APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        request_data = {'picture': request.data['image'], 'user': request.user.id}
        if ProfileImage.objects.filter(user=request.user).exists():
            profile_image_serializer = ProfileImageSerializer(instance=request.user.image, data=request_data)
        else:
            profile_image_serializer = ProfileImageSerializer(data=request_data)

        if profile_image_serializer.is_valid():
            profile_image_serializer.save()
            return Response(MeSerializer(request.user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(profile_image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


profileImageAPIView = ProfileImageAPIView.as_view()

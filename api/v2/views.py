from rest_framework import views, status, permissions
from rest_framework.response import Response
from account.models import GenreOfWorries, Gender, Job
from account.serializers import GenreOfWorriesSerializer
from account.v2.serializers import MeV2Serializer, PatchMeV2Serializer
from account.views import MeAPIView, ProfileImageAPIView


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
        genre_of_worries_obj = self.get_profile_params(GenreOfWorriesSerializer, GenreOfWorries)

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

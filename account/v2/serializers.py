import os
from rest_framework import serializers
from account.models import Account, ProfileImage, Plan, Gender, Job
from account.serializers import GenreOfWorriesSerializer
from fullfii.lib.constants import BASE_URL


class UserV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'gender', 'is_secret_gender', 'job', 'introduction',
                  'num_of_thunks', 'genre_of_worries', 'image', 'me')

    name = serializers.CharField(source='username')
    gender = serializers.SerializerMethodField()
    job = serializers.SerializerMethodField()
    genre_of_worries = GenreOfWorriesSerializer(many=True)
    image = serializers.SerializerMethodField()
    me = serializers.BooleanField(default=False)

    def get_gender(self, obj):
        if obj.gender in Gender.values:
            g = Gender(obj.gender)
        else:
            g = Gender.NOTSET
        return {'key': g.value, 'name': g.name, 'label': g.label}

    def get_job(self, obj):
        if obj.job in Job.values:
            j = Job(obj.job)
        else:
            j = Job.SECRET
        return {'key': j.value, 'name': j.name, 'label': j.label}

    def get_image(self, obj):
        if ProfileImage.objects.filter(user=obj).exists():
            image_url = obj.image.picture.medium.url
            return os.path.join(BASE_URL, image_url if image_url[0] != '/' else image_url[1:])


class MeV2Serializer(UserV2Serializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'gender', 'is_secret_gender', 'job', 'introduction', 'num_of_thunks',
                  'date_joined', 'plan', 'genre_of_worries', 'image', 'me', 'can_talk_heterosexual', 'device_token')

    plan = serializers.SerializerMethodField()
    me = serializers.BooleanField(default=True)

    def get_plan(self, obj):
        return {'key': Plan(obj.plan).value, 'label': Plan(obj.plan).label}


class PatchMeV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('name', 'introduction',
                  'can_talk_heterosexual', 'device_token')

    name = serializers.CharField(source='username')

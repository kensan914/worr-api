import os
from django.contrib.auth import password_validation as validators
from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer, jwt_payload_handler, jwt_encode_handler
import fullfii
from account.models import Account, ProfileImage, Plan, Status, Feature, GenreOfWorries, ScaleOfWorries, StatusColor, \
    Gender, IntroStep, Job


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileImage
        fields = ('picture', 'user')


class FeaturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        exclude = ['id']


class GenreOfWorriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenreOfWorries
        exclude = ['id']


class ScaleOfWorriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScaleOfWorries
        exclude = ['id']


class AuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'username', 'password', 'gender', 'job')

    password = serializers.CharField(write_only=True, min_length=8, max_length=30)


class SignupSerializer(AuthSerializer):
    def validate_password(self, data):
        validators.validate_password(password=data, user=Account)
        return data

    def create(self, validated_data):
        return Account.objects.create_user(**validated_data)


class AuthUpdateSerializer(AuthSerializer):
    class Meta:
        model = Account
        fields = ('id', 'username', 'password', 'gender', 'job', 'email')

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        else:
            instance = super().update(instance, validated_data)
        instance.save()
        return instance


class LoginSerializer(JSONWebTokenSerializer):
    username_field = 'email'
    def validate(self, attrs):
        password = attrs.get('password')
        account = Account.objects.filter(email=attrs.get('email')).first()
        if account is not None:
            if account.email is None or password is None:
                raise serializers.ValidationError('メールアドレスもしくはパスワードが含まれていません。')
            if not account.check_password(password):
                raise serializers.ValidationError('メールアドレスもしくはパスワードが間違っています。')
            if not account.is_active:
                raise serializers.ValidationError('アカウントが無効になっています。')
            payload = jwt_payload_handler(account)
            token = jwt_encode_handler(payload)
            return {
                'token': token,
            }
        else:
            raise serializers.ValidationError('このメールアドレスを持ったアカウントは存在しません。')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'birthday', 'age', 'gender', 'job', 'introduction', 'num_of_thunks', 'status', 'features', 'genre_of_worries', 'scale_of_worries', 'image', 'me')

    name = serializers.CharField(source='username')
    birthday = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    job = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    features = FeaturesSerializer(many=True)
    genre_of_worries = GenreOfWorriesSerializer(many=True)
    scale_of_worries = ScaleOfWorriesSerializer(many=True)
    image = serializers.SerializerMethodField()
    me = serializers.BooleanField(default=False)

    def get_birthday(self, obj):
        if obj.birthday:
            return fullfii.generate_birthday(birthday=obj.birthday)
        else: return

    def get_age(self, obj):
        if obj.birthday:
            return fullfii.calc_age(birthday=obj.birthday)
        else: return '-'

    def get_gender(self, obj):
        if obj.gender in Gender.values:
            g = Gender(obj.gender)
        else:
            g = Gender.SECRET
        return {'key': g.value, 'name': g.name, 'label': g.label}

    def get_job(self, obj):
        if obj.job in Job.values:
            j = Job(obj.job)
        else:
            j = Job.SECRET
        return {'key': j.value, 'name': j.name, 'label': j.label}

    def get_status(self, obj):
        return {'key': Status(obj.status).value, 'label': Status(obj.status).label, 'color': StatusColor(obj.status).label}

    def get_image(self, obj):
        if ProfileImage.objects.filter(user=obj).exists():
            image_url = obj.image.picture.medium.url
            return os.path.join(fullfii.BASE_URL, image_url if image_url[0] != '/' else image_url[1:])


class MeSerializer(UserSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'email', 'birthday', 'age', 'gender', 'introduction', 'num_of_thunks', 'date_joined', 'status', 'plan', 'features', 'genre_of_worries', 'scale_of_worries', 'intro_step', 'intro_step', 'image', 'me', 'can_talk_heterosexual')

    plan = serializers.SerializerMethodField()
    me = serializers.BooleanField(default=True)
    intro_step = serializers.SerializerMethodField()

    def get_plan(self, obj):
        return {'key': Plan(obj.plan).value, 'label': Plan(obj.plan).label}

    def get_intro_step(self, obj):
        intro_step = {}
        for intro_step_obj in IntroStep.objects.all():
            intro_step[intro_step_obj.key] = False
        for done_intro_step_obj in obj.intro_step.all():
            intro_step[done_intro_step_obj.key] = True
        return intro_step


class PatchMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('name', 'email', 'birthday', 'introduction', 'can_talk_heterosexual', 'gender')

    name = serializers.CharField(source='username')

    def validate_gender(self, data):
        if not data in Gender.values:
            raise serializers.ValidationError('不正な性別です。')
        return data

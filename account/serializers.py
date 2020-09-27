import os
from django.contrib.auth import password_validation as validators
from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer, jwt_payload_handler, jwt_encode_handler
import fullfii
from account.models import Account, ProfileImage, Plan, Status, Feature, GenreOfWorries, ScaleOfWorries, \
    WorriesToSympathize


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'username', 'email', 'password', 'birthday')

    password = serializers.CharField(write_only=True, min_length=8, max_length=30)

    def validate_password(self, data):
        validators.validate_password(password=data, user=Account)
        return data

    def create(self, validated_data):
        return Account.objects.create_user(**validated_data)


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


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileImage
        fields = ('picture', 'user')


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        exclude = ['id']


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


class WorriesToSympathizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorriesToSympathize
        exclude = ['id']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'birthday', 'age', 'introduction', 'num_of_thunks', 'status', 'features', 'genre_of_worries', 'scale_of_worries', 'worries_to_sympathize', 'image', 'me')

    name = serializers.CharField(source='username')
    birthday = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    status = StatusSerializer()
    features = FeaturesSerializer(many=True)
    genre_of_worries = GenreOfWorriesSerializer(many=True)
    scale_of_worries = ScaleOfWorriesSerializer(many=True)
    worries_to_sympathize = WorriesToSympathizeSerializer(many=True)
    image = serializers.SerializerMethodField()
    me = serializers.BooleanField(default=False)

    def get_birthday(self, obj):
        return fullfii.generate_birthday(birthday=obj.birthday)

    def get_age(self, obj):
        return fullfii.calc_age(birthday=obj.birthday)

    def get_image(self, obj):
        if ProfileImage.objects.filter(user=obj).exists():
            image_url = obj.image.picture.url
            return os.path.join(fullfii.BASE_URL, image_url if image_url[0] != '/' else image_url[1:])


class MeSerializer(UserSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'email', 'birthday', 'age', 'introduction', 'num_of_thunks', 'date_joined', 'status', 'plan', 'features', 'genre_of_worries', 'scale_of_worries', 'worries_to_sympathize', 'image', 'me')

    plan = serializers.SerializerMethodField()
    me = serializers.BooleanField(default=True)

    def get_plan(self, obj):
        return {'key': Plan(obj.plan).value, 'label': Plan(obj.plan).label}


class PatchMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('name', 'email', 'birthday', 'introduction')

    name = serializers.CharField(source='username')

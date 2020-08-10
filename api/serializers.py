from rest_framework import serializers
from main.models import User, Voice


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'name', 'description', 'icon')


class UserSerializer(serializers.ModelSerializer):
    followings_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    # is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('user_id', 'name', 'description', 'icon', 'followings_count', 'followers_count')

    def get_followings_count(self, obj):
        return obj.following.count()

    def get_followers_count(self, obj):
        return obj.follower.count()

    # def get_is_following(self, obj):
    #     user = self.context['request'].user
    #
    #     if user.is_authenticated:
    #         return obj in user.get_followings()
    #     else:
    #         return False

class VoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voice
        fields = '__all__'
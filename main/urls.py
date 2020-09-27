from django.urls import path
from rest_framework_jwt.views import ObtainJSONWebToken
from account.serializers import LoginSerializer
from account.views import signupAPIView, meAPIView, profileImageAPIView
from api.views import profileParamsAPIView, usersAPIView, talkRequestAPIView, cancelTalkAPIView, talkInfoAPIView, \
    endTalkAPIView, closeTalkAPIView

app_name = 'api'

urlpatterns = [
    path('/', ObtainJSONWebToken.as_view(serializer_class=LoginSerializer)),
]

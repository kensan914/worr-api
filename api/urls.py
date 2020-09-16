from django.urls import path
from rest_framework_jwt.views import ObtainJSONWebToken
from account.serializers import LoginSerializer
from account.views import signupAPIView, meAPIView, profileImageAPIView
from api.views import profileParamsAPIView, usersAPIView, chatRequestAPIView

app_name = 'api'

urlpatterns = [
    path('login/', ObtainJSONWebToken.as_view(serializer_class=LoginSerializer)),
    path('signup/', signupAPIView),
    path('me/', meAPIView),
    path('me/profile-image/', profileImageAPIView),
    path('profile-params/', profileParamsAPIView),
    path('users/', usersAPIView),
    path('users/<uuid:user_id>/', usersAPIView),
    path('chat-request/<uuid:user_id>/', chatRequestAPIView),
]

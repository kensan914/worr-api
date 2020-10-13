from django.urls import path
from rest_framework_jwt.views import ObtainJSONWebToken
from account.serializers import LoginSerializer
from account.views import signupAPIView, meAPIView, profileImageAPIView, authUpdateAPIView
from api.views import profileParamsAPIView, usersAPIView, talkRequestAPIView, cancelTalkAPIView, talkInfoAPIView, \
    endTalkAPIView, closeTalkAPIView, purchaseProductAPIView, noticeFromAppStoreAPIView, restoreProductAPIView, \
    blockAPIView

app_name = 'api'

urlpatterns = [
    path('login/', ObtainJSONWebToken.as_view(serializer_class=LoginSerializer)),
    path('signup/', signupAPIView),
    path('me/', meAPIView),
    path('me/profile-image/', profileImageAPIView),
    path('me/talk-info/', talkInfoAPIView),
    path('me/email/', authUpdateAPIView),
    path('me/password/', authUpdateAPIView),
    path('profile-params/', profileParamsAPIView),
    path('users/', usersAPIView),
    path('users/<uuid:user_id>/', usersAPIView),
    path('users/<uuid:user_id>/talk-request/', talkRequestAPIView),
    path('users/<uuid:user_id>/block/', blockAPIView),
    path('rooms/<uuid:room_id>/cancel/', cancelTalkAPIView),
    path('rooms/<uuid:room_id>/end/', endTalkAPIView),
    path('rooms/<uuid:room_id>/close/', closeTalkAPIView),
    path('products/<str:product_id>/purchase/', purchaseProductAPIView),
    path('products/<str:product_id>/restore/', restoreProductAPIView),
    path('products/notice/', noticeFromAppStoreAPIView),
]

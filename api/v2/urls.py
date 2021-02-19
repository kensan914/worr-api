from django.urls import path
from rest_framework_jwt.views import ObtainJSONWebToken
from account.serializers import LoginSerializer
from account.views import signupAPIView, meAPIView, profileImageAPIView, authUpdateAPIView
from api.v2.views import meV2APIView, profileParamsV2APIView, profileImageV2APIView, talkInfoV2APIView, \
    talkTicketAPIView, closeTalkV2APIView, worryAPIView
from api.views import profileParamsAPIView, usersAPIView, talkRequestAPIView, cancelTalkAPIView, talkInfoAPIView, \
    endTalkAPIView, closeTalkAPIView, purchaseProductAPIView, noticeFromAppStoreAPIView, restoreProductAPIView, \
    blockAPIView, worriesAPIView

app_name = 'api_v2'

urlpatterns = [
    # path('login/', ObtainJSONWebToken.as_view(serializer_class=LoginSerializer)),
    path('signup/', signupAPIView),
    path('me/', meV2APIView),
    path('me/profile-image/', profileImageV2APIView),
    path('me/talk-info/', talkInfoV2APIView),
    # path('me/device-token/', deviceTokenAPIView),
    # path('me/email/', authUpdateAPIView),
    # path('me/password/', authUpdateAPIView),
    path('profile-params/', profileParamsV2APIView),
    # path('users/', usersAPIView),
    path('users/<uuid:user_id>/', usersAPIView),
    # path('users/<uuid:user_id>/talk-request/', talkRequestAPIView),
    path('users/<uuid:user_id>/block/', blockAPIView),
    # path('rooms/<uuid:room_id>/cancel/', cancelTalkAPIView),
    # path('rooms/<uuid:room_id>/end/', endTalkAPIView),
    path('rooms/<uuid:room_id>/close/', closeTalkV2APIView),
    path('talk-ticket/<uuid:talk_ticket_id>/', talkTicketAPIView),
    path('me/worries/', worryAPIView),

    path('products/<str:product_id>/purchase/', purchaseProductAPIView),
    path('products/<str:product_id>/restore/', restoreProductAPIView),
    path('products/notice/', noticeFromAppStoreAPIView),
    # path('worries/', worriesAPIView),
    # path('worries/<uuid:worry_id>/', worriesAPIView),
]

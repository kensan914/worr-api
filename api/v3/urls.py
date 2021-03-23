from django.urls import path
from account.views import signupAPIView
from api.v2.views import meV2APIView, profileParamsV2APIView, profileImageV2APIView, talkInfoV2APIView, \
    talkTicketAPIView, closeTalkV2APIView, worryAPIView, genderAPIView
from api.v3.views import talkTicketAPIView
from api.views import usersAPIView, purchaseProductAPIView, noticeFromAppStoreAPIView, restoreProductAPIView, \
    blockAPIView

app_name = 'api_v3'

urlpatterns = [
    path('signup/', signupAPIView),
    path('me/', meV2APIView),
    path('me/profile-image/', profileImageV2APIView),
    path('me/talk-info/', talkInfoV2APIView),
    path('me/gender/', genderAPIView),
    path('profile-params/', profileParamsV2APIView),
    path('users/<uuid:user_id>/', usersAPIView),
    path('users/<uuid:user_id>/block/', blockAPIView),
    path('rooms/<uuid:room_id>/close/', closeTalkV2APIView),
    path('talk-ticket/<uuid:talk_ticket_id>/', talkTicketAPIView),
    path('me/worries/', worryAPIView),

    path('products/<str:product_id>/purchase/', purchaseProductAPIView),
    path('products/<str:product_id>/restore/', restoreProductAPIView),
    path('products/notice/', noticeFromAppStoreAPIView),
]

from django.urls import path
from account.v4.views import (
    signupAPIView,
    profileImageAPIView,
    meAPIView,
    profileParamsAPIView,
    genderAPIView,
    usersAPIView,
    hiddenRoomsAPIView,
    blockedRoomsAPIView,
)
from chat.v4.views import (
    talkInfoAPIView,
    roomsAPIView,
    roomAPIView,
    roomImagesAPIView,
    roomParticipantsAPIView,
    roomLeftMembersAPIView,
    roomClosedMembersAPIView,
)
from survey.views import accountDeleteSurveyAPIView

app_name = "api_v4"


urlpatterns = [
    path("signup/", signupAPIView),
    path("profile-params/", profileParamsAPIView),
    path("me/", meAPIView),
    path("me/profile-image/", profileImageAPIView),
    path("me/talk-info/", talkInfoAPIView),
    path("me/gender/", genderAPIView),
    path("me/hidden-rooms/", hiddenRoomsAPIView),
    path("me/blocked-rooms/", blockedRoomsAPIView),
    path("users/<uuid:user_id>/", usersAPIView),  # TODO: いる？
    path("rooms/", roomsAPIView),
    path("rooms/<uuid:room_id>/", roomAPIView),
    path("rooms/<uuid:room_id>/images/", roomImagesAPIView),
    path("rooms/<uuid:room_id>/participants/", roomParticipantsAPIView),
    path("rooms/<uuid:room_id>/left-members/", roomLeftMembersAPIView),
    path("rooms/<uuid:room_id>/closed-members/", roomClosedMembersAPIView),
    path("survey/account-delete/", accountDeleteSurveyAPIView),
]

from survey.serializers import AccountDeleteSurveySerializer
from rest_framework import views, permissions, status
from rest_framework.response import Response


class AccountDeleteSurveyAPIView(views.APIView):
    """
    post data: { reason: "使い方がイマイチわからない", }
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post_data = {"respondent": request.user.id, **request.data}
        account_delete_survey_serializer = AccountDeleteSurveySerializer(data=post_data)
        if account_delete_survey_serializer.is_valid():
            account_delete_survey_serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(
                data=account_delete_survey_serializer.errors,
                status=status.HTTP_404_NOT_FOUND,
            )


accountDeleteSurveyAPIView = AccountDeleteSurveyAPIView.as_view()

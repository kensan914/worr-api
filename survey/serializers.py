from rest_framework import serializers
from survey.models import AccountDeleteSurvey


class AccountDeleteSurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountDeleteSurvey
        fields = (
            "respondent",
            "reason",
        )

    def validate_reason(self, reason):
        if type(reason) != str:
            raise serializers.ValidationError("入力された値は文字列ではありません。")
        if len(reason) <= 0:
            raise serializers.ValidationError("1文字以上入力してください")

        return reason

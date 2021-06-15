from django.urls import path
from main.views import topView, termsOfServiceView, privacyPolicyView

app_name = "main"

urlpatterns = [
    path("", topView, name="top"),
    path("terms-of-service/", termsOfServiceView, name="terms_of_service"),
    path("privacy-policy/", privacyPolicyView, name="privacy_policy"),
]

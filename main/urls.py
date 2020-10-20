from django.urls import path
from main.views import topView, termsOfServiceView

app_name = 'main'

urlpatterns = [
    path('', topView, name='top'),
    path('terms-of-service/', termsOfServiceView, name='terms_of_service'),
]

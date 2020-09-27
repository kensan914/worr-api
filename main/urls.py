from django.urls import path, re_path
import main
from main import views

app_name = 'api'

urlpatterns = [
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
]

# catch all other URL
urlpatterns += [re_path(r'^.*/$', main.views.top, name='top')]
urlpatterns += [path('', main.views.top, name='top')]

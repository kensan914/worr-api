"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import settings

urlpatterns = [
    # path("api/v1/", include("api.urls")),
    # path('api/v2/', include('api.v2.urls')),
    # path('api/v3/', include('api.v3.urls')),
    path("api/v4/", include("api.v4.urls")),
    path("", include("main.urls")),
]

if settings.ADMIN:
    admin.site.site_header = "Fullfii 管理サイト"
    admin.site.site_title = "Fullfii 管理サイト"
    admin.site.index_title = "HOME🏠"
    urlpatterns += [path("admin/", admin.site.urls)]

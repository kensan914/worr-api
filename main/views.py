from django.shortcuts import render
from django.views import View
from config import settings


class BaseView(View):
    html_path = "frontend/index.html"
    context = {"static_update": "?3.0.0", "debug": settings.env.bool("DEBUG")}


class TopView(BaseView):
    html_path = "index.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.html_path, self.context)


topView = TopView.as_view()


class TermsOfServiceView(BaseView):
    html_path = "terms-of-service.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.html_path, self.context)


termsOfServiceView = TermsOfServiceView.as_view()


class PrivacyPolicyView(BaseView):
    html_path = "privacypolicy.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.html_path, self.context)


privacyPolicyView = PrivacyPolicyView.as_view()

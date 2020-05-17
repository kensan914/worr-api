from rest_framework import status, views
from rest_framework.response import Response


class Test(views.APIView):
    def get(self, request):
        return Response(((1, 2), (3, 4), (5, 6)), status.HTTP_200_OK)

test = Test.as_view()

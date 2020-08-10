from django.shortcuts import render
from rest_framework import viewsets, filters, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from main.models import User, Connection, Voice
from .serializers import UserSerializer, UserMiniSerializer, VoiceSerializer


# from .permissions import IsMyselfOrReadOnly


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsMyselfOrReadOnly]
    lookup_field = 'user_id'
    filter_backends = [filters.SearchFilter]
    search_fields = ['user_id', 'description']

    # @action(detail=True)
    # def follow(self, request, username=None):
    #     follower = request.user
    #     following = self.get_object()
    #
    #     if follower == following:
    #         return Response({'errors': ['You cannot follow your account']}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     obj, created = Connection.objects.get_or_create(follower=follower, following=following)
    #
    #     if (created):
    #         return Response({'data': ['Follow successfully']})
    #     else:
    #         return Response({'errors': ['You already follow']}, status=status.HTTP_400_BAD_REQUEST)
    #
    # @action(detail=True, permission_classes=[permissions.IsAuthenticated])
    # def unfollow(self, request, username=None):
    #     follower = request.user
    #     following = self.get_object()
    #
    #     if follower == following:
    #         return Response({'errors': ['You cannot unfollow your account']}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     if not Connection.objects.filter(follower=follower, following=following).exists():
    #         return Response({'errors': {"You aren't following that account"}}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     Connection.objects.get(follower=follower, following=following).delete()
    #
    #     return Response({'data': ['Unfollow successfully']})

    @action(detail=True)
    def followings(self, request):
        test_user = User.objects.get(user_id='test')
        users = test_user.following

        # users = self.get_object().get_followings()
        serializer = UserMiniSerializer(users, many=True, context={'request': request})

        return Response(serializer.data)

    @action(detail=True)
    def followers(self, request):
        test_user = User.objects.get(user_id='test')
        users = test_user.follower

        # users = self.get_object().get_followers()
        serializer = UserMiniSerializer(users, many=True, context={'request': request})

        return Response(serializer.data)


class VoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Voice.objects.all()
    serializer_class = VoiceSerializer

    lookup_field = 'voice_id'
    filter_backends = [filters.SearchFilter]
    search_fields = ['voice_id']

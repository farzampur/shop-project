from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserStore
from .serializers import (
    UserStoreSerializer,
    StoreUserCreateSerializer,
    MeSerializer,
)
from .permissions import StoreUserPermission

class UserStoreViewSet(viewsets.ModelViewSet):

    permission_classes = [
        IsAuthenticated,
        StoreUserPermission,
    ]

    def get_queryset(self):

        return UserStore.objects.filter(
            store__store_users__user=self.request.user
        ).select_related(
            "user",
            "store",
        )

    def get_serializer_class(self):

        if self.action == "create":
            return StoreUserCreateSerializer

        return UserStoreSerializer
        
        
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        user_store = UserStore.objects.get(
            user=user,
            store=serializer.validated_data["store"]
        )

        response_serializer = UserStoreSerializer(
            user_store
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
            

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)

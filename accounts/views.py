from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import UserStore
from .serializers import UserStoreSerializer


class UserStoreViewSet(viewsets.ModelViewSet):

    serializer_class = UserStoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserStore.objects.filter(
            user=self.request.user
        )
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Account, Role
from .permissions import IsAdminRole
from .serializers import (
    AccountSerializer,
    AccountWriteSerializer,
    EmailTokenObtainPairSerializer,
)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class MeView(RetrieveAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AccountViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = AccountWriteSerializer
    queryset = Account.objects.all()

    def get_queryset(self):
        if getattr(self.request.user, "role", None) == Role.ADMIN:
            return Account.objects.all()
        return Account.objects.filter(pk=self.request.user.pk)

    def get_permissions(self):
        if self.action in ("list", "create"):
            return [IsAdminRole()]
        return [IsAuthenticated()]

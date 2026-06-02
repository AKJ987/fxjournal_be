from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from utils.mixins import SuccessMessageMixin
from accounts.models import User
from .serializers import UserCreateSerializer

class UserRegisterAPI(SuccessMessageMixin, CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]
    success_message = "User registration successful."
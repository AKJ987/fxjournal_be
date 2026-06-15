from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from utils.mixins import SuccessMessageMixin
from accounts.models import User
from .serializers import (
    UserCreateSerializer,
    UserLoginSerializer,
    UserLogoutSerializer,
    ForgetPasswordOTPSerializer,
    ResetPasswordSerializer,
)

class UserRegisterAPIView(SuccessMessageMixin, CreateAPIView):
    """
    API view for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]
    success_message = "User registration successful."

class UserLoginAPIView(GenericAPIView):
    """
    API view for user login.
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "data": serializer.validated_data,
                "message": "Login successful."
            },
            status=status.HTTP_200_OK
        )


class UserLogoutAPIView(GenericAPIView):
    """
    API view for user logout.
    """
    serializer_class = UserLogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "message": "Logout successful."
            },
            status=status.HTTP_200_OK
        )


class ForgetPasswordOTPAPIView(SuccessMessageMixin, CreateAPIView):
    """
    API view for generating forget password OTP.
    """
    serializer_class = ForgetPasswordOTPSerializer
    permission_classes = [AllowAny]
    success_message = "OTP sent successfully."


class ResetPasswordAPIView(SuccessMessageMixin, CreateAPIView):
    """
    API view for resetting password.
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    success_message = "Password updated successfully."

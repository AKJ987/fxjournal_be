import base64
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from accounts.models import User
from .functions import is_password_valid, generate_otp, decrypt_data
from emails.views import send_email

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ("full_name", "email", "password", "confirm_password")

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        confirm_password = attrs.pop("confirm_password")

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"error": "Email already exists."})

        if not is_password_valid(password):
            raise serializers.ValidationError({"error": "Password does not meet requirements."})

        if password != confirm_password:
            raise serializers.ValidationError({"error": "Passwords do not match."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(
            username=validated_data["email"],
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"),
            password=attrs.get("password")
        )

        if not user:
            raise AuthenticationFailed("Invalid username or password.")

        if not user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        refresh = RefreshToken.for_user(user)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            token = RefreshToken(attrs["refresh"])
            token.blacklist()
        except Exception:
            raise ValidationError("Invalid refresh token.")

        return {}


class ForgetPasswordOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')

        user = User.objects.filter(email=email, is_active=True).first()
        if not user:
            raise serializers.ValidationError(
                {"error": "User with this email does not exist."}
            )
        
        self.user = user
        return attrs

    def create(self, validated_data):
        otp = generate_otp(self.user)
        subject = "Password Reset Verification"

        body_vars = {"username":self.user.full_name, "otp":otp}
        header = {
            'subject':subject,
            'to':[self.user.email],
            'template_name':'fgt_password'
        }
        send_email(header, body_vars)

        return {
            "email": self.user.email
        }


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)
    otp = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get("otp")
        password = attrs.get("password")
        confirm_password = attrs.pop("confirm_password")

        user = User.objects.filter(email=email, is_active=True).first()
        if not user:
            raise serializers.ValidationError(
                {"error": "User with this email does not exist."}
            )

        decrypted_otp = decrypt_data(user.otp, base64.b64decode(user.secret_key)).decode('utf-8')

        if otp != decrypted_otp:
            raise serializers.ValidationError({"error": "Verification failed. The OTP is not valid."})
        
        if timezone.now() - user.otp_created_time > timedelta(minutes=10):
            raise serializers.ValidationError({"error": "Verification failed. The OTP has expired."})

        if not is_password_valid(password):
            raise serializers.ValidationError({"error": "Password does not meet requirements."})

        if password != confirm_password:
            raise serializers.ValidationError({"error": "Passwords do not match."})

        self.user = user
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = self.user
        user.set_password(password)
        user.otp = user.otp_created_time = user.secret_key = None
        user.save()
        return user

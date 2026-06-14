from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from .functions import is_password_valid

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

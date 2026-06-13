from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("full_name", "email", "phone", "password")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data["email"]

        user = User(
            username=email,
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

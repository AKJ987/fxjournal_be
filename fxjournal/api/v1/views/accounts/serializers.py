from rest_framework import serializers
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
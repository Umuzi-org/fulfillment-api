from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Account, Role


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get(self.username_field)
        if email:
            attrs[self.username_field] = email.lower()
        return super().validate(attrs)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("id", "email", "role", "created_at")
        read_only_fields = fields


class AccountWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = Account
        fields = ("id", "email", "password", "role", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_email(self, value):
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_role(self, value):
        user = self.context["request"].user
        changing_own_role = self.instance is not None and value != self.instance.role
        if changing_own_role and getattr(user, "role", None) != Role.ADMIN:
            raise serializers.ValidationError("Only an admin can change role.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        account = Account(**validated_data)
        account.set_password(password)
        account.save()
        return account

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        account = super().update(instance, validated_data)
        if password:
            account.set_password(password)
            account.save(update_fields=["password"])
        return account

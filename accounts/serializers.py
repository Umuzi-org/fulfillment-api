from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Account


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

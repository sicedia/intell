"""
Serializers for authentication endpoints.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Serializer for login credentials."""
    username = serializers.CharField(
        max_length=150,
        help_text="Username or email"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="User password"
    )


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data (read-only, no sensitive fields)."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = fields

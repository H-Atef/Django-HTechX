from rest_framework import serializers
from django.core.exceptions import ValidationError
from users.models import User  

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True}
        }

    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create user with hashed password and role-based logic."""
        email = validated_data.get("email")

        # Ensure email is not empty
        if not email:
            raise serializers.ValidationError({"email": "Email cannot be empty."})

        # Create user
        user = User.objects.create_user(**validated_data)

      
        return user

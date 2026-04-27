from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from auth_app.models import Profile
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'fullname', 'email', 'password', 'repeated_password']

    def validate(self, data):
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('repeated_password')
        fullname = validated_data.pop('fullname')

        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        Profile.objects.create(
            user = user,
            fullname=fullname
        )

        Token.objects.create(user=user)

        return user
    

class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only = True)


    def validate(self,data):
        email = data.get('email')
        password = data.get('password')

        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
        
        user = authenticate(username=username, password=password)
        print(f"authenticated user: {user}")
        
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        data["user"] = user
        return data
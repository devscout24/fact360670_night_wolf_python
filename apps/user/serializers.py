

from .models import User
from rest_framework import fields, serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta 
User = get_user_model()


class UserProfileSerializer( serializers.ModelSerializer):
    class Meta:
        model= User
        fields= ['id','full_name', 'is_subscribed', 'photo']

class SignUpSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id','full_name',  'email', 'password', 'password2']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password_mismatch": "Password fields did not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2') 
        password = validated_data['password']

        validate_password(password)

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password
        )
        return user


# User can change password using old password
class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)    
    
class PasswordResetRQSerializer(serializers.Serializer):
    email= serializers.EmailField()
    
    def validate_email(self,data):
        try:
            user= User.objects.get(email=data)
        except:
            raise serializers.ValidationError("This Email does not exist!")
        
         
        user.generate_otp()
        send_mail(
             "Password Reset OTP",
            f"Your OTP for password reset is {user.otp}",
            "aboutazizur@gmail.com",
            [user.email],
            fail_silently=False,
        )
        print("OTP Sent:", user.otp)
        return data
    

class OTPVerifySerializer(serializers.Serializer):
    email= serializers.EmailField()
    otp= serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        try:
            user= User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})
        
        if user.otp!=attrs['otp']:
            raise  serializers.ValidationError({"otp": "Invalid OTP."})
        if user.otp_exp < now(): 
            raise serializers.ValidationError({"otp": "OTP expired."})

        user.otp_verified = True
        user.save()
        
        print("OTP Verified (after save):", user.otp_verified)
        print("From DB:", User.objects.get(email=user.email).otp_verified)

        return attrs
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    def validate(self, data):
        try:
             user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
             raise serializers.ValidationError({"email": "User not found."})

        if not user.otp_verified:
             raise serializers.ValidationError({"otp": "OTP verification required."})

        if user.otp_exp < now():
            raise serializers.ValidationError({"otp": "OTP has expired."})
        
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password_mismatch": "New password and confirm password do not match."})

        return data
    
    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["new_password"])
        user.otp = None  
        user.otp_exp = None
        user.otp_verified = False  
        user.save()
        return user
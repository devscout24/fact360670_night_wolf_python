

from .models import *
from rest_framework import fields, serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from django.utils import timezone
User = get_user_model()
from rest_framework_simplejwt.tokens import RefreshToken


class AbsoluteImageSerializer(serializers.ImageField):
    def to_representation(self, value):
        request = self.context.get('request', None)
        if value:
            url = value.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None


class SubscriptionSerializer(serializers.ModelSerializer):
    months_left = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ["id", "user", "start_date", "end_date", "months_left", "is_active"]

    def get_months_left(self, obj):
        return obj.months_left()

    def get_is_active(self, obj):
        return obj.is_active()
    

class UserProfileSerializer( serializers.ModelSerializer):
    photo = AbsoluteImageSerializer(required=False)
    class Meta:
        model= User
        fields= ['id','full_name', 'is_subscribed', 'photo']


class SignUpSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    photo = AbsoluteImageSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'password', 'password2', 'photo']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # remove password2
        password = validated_data.pop('password2', None)

        # Delete previous unverified users with same email
        email = validated_data.get('email')
        User.objects.filter(email=email, otp_verified=False).delete()

        # Create user
        user = User.objects.create_user(
            email=validated_data.get('email'),
            password=validated_data.get('password'),  
            full_name=validated_data.get('full_name'),
            photo=validated_data.get('photo'),
            is_active=False
        )

        # Generate OTP
        user.generate_otp()

        # Send OTP via email
        subject = "Verify your email"
        message = f"Hi {user.full_name},\nYour OTP is {user.otp}. It expires in 10 minutes."
        send_mail(subject, message, 'from@example.com', [user.email])
        print("OTP Sent:", user.otp)

        return user


class EmailVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        # Check if OTP matches
        if user.otp != otp:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        # Check if OTP expired
        if user.otp_exp < timezone.now():
            raise serializers.ValidationError({"otp": "OTP expired."})

        self.user = user
        return attrs

    def save(self):
        user = self.user
        user.otp_verified = True
        user.is_active= True
        user.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return {
            "user": user,
            "refresh": refresh,
            "access": access
        }


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)    
    
    
class PasswordResetRQSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, data):
        try:
            user = User.objects.get(email=data)
        except User.DoesNotExist:
            raise serializers.ValidationError("This Email does not exist!")

        # Generate OTP
        user.generate_otp()

        # Send OTP via email
        # send_mail(
        #     "Password Reset OTP",
        #     f"Your OTP for password reset is {user.otp}",
        #     "aboutazizur@gmail.com",
        #     [user.email],
        #     fail_silently=False,
        # )

        # Save the user instance to serializer for view access
        self.user = user  

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
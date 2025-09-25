from django.shortcuts import render
from .models import *
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from .serializers import SignUpSerializer
from apps.stories.thread import create_subscription_notification
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserProfileSerializer, UserChangePasswordSerializer, PasswordResetRQSerializer,OTPVerifySerializer,PasswordResetSerializer, EmailVerifySerializer, SubscriptionSerializer


class BaseAPIView(APIView):
    
    def success_response(self, message="Thank you for your request", data=None, status_code=status.HTTP_200_OK):
        return Response(
            {
            "success": True,
            "message": message,
            "status_code": status_code,
            "data": data or {}
            }, 
            status=status_code)
        
    def error_response(self, message="I am sorry for your request", data=None, status_code=status.HTTP_400_BAD_REQUEST):
        return Response(
            {
            "success": False,
            "message": message,
            "status_code": status_code,
            "data": data or {}
            }, 
            status=status_code)


class SubscriptionView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    # GET → show current subscription details
    def get(self, request):
        try:
            subscription = request.user.subscription
            serializer = SubscriptionSerializer(subscription)
            return self.success_response(
                message="Current subscription details",
                data=serializer.data
            )
        except Subscription.DoesNotExist:
            return self.error_response(
                message="No active subscription",
                status_code=status.HTTP_404_NOT_FOUND
            )

    # POST → create or update subscription
    def post(self, request):
        months = int(request.data.get("months", 1))  # default 1 month
        start = timezone.now()
        end = start + timedelta(days=months * 30)

        subscription, created = Subscription.objects.update_or_create(
            user=request.user,
            defaults={"start_date": start, "end_date": end},
        )

        # update user's subscription status
        request.user.is_subscribed = True
        request.user.save(update_fields=["is_subscribed"])

        # send notification about subscription months left
        create_subscription_notification(request.user)

        serializer = SubscriptionSerializer(subscription)
        return self.success_response(
            message="Subscription created" if created else "Subscription updated",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    # DELETE → cancel subscription
    def delete(self, request):
        try:
            subscription = request.user.subscription
            subscription.delete()

            # update user's subscription status
            request.user.is_subscribed = False
            request.user.save(update_fields=["is_subscribed"])

            return self.success_response(
                message="Subscription cancelled successfully",
                data={},
                status_code=status.HTTP_204_NO_CONTENT
            )
        except Subscription.DoesNotExist:
            return self.error_response(
                message="No active subscription",
                status_code=status.HTTP_404_NOT_FOUND
            )


class UserProfileAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return self.success_response(data=serializer.data)


class UserProfileDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        if id:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return self.error_response('User not found.', status_code=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user

        serializer = UserProfileSerializer(user)
        return self.success_response(data=serializer.data)
    
    def put(self, request, id=None):
        if id:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return self.error_response("User not found", status_code=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(data=serializer.data)
        return self.error_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        if id:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return self.error_response('User not found.', status_code=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user

        user.delete()
        return self.success_response('User profile deleted successfully.')


class SignUpView(BaseAPIView):
    permission_classes = []
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return self.success_response(
                message="OTP sent to your email",
                data={"otp": user.otp},
                status_code=status.HTTP_201_CREATED
            )
        return self.error_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class EmailOTPVerifyView(BaseAPIView):
    permission_classes = []

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            user_serializer = UserProfileSerializer(data["user"])
            
            return self.success_response(
                data={
                    "user": user_serializer.data,
                    "refresh": str(data["refresh"]),
                    "access": str(data["access"]),
                }
            )
        return self.error_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    
class LoginView(BaseAPIView):
    permission_classes = []    

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return self.error_response("Invalid email or password", status_code=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password): 
            return self.error_response("Invalid email or password", status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return self.error_response("Account is not active", status_code=status.HTTP_403_FORBIDDEN)

        serializer = UserProfileSerializer(user)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return self.success_response(
            data={
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(access),
            }
        )

    
class LogoutView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return self.success_response("Logout successful", status_code=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return self.error_response("Invalid token", status_code=status.HTTP_400_BAD_REQUEST)  

    
class UserChangePasswordAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        serializer = UserChangePasswordSerializer(data=request.data)
        userdata = UserProfileSerializer(request.user).data
        
        if serializer.is_valid():
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]
            confirm_password = request.data.get("confirm_password")

            try:
                user = User.objects.get(pk=pk)
            except User.DoesNotExist:
                return self.error_response("User not found.", status_code=status.HTTP_404_NOT_FOUND)

            if not user.check_password(old_password):
                return self.error_response("Old password does not match.", status_code=status.HTTP_400_BAD_REQUEST)
            
            if new_password != confirm_password:
                return self.error_response("New password and confirm password do not match.", status_code=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return self.success_response(data=userdata)

        return self.error_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class PasswordResetRQAPIView(BaseAPIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetRQSerializer(data=request.data)
        if serializer.is_valid():
            user = getattr(serializer, 'user', None)
            otp_value = user.otp if user else None
            email = user.email if user else None
            
            return self.success_response(
                message="OTP sent to email.",
                data={
                    "otp": otp_value,
                    "email": email
                }
            )

        return self.error_response(
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

        
class OTPVerifyAPIView(BaseAPIView):
    permission_classes = []
    
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            return self.success_response("OTP verified successfully.")
        
        return self.error_response(
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )     
           
           
class PasswordResetAPIView(BaseAPIView):
    permission_classes = []
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return self.success_response("Password reset successfully.")
        
        return self.error_response(
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
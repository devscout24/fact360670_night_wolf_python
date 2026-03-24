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
            "data": data or []
            }, 
            status=status_code)

    def _flatten_errors(self, errors):
        """Flatten serializer errors dict into a single readable message string."""
        if isinstance(errors, str):
            return errors
        if isinstance(errors, list):
            return " ".join(str(e) for e in errors)
        if isinstance(errors, dict):
            messages = []
            for field, error_list in errors.items():
                if isinstance(error_list, list):
                    for err in error_list:
                        messages.append(str(err))
                else:
                    messages.append(str(error_list))
            return " ".join(messages)
        return str(errors)
        
    def error_response(self, message="I am sorry for your request", data=None, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        # If serializer errors are passed, flatten them into the message field
        if errors is not None:
            message = self._flatten_errors(errors)
        elif data is not None and isinstance(data, dict):
            # If data looks like serializer errors (dict with list values), move to message
            is_error_dict = all(isinstance(v, list) for v in data.values()) if data else False
            if is_error_dict:
                message = self._flatten_errors(data)
                data = None

        return Response(
            {
            "success": False,
            "message": message,
            "status_code": status_code,
            "data": data or []
            }, 
            status=status_code)


class SubscriptionView(BaseAPIView):
    permission_classes = [permissions.AllowAny]

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
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return self.success_response(
                    message="OTP sent to your email",
                    data={"otp": user.otp},
                    status_code=status.HTTP_201_CREATED
                )
            # return validation errors
            return self.error_response(
                message="Validation failed",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            # catch any unexpected error
            return self.error_response(
                message="Something went wrong while processing your request",
                data={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



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

        # Activate user on first login if not already active
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        # If user has not verified OTP, generate and send a new OTP
        otp_value = None
        if not user.otp_verified:
            user.generate_otp()
            from django.core.mail import send_mail
            from django.conf import settings as app_settings
            send_mail(
                subject='Account Verification OTP',
                message='The OTP for account verification is: {}'.format(user.otp),
                from_email=app_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            otp_value = user.otp

        serializer = UserProfileSerializer(user)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response_data = {
            "user": serializer.data,
            "refresh": str(refresh),
            "access": str(access),
        }

        # Include OTP in response if user is not verified (for development/testing)
        if otp_value:
            response_data["otp"] = otp_value

        # Set message based on verification status
        if not user.otp_verified:
            message = "OTP verification required. OTP has been sent to your email."
        else:
            message = "Login successful"

        return self.success_response(message=message, data=response_data)

    
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
            email_sent = getattr(serializer, 'email_sent', None)
            
            return self.success_response(
                message="OTP sent to email.",
                data={
                    "otp": otp_value,
                    "email": email,
                    "email_sent": email_sent
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
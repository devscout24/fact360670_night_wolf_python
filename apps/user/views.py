from django.shortcuts import render

# Create your views here.
from .models import *
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from .serializers import SignUpSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserProfileSerializer, UserChangePasswordSerializer, PasswordResetRQSerializer,OTPVerifySerializer,PasswordResetSerializer, EmailVerifySerializer


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response( serializer.data)


class UserProfileDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        if id:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return Response({'success': False, 'message': 'User not found.'}, status=404)
        else:
            user = request.user

        serializer = UserProfileSerializer(user)
        return Response({'success': True, 'data': serializer.data})
    
    def put(self, request, id=None):
        if id:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return Response({"message": "User not found"}, status= 404)
        else:
            user = request.user

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        if id:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return Response({'success': False, 'message': 'User not found.'}, status=404)
        else:
            user = request.user

        user.delete()
        return Response({'success': True, 'message': 'User profile deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class SignUpView(APIView):
    permission_classes = []
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "message": "OTP sent to your email",
            "otp": user.otp
        }, status=status.HTTP_201_CREATED)

class EmailOTPVerifyView(APIView):
    permission_classes= []  
    
    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.save()
        return Response(tokens, status=status.HTTP_200_OK)
    
    
class LoginView(APIView):
    permission_classes= []    
    
    def post(self, request):
        email= request.data.get("email")
        password= request.data.get("password")
        
        user= authenticate(email=email, password= password)
        serializer= UserProfileSerializer(user)
        if user is None:
            raise AuthenticationFailed({"error": "Invalid email or password"})
        
        refresh= RefreshToken.for_user(user)
        access= refresh.access_token
        
        return Response(
            {
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(access),
            }
        )

    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)  


    
class UserChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        serializer = UserChangePasswordSerializer(data=request.data)
        userdata= UserProfileSerializer(request.user).data
        if serializer.is_valid():
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]
            confirm_password = request.data.get("confirm_password")

            try:
                user = User.objects.get(pk=pk)
            except User.DoesNotExist:
                 raise ValidationError({"error": "User not found."})

            if not user.check_password(old_password):
                raise ValidationError ("Old password does not match.")
            
            if new_password != confirm_password:
                raise ValidationError({"error": "New password and confirm password do not match."})

            user.set_password(new_password)
            user.save()
            return Response(userdata)

        return Response(serializer.errors)    


class PasswordResetRQAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetRQSerializer(data=request.data)
        if serializer.is_valid():
            user = getattr(serializer, 'user', None)
            otp_value = user.otp if user else None
            email= user.email if user else None
            return Response(
                {
                    "message": "OTP sent to email.",
                    "otp": otp_value,
                    "email": email
                },
                status=200
            )

        return Response(
            {"errors": serializer.errors},
            status=400
        )

        
class OTPVerifyAPIView(APIView):
    permission_classes= []
    
    def post(self, request):
        serializer= OTPVerifySerializer(data= request.data)
        
        if serializer.is_valid():
            return Response(
                {"message": "OTP verified successfully."}
            )
        return Response(
            {"errors": serializer.errors}
        )     
           
           
class PasswordResetAPIView(APIView):
    permission_classes = []
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password reset successfully."}
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )           
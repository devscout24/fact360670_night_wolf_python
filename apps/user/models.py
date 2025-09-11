from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

import random 
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self,email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required!")
        email= self.normalize_email(email)
        extra_fields.setdefault('is_active', False)
        user= self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get("is_superuser") is not True:
            extra_fields.setdefault('is_superuser', True)
        if extra_fields.get("is_staff") is not True:
            extra_fields.setdefault('is_staff', True)
        
        return self.create_user(email, password, **extra_fields) 
    
def user_photo_upload_path(instance, filename):
    return f"user_{instance.id}/{filename}"


class User(AbstractBaseUser, PermissionsMixin):
    email= models.EmailField('Your Email', unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    photo = models.ImageField(upload_to=user_photo_upload_path, blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)

    is_active= models.BooleanField(default= False)
    is_staff= models.BooleanField(default=False)
    is_superuser= models.BooleanField(default= False)
    date_joined= models.DateTimeField(default=timezone.now)
    
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_exp = models.DateTimeField(blank=True, null=True) 
    otp_verified = models.BooleanField(default=False)

    objects= UserManager()
    USERNAME_FIELD= 'email'
    
    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))  
        self.otp_exp = timezone.now() + timedelta(minutes=10)
        self.otp_verified = False
        self.save()
    
    def __str__(self):
        return self.email

from rest_framework import serializers
from .models import *
from apps.user.models import User
from django.utils.timesince import timesince

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model= User
        fields=["id", "email", "full_name", "photo"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class FollowCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = FollowCategory
        fields = ["id", "category", "category_id", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id", "audio", "category", "image",
            "message", "is_read", "created_at"
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        
        # যদি audio notification → audio cover image
        if obj.audio and obj.audio.cover_image:
            return request.build_absolute_uri(obj.audio.cover_image.url)
        
        # যদি category notification → fixed category icon
        if obj.category:
            return request.build_absolute_uri("/media/static_image/category_icon.png")

        # যদি subscription notification → fixed subscription icon
        if "Subscription" in obj.message:
            return request.build_absolute_uri("/media/static_image/subcription.png")

        return None


class AudioSerializer(serializers.ModelSerializer):
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_downloaded = serializers.SerializerMethodField() 

    class Meta:
        model = Audio
        fields = "__all__"
        depth = 1

    def get_like_count(self, obj):
        return Like.objects.filter(audio=obj).count()

    def get_comment_count(self, obj):
        return Comment.objects.filter(audio=obj).count()
    
    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(audio=obj, user=request.user).exists()
        return False

    def get_is_downloaded(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Download.objects.filter(audio=obj, user=request.user).exists()
        return False



class AudioPlaySerializer(serializers.ModelSerializer):
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()  # 👈 নতুন field

    class Meta:
        model = Audio
        fields = "__all__"
        depth = 1

    def get_like_count(self, obj):
        return Like.objects.filter(audio=obj).count()

    def get_comment_count(self, obj):
        return Comment.objects.filter(audio=obj).count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(audio=obj, user=request.user).exists()
        return False
        
        
class PlayListSerializer(serializers.ModelSerializer):
    audios= AudioSerializer(many=True, read_only= True)
    
    class Meta:
        model = Playlist
        fields = ["id", "name", "audios"]      
        
        
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model= Like
        fields= ['id', "user", "created_at"]
        
        
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', "user", 'text', "created_at", "time_ago"]

    def get_time_ago(self, obj):
        # created_at theke current time porjonto gap
        return f"{timesince(obj.created_at)} ago"
        
        
class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model= History
        fields= "__all__"
        
        
class DownloadSerializer(serializers.ModelSerializer):
    audio = AudioSerializer(read_only=True)
    
    class Meta:
        model= Download
        fields= ['id','user', 'audio']                
        
        
class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = "__all__"
        
        

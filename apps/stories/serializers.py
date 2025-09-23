from rest_framework import serializers
from .models import *
from apps.user.models import User

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
    audio_title = serializers.CharField(source="audio.title", read_only=True)
    category_name = serializers.CharField(source="audio.category.name", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "audio", "audio_title", "category_name", "message", "is_read", "created_at"]


class AudioSerializer(serializers.ModelSerializer):
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
    user= UserSerializer(read_only= True)
    audio= AudioSerializer(read_only= True)
    
    class Meta:
        model= Comment
        fields= "__all__"
        
        
class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model= History
        fields= "__all__"
        
        
class DownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model= Download
        fields= "__all__"                
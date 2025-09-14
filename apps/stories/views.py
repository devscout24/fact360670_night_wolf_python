from django.shortcuts import render

# Create your views here.
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

class AudioListView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    
    def get(self, request):
        audios= Audio.objects.all().order_by("-created_at")
        serializer= AudioSerializer(audios, many=True)
        
        return Response(serializer.data)

class AudioPlayView(APIView):
    permission_classes= [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            audio= Audio.objects.get(pk=pk)
            audio.increment_play()
            
            History.objects.create(user= request.user, audio= audio)
            serializer= AudioSerializer(audio, context={"request":request})
            return Response({
                
                "message": "Playing audio",
                "play_count": audio.play_count,
                "audio": serializer.data
            })     
            
        except Audio.DoesNotExist:
            return Response({"message": "Audio not found"}, status=404)   
        

class FollowCategoryCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

        follow, created = FollowCategory.objects.get_or_create(
            user=request.user, category=category
        )
        if created:
            return Response({"message": f"You followed {category.name}"}, status=201)
        return Response({"message": f"You already follow {category.name}"}, status=200)


class FollowCategoryDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

        deleted, _ = FollowCategory.objects.filter(
            user=request.user, category=category
        ).delete()
        if deleted:
            return Response({"message": f"You unfollowed {category.name}"}, status=200)
        return Response({"message": "You were not following this category"}, status=400)


class FollowCategoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        follows = FollowCategory.objects.filter(user=request.user)
        serializer = FollowCategorySerializer(follows, many=True)
        return Response(serializer.data, status=200)

class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all notifications for the logged in user"""
        notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """Mark a notification as read"""
        try:
            notif = Notification.objects.get(id=pk, user=request.user)
            notif.is_read = True
            notif.save(update_fields=["is_read"])
            return Response({"message": "Notification marked as read"})
        except Notification.DoesNotExist:
            return Response({"message": "Notification not found"}, status=404)

        
class TrendingAudioView(APIView):
    permission_classes= [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta

        last_week = timezone.now() - timedelta(days=7)
        audios = Audio.objects.filter(created_at__gte=last_week).order_by("-play_count", "-created_at")
        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return Response(serializer.data)


class TopAllStoriesView(APIView):
    permission_classes= [permissions.IsAuthenticated]

    def get(self, request):
        audios = Audio.objects.order_by("-play_count", "-created_at")
        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return Response(serializer.data)


class PopularAudioView(APIView):
    permission_classes= [permissions.IsAuthenticated]

    def get(self, request):
        audios = Audio.objects.order_by("-play_count")
        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return Response(serializer.data)


class RecommendedAudioView(APIView):
    permission_classes= [permissions.IsAuthenticated]

    def get(self, request):
        last_history = History.objects.filter(user=request.user).order_by("-played_at").first()
        if last_history and last_history.audio.category:
            audios = Audio.objects.filter(category=last_history.audio.category).exclude(history__user=request.user)
        else:
            audios = Audio.objects.all().order_by("?")  # fallback = random

        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return Response(serializer.data)

      
class LikeView(APIView):
    permission_classes= [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        audio= Audio.objects.get(pk=pk)
        like, created= Like.objects.get_or_create(user= request.user, audio= audio)
        if not created:
            return Response({"message":"Aready Liked"})
        return Response({"message": "Liked", "total_like": Like.objects.filter(audio=audio).count()})
    
    def get(self, request, pk):
        likes = Like.objects.filter(audio_id=pk).order_by("-created_at")
        serializer = LikeSerializer(likes, many=True, context={"request": request})
        return Response({
            "total_like": likes.count(),
            "likes": serializer.data
        }, status=200)
    
class UnlikeView(APIView):
    permission_classes= [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            like= Like.objects.get(user= request.user, audio_id= pk)
            like.delete()
            return Response({"message": "Unliked"})
        except Like.DoesNotExist:
            return Response({"message":"Not liked yet"})
        
class CommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # GET all comments
    def get(self, request, pk):
        try:
            audio = Audio.objects.get(pk=pk)
        except Audio.DoesNotExist:
            return Response({"error": "Audio not found"}, status=404)

        comments = Comment.objects.filter(audio=audio).order_by("-created_at")
        serializer = CommentSerializer(comments, many=True, context={"request": request})
        return Response({
            "total_comments": comments.count(),
            "comments": serializer.data
        }, status=200)

    # POST new comment
    def post(self, request, pk):
        try:
            audio = Audio.objects.get(pk=pk)
        except Audio.DoesNotExist:
            return Response({"error": "Audio not found"}, status=404)

        serializer = CommentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user, audio=audio)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class CommentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # Helper function with try
    def get_object(self, comment_id, user=None):
        try:
            comment = Comment.objects.get(id=comment_id)
            if user and comment.user != user:
                return None
            return comment
        except Comment.DoesNotExist:
            return None

    # PUT update comment
    def put(self, request, comment_id):
        comment = self.get_object(comment_id, user=request.user)
        if not comment:
            return Response({"error": "Not allowed or comment not found"}, status=403)
        serializer = CommentSerializer(comment, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    # DELETE comment
    def delete(self, request, comment_id):
        comment = self.get_object(comment_id, user=request.user)
        if not comment:
            return Response({"error": "Not allowed or comment not found"}, status=403)
        comment.delete()
        return Response({"message": "Comment deleted"}, status=200)

class PlayListView(APIView):
    permission_classes= [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer= PlayListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user= request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors)
    
    def get(self, request):
        playlists= Playlist.objects.filter(user= request.user)
        serializer= PlayListSerializer(playlists, many= True)
        
        return Response(serializer.data)
          
class AddAudioToPlaylistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, playlist_id):
        try:
            playlist = Playlist.objects.get(id=playlist_id, user=request.user)
        except Playlist.DoesNotExist:
            return Response({"error": "Playlist not found"}, status=404)

        audio_ids = request.data.get("audio_ids", [])
        if not audio_ids:
            return Response({"error": "No audio_ids provided"}, status=400)

        added_audios = []
        for audio_id in audio_ids:
            try:
                audio = Audio.objects.get(id=audio_id)
                playlist.audios.add(audio)
                added_audios.append(audio.title)
            except Audio.DoesNotExist:
                continue

        return Response({
            "message": f"Added audios to playlist: {added_audios}",
            "playlist_id": playlist.id,
            "total_audios": playlist.audios.count()
        }, status=200)

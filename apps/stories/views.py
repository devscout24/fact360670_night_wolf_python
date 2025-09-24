from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

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


class AudioListView(BaseAPIView):
    permission_classes=[permissions.IsAuthenticated]
    
    def get(self, request):
        audios = Audio.objects.all().order_by("-created_at")
        serializer = AudioSerializer(audios, many=True)
        
        return self.success_response(
            message="Audio list retrieved successfully",
            data=serializer.data
        )

class AudioDetailsView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            audio = Audio.objects.get(pk=pk)
            
            History.objects.create(user=request.user, audio=audio)
            serializer = AudioSerializer(audio, context={"request": request})

            related_audios= Audio.objects.filter(category= audio.category).exclude(id=audio.id)
            related_serializer = AudioSerializer(related_audios, many=True, context={"request": request})
            
            return self.success_response(
                message="Audio is now playing",
                data={
                    "play_count": audio.play_count,
                    "audio": serializer.data ,
                    "related_audios": related_serializer.data
                }
            )        
            
        except Audio.DoesNotExist:
            return self.error_response(
                message="Audio not found. Please check the audio ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )   
            
class AudioPlayView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            audio = Audio.objects.get(pk=pk)
            audio.increment_play()
            
            History.objects.create(user=request.user, audio=audio)
            serializer = AudioPlaySerializer(audio, context={"request": request})
            
            return self.success_response(
                message="Audio is now playing",
                data={
                    "play_count": audio.play_count,
                    "audio": serializer.data 
                }
            )      
            
        except Audio.DoesNotExist:
            return self.error_response(
                message="Audio not found. Please check the audio ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )               

class CategoryListView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get all categories with their audios
        categories = Category.objects.all()
        result = []
        
        for category in categories:
            audios = Audio.objects.filter(category=category).order_by("-created_at")
            audio_serializer = AudioSerializer(audios, many=True, context={"request": request})
            
            result.append({
                "category_id": category.id,
                "category_name": category.name,
                "total_audios": audios.count(),
                "audios": audio_serializer.data
                
            })
        
        return self.success_response(
            message="All categories with their audios retrieved successfully",
            data=result
        )

 
class CategoryView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, category_name=None):
        if category_name:
            # Filter by specific category from URL parameter
            try:
                category = Category.objects.get(name=category_name)
                audios = Audio.objects.filter(category=category).order_by("-created_at")
                audio_serializer = AudioSerializer(audios, many=True, context={"request": request})
                
                return self.success_response(
                    message=f"Audios for category '{category_name}' retrieved successfully",
                    data={
                        "category_id": category.id,
                        "category_name": category.name,
                        "audios": audio_serializer.data,
                        "total_audios": audios.count()
                    }
                )
            except Category.DoesNotExist:
                return self.error_response(
                    message=f"Category '{category_name}' not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get all categories with their audios
            categories = Category.objects.all()
            result = []
            
            for category in categories:
                audios = Audio.objects.filter(category=category).order_by("-created_at")
                audio_serializer = AudioSerializer(audios, many=True, context={"request": request})
                
                result.append({
                    "total_audios": audios.count(),
                    "category_id": category.id,
                    "category_name": category.name,
                    "audios": audio_serializer.data,
                    "total_audios": audios.count()
                })
            
            return self.success_response(
                message="All categories with their audios retrieved successfully",
                data=result
            )  
        

class FollowCategoryCreateView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return self.error_response(
                message="Category not found. Please check the category ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        follow, created = FollowCategory.objects.get_or_create(
            user=request.user, category=category
        )
        if created:
            return self.success_response(
                message=f"You are now following the category: {category.name}",
                status_code=status.HTTP_201_CREATED
            )
        return self.success_response(
            message=f"You are already following the category: {category.name}"
        )


class FollowCategoryDeleteView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return self.error_response(
                message="Category not found. Please check the category ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        deleted, _ = FollowCategory.objects.filter(
            user=request.user, category=category
        ).delete()
        if deleted:
            return self.success_response(
                message=f"You have unfollowed the category: {category.name}"
            )
        return self.error_response(
            message="You were not following this category"
        )


class FollowCategoryListView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        follows = FollowCategory.objects.filter(user=request.user)
        serializer = FollowCategorySerializer(follows, many=True)
        return self.success_response(
            message="Your followed categories retrieved successfully",
            data=serializer.data
        )


class NotificationListView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all notifications for the logged in user"""
        notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
        serializer = NotificationSerializer(notifications, many=True, context={"request": request})
        return self.success_response(
            message="Your notifications retrieved successfully",
            data=serializer.data
        )

class NotificationMarkReadView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """Mark a notification as read"""
        try:
            notif = Notification.objects.get(id=pk, user=request.user)
            notif.is_read = True
            notif.save(update_fields=["is_read"])
            return self.success_response(
                message="Notification marked as read successfully"
            )
        except Notification.DoesNotExist:
            return self.error_response(
                message="Notification not found. Please check the notification ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
    def delete(self, request, pk):
        """Delete a notification"""
        try:
            notif = Notification.objects.get(id=pk, user=request.user)
            notif.delete()
            return self.success_response(
                message="Notification deleted successfully",
                data={"deleted_id": pk}
            )
        except Notification.DoesNotExist:
            return self.error_response(
                message="Notification not found or you don't have permission.",
                status_code=status.HTTP_404_NOT_FOUND
            )        

        
class TrendingAudioView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        last_week = timezone.now() - timedelta(days=7)
        audios = Audio.objects.filter(created_at__gte=last_week).order_by("-play_count", "-created_at")
        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return self.success_response(
            message="Trending audios from the last week retrieved successfully",
            data=serializer.data
        )


class TopAllStoriesView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        audios = Audio.objects.order_by("-play_count", "-created_at")
        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return self.success_response(
            message="Top stories retrieved successfully",
            data=serializer.data
        )


class PopularAudioView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        audios = Audio.objects.order_by("-play_count")
        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return self.success_response(
            message="Popular audios retrieved successfully",
            data=serializer.data
        )


class RecommendedAudioView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        last_history = History.objects.filter(user=request.user).order_by("-played_at").first()
        if last_history and last_history.audio.category:
            audios = Audio.objects.filter(category=last_history.audio.category).exclude(history__user=request.user)
        else:
            audios = Audio.objects.all().order_by("?")  # fallback = random

        serializer = AudioSerializer(audios, many=True, context={"request": request})
        return self.success_response(
            message="Recommended audios based on your listening history retrieved successfully",
            data=serializer.data
        )

      
class LikeToggleView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            audio = Audio.objects.get(pk=pk)
            like = Like.objects.filter(user=request.user, audio=audio).first()

            if like:
                # already liked → unlike
                like.delete()
                return self.success_response(
                    message="Audio unliked successfully",
                    data={
                        "is_liked": False,
                        "total_like": Like.objects.filter(audio=audio).count()
                    }
                )
            else:
                # not liked → like
                Like.objects.create(user=request.user, audio=audio)
                return self.success_response(
                    message="Audio liked successfully",
                    data={
                        "is_liked": True,
                        "total_like": Like.objects.filter(audio=audio).count()
                    }
                )

        except Audio.DoesNotExist:
            return self.error_response(
                message="Audio not found. Please check the audio ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        

class CommentView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]

    # GET all comments
    def get(self, request, pk):
        try:
            audio = Audio.objects.get(pk=pk)
        except Audio.DoesNotExist:
            return self.error_response(
                message="Audio not found. Please check the audio ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        comments = Comment.objects.filter(audio=audio).order_by("-created_at")
        serializer = CommentSerializer(comments, many=True, context={"request": request})
        
        return self.success_response(
            message="Comments retrieved successfully",
            data={
                "total_comments": comments.count(),
                "comments": serializer.data
            }
        )

    # POST new comment
    def post(self, request, pk):
        try:
            audio = Audio.objects.get(pk=pk)
        except Audio.DoesNotExist:
            return self.error_response(
                message="Audio not found. Please check the audio ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CommentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user, audio=audio)
            return self.success_response(
                message="Comment added successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        return self.error_response(
            message="Failed to add comment. Please check your input.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class CommentDetailView(BaseAPIView):
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
            return self.error_response(
                message="You are not authorized to edit this comment or comment not found",
                status_code=status.HTTP_403_FORBIDDEN
            )
        serializer = CommentSerializer(comment, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                message="Comment updated successfully",
                data=serializer.data
            )
        return self.error_response(
            message="Failed to update comment. Please check your input.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # DELETE comment
    def delete(self, request, comment_id):
        comment = self.get_object(comment_id, user=request.user)
        if not comment:
            return self.error_response(
                message="You are not authorized to delete this comment or comment not found",
                status_code=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return self.success_response(
            message="Comment deleted successfully"
        )


class PlayListView(BaseAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PlayListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return self.success_response(
                message="Playlist created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        return self.error_response(
            message="Failed to create playlist. Please check your input.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def get(self, request):
        playlists = Playlist.objects.filter(user=request.user)
        serializer = PlayListSerializer(playlists, many=True)
        
        return self.success_response(
            message="Your playlists retrieved successfully",
            data=serializer.data
        )
          

class AddAudioToPlaylistView(BaseAPIView):    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, playlist_id):
        try:
            playlist = Playlist.objects.get(id=playlist_id, user=request.user)
        except Playlist.DoesNotExist:
            return self.error_response(
                message="Playlist not found. Please check the playlist ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        audio_ids = request.data.get("audio_ids", [])
        if not audio_ids:
            return self.error_response(
                message="No audio IDs provided. Please specify audio_ids in your request.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        added_audios = []
        for audio_id in audio_ids:
            try:
                audio = Audio.objects.get(id=audio_id)
                playlist.audios.add(audio)
                added_audios.append(audio.title)
            except Audio.DoesNotExist:
                continue

        return self.success_response(
            message=f"Successfully added {len(added_audios)} audio(s) to your playlist",
            data={
                "playlist_id": playlist.id,
                "added_audios": added_audios,
                "total_audios": playlist.audios.count()
            }
        )
        
        
class DownloadListView(BaseAPIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # --- Auto delete older than 7 days ---
        seven_days_ago = timezone.now() - timedelta(days=7)
        Download.objects.filter(created_at__lt=seven_days_ago).delete()

        # --- Return only last 7 days ---
        downloads = Download.objects.filter(
            user=request.user,
            created_at__gte=seven_days_ago
        ).order_by('-created_at')

        serializer = DownloadSerializer(downloads, many=True, context={'request': request})
        return self.success_response(
            message="Download list retrieved successfully",
            data=serializer.data
        )   
        
        
class DownloadCreateView(BaseAPIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, audio_id):
       
        seven_days_ago = timezone.now() - timedelta(days=7)
        Download.objects.filter(created_at__lt=seven_days_ago).delete()

   
        try:
            audio = Audio.objects.get(pk=audio_id)
        except Audio.DoesNotExist:
            return self.error_response(
                message="Audio not found. Please check the audio ID.",
                status_code=status.HTTP_404_NOT_FOUND
            )

    
        existing = Download.objects.filter(
            user=request.user,
            audio=audio,
            created_at__gte=seven_days_ago
        ).first()

        if existing:
            serializer = DownloadSerializer(existing, context={'request': request})
            return self.success_response(
                message="Audio already in your download list (within 7 days)",
                data=serializer.data
            )

 
        download = Download.objects.create(user=request.user, audio=audio)
        serializer = DownloadSerializer(download, context={'request': request})

        return self.success_response(
            message="Audio added to your download list successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
        
        
class DownloadDeleteView(BaseAPIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        Download.objects.filter(created_at__lt=seven_days_ago).delete()

        try:
            download = Download.objects.get(pk=pk, user=request.user)
            download.delete()
            return self.success_response(
                message="Download deleted successfully",
                data={"deleted_id": pk}
            )
        except Download.DoesNotExist:
            return self.error_response(
                message="Download not found or you don't have permission.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        
class AudioSearchView(BaseAPIView):
    """
    Search functionality + return history in same response
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '')

        results = []  # search result list

        if query:
            # search result
            audios = Audio.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            ).order_by('-created_at')

            # save history
            SearchHistory.objects.create(user=request.user, query=query)

            results = AudioSerializer(audios, many=True, context={'request': request}).data

        # Always include history
        histories = SearchHistory.objects.filter(user=request.user).order_by('-created_at')
        history_data = SearchHistorySerializer(histories, many=True).data

        return self.success_response(
            message="Search results & history retrieved successfully",
            data={
                 "history": history_data,
                "results": results  
               
            }
        )



class SearchHistoryDeleteView(BaseAPIView):
    """
    হিস্টোরি থেকে একটি কুয়েরি ডিলিট করা (pk URL থেকে)
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            history = SearchHistory.objects.get(pk=pk, user=request.user)
            history.delete()
            return self.success_response(
                message="History deleted successfully",
                data={"deleted_id": pk}
            )
        except SearchHistory.DoesNotExist:
            return self.error_response(
                message="History not found or you don't have permission.",
                status_code=status.HTTP_404_NOT_FOUND
            ) 
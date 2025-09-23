from django.contrib import admin
from .models import Audio, Playlist, History, Like, Comment, Follow, Download, Category, Notification, FollowCategory

# Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

# Audio
@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "artist", "category", "play_count", "is_premium", "created_at")
    list_filter = ("category", "is_premium", "created_at")
    search_fields = ("title", "artist", "description")
    readonly_fields = ("play_count",)

# # Playlist
# @admin.register(Playlist)
# class PlaylistAdmin(admin.ModelAdmin):
#     list_display = ("id", "name", "user")
#     search_fields = ("name", "user__email")
#     filter_horizontal = ("audios",)

# History
@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "audio", "played_at", "last_viewed", "completed")
    list_filter = ("completed", "played_at")
    search_fields = ("user__email", "audio__title")

# Like
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "audio", "created_at")
    search_fields = ("user__email", "audio__title")
    list_filter = ("created_at",)

# Comment
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "audio", "text", "created_at")
    search_fields = ("user__email", "audio__title", "text")
    list_filter = ("created_at",)

# # Follow
# @admin.register(Follow)
# class FollowAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "artist", "created_at")
#     search_fields = ("user__email", "artist__email")
#     list_filter = ("created_at",)

# # Download
# @admin.register(Download)
# class DownloadAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "audio", "created_at")
#     search_fields = ("user__email", "audio__title")
#     list_filter = ("created_at",)


# @admin.register(FollowCategory)
# class FollowCategoryAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "category", "created_at")
#     list_filter = ("category", "created_at")
#     search_fields = ("user__full_name", "category__name")


# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "audio", "message", "is_read", "created_at")
#     list_filter = ("is_read", "created_at")
#     search_fields = ("user__full_name", "audio__title", "message")
#     readonly_fields = ("created_at",)
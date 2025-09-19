from django.urls import path
from .views import (
    AudioListView,
    AudioPlayView,
    TrendingAudioView,
    PopularAudioView,
    RecommendedAudioView,
    LikeView,
    UnlikeView,
    CommentView,
    PlayListView,
    TopAllStoriesView,
    NotificationListView,
    NotificationMarkReadView,
    FollowCategoryCreateView,
    FollowCategoryDeleteView,
    FollowCategoryListView,
    CommentDetailView,
    AddAudioToPlaylistView,
    CategoryListView,
    CategoryView
)

urlpatterns = [
    # Audio
    path("audios/", AudioListView.as_view(), name="audio-list"),
    path("audios/<int:pk>/play/", AudioPlayView.as_view(), name="audio-play"),

    # Trending / Top Story / Popular / Recommended
    path("audios/trending/", TrendingAudioView.as_view(), name="trending-audios"),
    path("audios/top/", TopAllStoriesView.as_view(), name="top-all-stories"),
    path("audios/popular/", PopularAudioView.as_view(), name="popular-audios"),
    path("audios/recommended/", RecommendedAudioView.as_view(), name="recommended-audios"),
    
    path('categories/', CategoryListView.as_view(), name='categories-list'),
    path('categories/<str:category_name>/', CategoryView.as_view(), name='category-audios'),

    # Likes
    path("audios/<int:pk>/like/", LikeView.as_view(), name="like-audio"),
    path("audios/<int:pk>/unlike/", UnlikeView.as_view(), name="unlike-audio"),

    # Comments
     path("audios/<int:pk>/comments/", CommentView.as_view(), name="audio_comments"),
    path("comments/<int:comment_id>/", CommentDetailView.as_view(), name="comment_detail"),

    # Playlists
    path("playlists/", PlayListView.as_view(), name="playlists"),
    path("playlists/<int:playlist_id>/add-story/", AddAudioToPlaylistView.as_view(), name="add_audios_to_playlist"),
    
# Category follow/unfollow
    path("categories/follow/<int:category_id>/", FollowCategoryCreateView.as_view(), name="follow_category"),
    path("categories/unfollow/<int:category_id>/", FollowCategoryDeleteView.as_view(), name="unfollow_category"),
    path("categories/followed/", FollowCategoryListView.as_view(), name="followed_categories"),

    # Notifications
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification_mark_read"),
]

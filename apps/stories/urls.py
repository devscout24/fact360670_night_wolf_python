from django.urls import path
from .views import (
    AudioListView,
    AudioPlayView,
    TrendingAudioView,
    PopularAudioView,
    RecommendedAudioView,
    LikeToggleView,
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
    CategoryView,
    NotificationListView,
    AudioDetailsView,
    DownloadCreateView,
    DownloadListView,
    DownloadDeleteView,
    AudioSearchView,
    SearchHistoryDeleteView,
)

urlpatterns = [
    #Notificatiuons
     path("notifications/", NotificationListView.as_view(), name="notification-list"),
    
    # Audio
    path("audios/", AudioListView.as_view(), name="audio-list"),
    path("audios/<int:pk>/play/", AudioPlayView.as_view(), name="audio-play"),
    path("audios/<int:pk>/details/", AudioDetailsView.as_view(), name="audio-play"),
    
    #Downloades
    path('downloads/', DownloadListView.as_view(), name='download-list'),
    path('downloads/<int:audio_id>/create/', DownloadCreateView.as_view(), name='download-create'),
    path('downloads/<int:pk>/delete/', DownloadDeleteView.as_view(), name='download-delete'),
    
    #Search
    path('search/', AudioSearchView.as_view(), name='audio-search'),
    path('search/history/<int:pk>/delete/', SearchHistoryDeleteView.as_view(), name='search-history-delete'),

    # Trending / Top Story / Popular / Recommended
    path("audios/trending/", TrendingAudioView.as_view(), name="trending-audios"),
    path("audios/top/", TopAllStoriesView.as_view(), name="top-all-stories"),
    path("audios/popular/", PopularAudioView.as_view(), name="popular-audios"),
    path("audios/recommended/", RecommendedAudioView.as_view(), name="recommended-audios"),
    
    path('categories/', CategoryListView.as_view(), name='categories-list'),
    path('categories/<str:category_name>/', CategoryView.as_view(), name='category-audios'),

    # Likes
     path("audios/<int:pk>/like-toggle/", LikeToggleView.as_view(), name="audio-like-toggle"),

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
    path("notifications/<int:pk>/", NotificationMarkReadView.as_view(), name="notification_mark_read"),
]

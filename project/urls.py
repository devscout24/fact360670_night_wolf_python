from django.http import HttpResponse
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    return HttpResponse("Django is working on SleepCast server!")


urlpatterns = [
      path('', home),
      path('admin/', admin.site.urls),
      path('api/auth/', include('apps.user.urls')),
      path('api/story/', include('apps.stories.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
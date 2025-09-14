from django.db import models

# Create your models here.
from apps.user.models import User

class Category(models.Model):
    name= models.CharField(max_length=150)
    
    def __str__(self):
        return self.name


class Audio (models.Model):
    title= models.CharField(max_length=200)
    artist= models.CharField(max_length=150)
    description= models.TextField(null=True, blank= True)
    cover_image= models.ImageField(upload_to='cover/', null=True, blank= True)
    audio_file= models.FileField(upload_to='audios/')
    duration= models.DurationField(null=True, blank= True)
    category= models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    
    play_count= models.PositiveIntegerField(default=0)
    is_featured= models.BooleanField(default=False)
    created_at= models.DateTimeField(auto_now_add= True)
    
    def increment_play(self):
        self.play_count+=1
        self.save(update_fields=["play_count"])
    
    def __str__(self):
        return self.title
    
class FollowCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followed_categories")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'category')  

    def __str__(self):
        return f"{self.user.full_name} follows {self.category.name}"
    
class Notification(models.Model):
    user= models.ForeignKey(User, on_delete= models.CASCADE, related_name='notifications')
    audio= models.ForeignKey(Audio, on_delete= models.CASCADE)
    message= models.CharField(max_length=400)
    is_read= models.BooleanField(default=False)
    created_at= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.user}-{self.message}"    
    
    
class Playlist(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    audios = models.ManyToManyField(Audio, related_name="playlists")
    name= models.CharField(max_length=150)
    
    def __str__(self):
     return f"{self.user.full_name} - {self.name}"

    
class History(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    audio= models.ForeignKey(Audio, on_delete=models.CASCADE)
    played_at= models.DateTimeField(auto_now_add=True)
    last_viewed= models.DateTimeField(auto_now=True)
    duration_played= models.FloatField(default=0)
    completed= models.BooleanField(default=False)
    
class Like(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)   
    audio= models.ForeignKey(Audio, on_delete= models.CASCADE)
    created_at= models.DateTimeField(auto_now_add=True)     
    
    
class Comment( models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    audio= models.ForeignKey(Audio, on_delete=models.CASCADE)
    text= models.TextField()
    created_at= models.DateTimeField(auto_now_add=True)
    
class Follow(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower")
    artist= models.ForeignKey(User, on_delete= models.CASCADE, related_name="following")
    created_at= models.DateTimeField(auto_now_add=True)
    
class Download(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    audio= models.ForeignKey(Audio, on_delete=models.CASCADE)
    created_at= models.DateTimeField(auto_now_add=True)
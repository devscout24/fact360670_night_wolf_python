import threading
from apps.user.models import User
from apps.stories.models import Notification



def create_audio_notifications(audio):
    """Background thread task for audio notifications"""
    def task():
        users = User.objects.all()
        notifications = [
            Notification(
                user=user,
                audio=audio,
                message=f"New story uploaded: {audio.title}"
            )
            for user in users
        ]
        Notification.objects.bulk_create(notifications)
    threading.Thread(target=task).start()


def create_category_notifications(category):
    """Background thread task for category notifications"""
    def task():
        users = User.objects.all()
        notifications = [
            Notification(
                user=user,
                category=category,
                message=f"New category added: {category.name}"
            )
            for user in users
        ]
        Notification.objects.bulk_create(notifications)
    threading.Thread(target=task).start()

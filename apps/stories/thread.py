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


def create_subscription_notification(user):
    """Background thread task for subscription notifications"""
    def task():
        if user.subscription and user.subscription.is_active():
            months_left = user.subscription.months_left()
            message = f"You Have {months_left} Months Left On Your Subscription."

            Notification.objects.create(
                user=user,
                message=message,
                # audio/category ফাঁকা থাকবে
            )

    threading.Thread(target=task).start()

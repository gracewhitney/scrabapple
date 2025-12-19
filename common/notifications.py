from common.models import Notification


def create_notification(user, notification_type, text, url):
    Notification.objects.create(user=user, notification_type=notification_type, notification_text=text, view_url=url)

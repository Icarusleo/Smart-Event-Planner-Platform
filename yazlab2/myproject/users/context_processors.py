from .models import Notification

def notifications_context(request):
    """
    Bildirimleri tüm şablonlara eklemek için bir context processor.
    """
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        unread_count = notifications.filter(is_read=False).count()
        return {
            'notifications': notifications[:5],  # İlk 5 bildirimi gönder
            'unread_count': unread_count  # Okunmamış bildirim sayısı
        }
    return {'notifications': [], 'unread_count': 0}
from django.urls import path
from . import views

urlpatterns = [
    # Etkinlikleri listele (GET isteği)
    path('events/', views.get_events, name='get_events'),  

    # Yeni etkinlik ekle (POST isteği)
    path('homepage/', views.create_event, name='create_event'),
    
    # (Opsiyonel) Kullanıcıya ait etkinlikleri listeleme
    path('user-events/', views.get_user_events, name='get_user_events'),  # Kullanıcıya ait etkinlikleri listele
]

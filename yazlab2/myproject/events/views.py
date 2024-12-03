from django.shortcuts import render
from django.http import JsonResponse
from .models import Event
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.utils import timezone

# Etkinlikleri listeleme (GET isteği)
@login_required
def get_events(request):
    events = Event.objects.all()
    events_list = []
    for event in events:
        event_data = {
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'event_date': event.event_date.strftime('%Y-%m-%d %H:%M'),  # Formatlı tarih
            'user_username': event.user.username,
        }
        events_list.append(event_data)
    return JsonResponse(events_list, safe=False)

# Yeni etkinlik ekleme (POST isteği)
@login_required
def create_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        location = request.POST.get('location')
        event_date = request.POST.get('event_date')

        # Form verisi doğrulama
        if not title or not description or not location or not event_date:
            return JsonResponse({'status': 'error', 'message': 'Tüm alanlar gereklidir!'})

        # Event tarihini doğru formatta alalım
        try:
            event_date = parse_datetime(event_date)
            if event_date is None or event_date < timezone.now():
                return JsonResponse({'status': 'error', 'message': 'Geçersiz etkinlik tarihi!'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Geçersiz tarih formatı!'})

        # Etkinliği kaydetme
        event = Event(
            title=title,
            description=description,
            location=location,
            event_date=event_date,
            user=request.user
        )
        event.save()

        return JsonResponse({'status': 'success', 'message': 'Etkinlik başarıyla eklendi!'})

    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek!'})

@login_required
def get_user_events(request):
    user_events = Event.objects.filter(user=request.user)  # Sadece giriş yapan kullanıcının etkinlikleri
    events_list = []
    for event in user_events:
        event_data = {
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'event_date': event.event_date.strftime('%Y-%m-%d %H:%M'),  # Formatlı tarih
            'user_username': event.user.username,
        }
        events_list.append(event_data)
    return JsonResponse(events_list, safe=False)


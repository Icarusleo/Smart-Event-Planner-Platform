from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import User,Event,UserInterests,Participation,Comment,Messages,Notification    
from django.views.decorators.csrf import csrf_exempt
import random ,datetime,math,json
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from .forms import UserEditForm , EventForm, UserInterestsForm, RegisterForm, CommentForm
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy,reverse
from django.http import HttpResponseForbidden , HttpResponseRedirect
from django.db.models.signals import post_save
from django.dispatch import receiver


def base_view(request):
   return render(request,'base.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            user.score = calculate_score(user)
            user.save()
            if user.is_admin:
                login(request, user)
                return redirect('admin_dashboard')
            else:    
                login(request, user)
                return redirect('homepage')  
        else:
            messages.error(request, "Geçersiz kullanıcı adı veya şifre.")
            return render(request, 'login.html')  
    else:
        return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('homepage') 

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False) 
            user.set_password(form.cleaned_data['password']) 
            user.score = calculate_score(user)
            user.save()
            form.save_m2m() 
            messages.success(request, "Kayıt başarılı! Giriş yapabilirsiniz.")
            return redirect('login')
        else:
            messages.error(request, "Kayıt sırasında bir hata oluştu. Lütfen bilgilerinizi kontrol edin.")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def password_reset_view(request):
    return render(request, 'password_reset.html')

@csrf_exempt
def send_verification_code(request):
    
    if request.method == 'POST':
        email = request.POST.get('email')
        users = User.objects.all()
        user = next((u for u in users if u.email == email), None)
        if user:
            verification_code = random.randint(100000, 999999)
            user.verification_code = verification_code
            user.save()
            send_mail(
                'Şifre Sıfırlama Kodu',
                f'Sıfırlama kodunuz: {verification_code}',
                'your_email@example.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success', 'message': 'Kod e-posta adresine gönderildi.'})
        return JsonResponse({'status': 'error', 'message': 'E-posta adresi bulunamadı.'})

@csrf_exempt   
def verify_code(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        code = request.POST.get('code')
        user = User.objects.filter(email=email, verification_code=code).first()
        if user:
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Doğrulama kodu geçersiz.'})
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek.'})

@csrf_exempt
def password_reset_complete(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        user = User.objects.filter(email=email).first()
        if user:
            user.set_password(new_password)
            user.verification_code = None
            user.save()
            return JsonResponse({
                'status': 'success', 
                'message': 'Şifre başarıyla değiştirildi.',
                'redirect_url': '/login/'  
            })
    return JsonResponse({'status': 'error', 'message': 'Geçersiz işlem.'})

@login_required
def edit_profile(request):
    user = request.user  
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES,user=user, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profiliniz başarıyla güncellendi.')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Lütfen formu doğru bir şekilde doldurun.')
    else:
        form = UserEditForm(user=user, instance=user)

    return render(request, 'edit_profile.html', {'form': form})

def edit_user_interests(request):
    user_interests, created = UserInterests.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserInterestsForm(request.POST, instance=user_interests)
        if form.is_valid():
            form.save()
            return redirect('edit_profile')  
    else:
        form = UserInterestsForm(instance=user_interests)

    return render(request, 'edit_user_interests.html', {'form': form})

def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        request_user = request.user
        user.delete()
        messages.success(request, 'Kullanıcı başarıyla silindi!')
        if request_user.is_admin:
            return redirect('admin_dashboard')
        else:
            return redirect('event_list')
    return render(request, 'delete_user.html', {'user': user})

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'password_reset.html'
    success_url = reverse_lazy('edit_profile')

def homepage(request):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            body = json.loads(request.body)
            user_latitude = float(body.get('latitude', 0))
            user_longitude = float(body.get('longitude', 0))
            print(user_latitude)
            user = request.user
            user.score = calculate_score(user)
            user.save()
            recommended_events = event_recommendation(request.user)

            def calculate_distance(event):
                if event.latitude and event.longitude:
                    return math.sqrt(
                        (event.latitude - user_latitude) ** 2 + (event.longitude - user_longitude) ** 2
                    )
                return float('inf')

            sorted_recommended_events = sorted(
                recommended_events,
                key=lambda event: calculate_distance(event)
            )

            response_data = [
                {
                    'id': event.id,
                    'title': event.title,
                    'latitude': event.latitude,
                    'longitude': event.longitude,
                    'description' : event.description,
                    'category': event.category,
                    'date': event.date.strftime('%Y-%m-%d'),
                    'start_time': event.start_time.strftime('%H:%M:%S'),
                    'end_time': event.end_time.strftime('%H:%M:%S'),
                }
                for event in sorted_recommended_events
            ]
            return JsonResponse({'recommended_events': response_data}, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    events = Event.objects.filter(approved=True)
    recommended_events = (
        event_recommendation(request.user) if request.user.is_authenticated else events
    )
    events_list = list(events.values('id', 'title', 'latitude', 'longitude', 'category', 'date', 'start_time', 'end_time'))
    return render(request, 'homepage.html', {'recommended_events': recommended_events, 'events': events_list})

def events_json(request):
    events = Event.objects.filter(approved=True).values(
        'id', 'title', 'latitude', 'longitude', 'category', 'date', 'start_time', 'end_time'
    )
    return JsonResponse(list(events), safe=False)

@login_required
def create_event(request):
    if request.method == 'POST':
        print(request.POST)
        form = EventForm(request.POST)
        if form.is_valid():
            print("Form geçerli.") 
            user = request.user
            event = form.save(commit=False)
            event.created_by = user  
            event.latitude = form.cleaned_data['latitude']
            event.longitude = form.cleaned_data['longitude']
            conflict_check = check_event_overlap(user, event)
            if conflict_check['status'] == 'conflict':
                messages.error(request, "Etkinliği güncelleyemezsiniz! Çakışan etkinlikler var.")
                return render(request, 'update_event.html', {
                    'form': form,
                    'initial_position': {
                        "latitude": event.latitude if event.latitude else 39.92077,
                        "longitude": event.longitude if event.longitude else 32.85411
                    },
                    'event': event
                })

            event.save()
            user.score = calculate_score(user)
            user.save()
            messages.success(request, "Etkinlik başarıyla oluşturuldu!")
            return redirect('event_list')
        else:
            print(form.errors) 
    else:
        form = EventForm()

    return render(request, 'create_event.html', {'form': form})

@login_required
def update_event(request, event_id):
    user = request.user
    event = Event.objects.get(id=event_id)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            updated_event = form.save(commit=False)
            updated_event.created_by = request.user

            
            if user.is_admin:
                conflict_check = {'status': 'ok'}
            else:
                conflict_check = check_event_overlap(request.user, updated_event, exclude_event=event)
            if conflict_check['status'] == 'conflict':
                messages.error(request, "Etkinliği güncelleyemezsiniz! Çakışan etkinlikler var.")
                return render(request, 'update_event.html', {
                    'form': form,
                    'initial_position': {
                        "latitude": event.latitude if event.latitude else 39.92077,
                        "longitude": event.longitude if event.longitude else 32.85411
                    },
                    'event': event
                })

            updated_event.save()
            messages.success(request, 'Etkinlik başarıyla güncellendi.')
            return redirect('event_list')
    else:
        form = EventForm(instance=event)

    initial_position = {
        "latitude": event.latitude if event.latitude else 39.92077,
        "longitude": event.longitude if event.longitude else 32.85411
    }
    return render(request, 'update_event.html', {'form': form, 'initial_position': initial_position, 'event': event})

@login_required
def delete_event(request, event_id):
    event = Event.objects.get(id=event_id, created_by=request.user)
    if request.method == 'POST':
        user = request.user
        event.delete()
        user.score = calculate_score(user)
        user.save()
        messages.success(request, 'Etkinlik başarıyla silindi.')
        if user.is_admin:
            return redirect('admin_dashboard')
        else:
            return redirect('event_list')
    return render(request, 'delete_event.html', {'event': event})

@login_required
def event_list(request):
    events = Event.objects.filter(created_by=request.user)
    return render(request, 'event_list.html', {'events': events})

@login_required
def get_user_events(request):
    user_events = Event.objects.filter(user=request.user)  
    events_list = []
    for event in user_events:
        event_data = {
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'event_date': event.event_date.strftime('%Y-%m-%d %H:%M'), 
            'user_username': event.user.username,
        }
        events_list.append(event_data)
    return JsonResponse(events_list, safe=False)

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    comments = event.comments.all().order_by('-created_at')  
    
    comments = event.comments.all().order_by('-created_at') 
    if request.user.is_authenticated:
        is_participant = Participation.objects.filter(event=event, user=request.user).exists()
    else:
        is_participant = False
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.event = event
            comment.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = CommentForm()

    context = {
        'event': event,
        'comments': comments,
        'form': form,
        'is_participant': is_participant
    }
    return render(request, 'event_detail.html',context )

@csrf_exempt
def delete_comment(request, comment_id):
    if request.method == 'POST' and request.user.is_authenticated:
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.user == request.user:
            comment.delete()
            return JsonResponse({'status': 'success', 'message': 'Yorum silindi.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Bu yorumu silme yetkiniz yok.'})
    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek.'})
    
@csrf_exempt    
def join_event(request, event_id):
    if request.method == 'POST' and request.user.is_authenticated:
        event = get_object_or_404(Event, id=event_id)

        overlap_check = check_event_overlap(request.user, event)
        if overlap_check['status'] == 'conflict':
            messages.error(request, "Etkinlik zaman çakışması var!")
            return HttpResponseRedirect(reverse('event_detail', args=[event_id]))

        participation, created = Participation.objects.get_or_create(user=request.user, event=event)
        user = request.user
        user.score = calculate_score(user)
        user.save()
        if created:
            messages.success(request, "Etkinliğe başarıyla katıldınız.")
        else:
            messages.warning(request, "Zaten bu etkinliğe katıldınız.")
        
        return HttpResponseRedirect(reverse('event_detail', args=[event_id]))

    messages.error(request, "Geçersiz işlem.")
    return HttpResponseRedirect(reverse('event_detail', args=[event_id]))

def check_event_overlap(user, new_event):
   
    print(f"Kullanıcı: {user.username}, Yeni Etkinlik: {new_event.title}")
    user_participations = Participation.objects.filter(user=user, event__date=new_event.date)
    user_events = [participation.event for participation in user_participations]
    conflicts = []
    for event in user_events:
        print(f"Kontrol edilen etkinlik: {event.title} ({event.start_time} - {event.end_time})")
        if (
        (new_event.start_time < event.end_time and new_event.end_time > event.start_time) or
        (new_event.start_time < event.start_time and new_event.end_time > event.end_time) or
        (event.start_time < new_event.start_time and new_event.end_time < event.end_time) or
        (new_event.start_time == event.start_time and new_event.end_time == event.end_time) or
        (new_event.start_time == event.end_time or new_event.end_time == event.start_time) or
        (abs((new_event.start_time - event.end_time).total_seconds()) < 900 or
         abs((new_event.end_time - event.start_time).total_seconds()) < 900)
    ):
            conflicts.append({
                "event_title": event.title,
                "date": event.date,
                "start_time": event.start_time,
                "end_time": event.end_time,
            })

    if conflicts:
        print(f"Çakışan etkinlikler: {conflicts}")
        return {"status": "conflict", "conflicts": conflicts}
    else:
        return {"status": "ok", "message": "Çakışma yok."}
    
def check_event_overlap(user, new_event, exclude_event=None):
    
    user_participations = Participation.objects.filter(
        user=user, 
        event__date=new_event.date
    ).exclude(event=exclude_event) 
    user_events = [participation.event for participation in user_participations]

    conflicts = []
    for event in user_events:
        if ((new_event.start_time < event.end_time and new_event.end_time > event.start_time) or
            (new_event.start_time < event.start_time and new_event.end_time > event.end_time) or 
            (event.start_time < new_event.start_time and new_event.end_time < event.end_time) or
            (new_event.start_time == event.start_time and new_event.end_time == event.end_time) or
        (new_event.start_time == event.end_time or new_event.end_time == event.start_time) or
        (abs((new_event.start_time - event.end_time).total_seconds()) < 900 or
         abs((new_event.end_time - event.start_time).total_seconds()) < 900)):
            conflicts.append({
                "event_title": event.title,
                "date": event.date,
                "start_time": event.start_time,
                "end_time": event.end_time,
            })

    if conflicts:
        return {"status": "conflict", "conflicts": conflicts}
    else:
        return {"status": "ok", "message": "Çakışma yok."}

def event_recommendation(user):
   
    user_interests = UserInterests.objects.get(user=user).interests.values_list('name', flat=True)
    print(user_interests)
 
    user_participations = Participation.objects.filter(user=user)
    user_event_categories = {participation.event.category for participation in user_participations}

    recommended_events = Event.objects.filter(category__in=user_interests)
    print(f"İlgi alanlarına uygun etkinlikler: {[event.title for event in recommended_events]}")
    additional_events = Event.objects.exclude(
        participation__user=user 
    ).filter(
        category__in=user_event_categories  
    )

    attended_events = get_attended_events(user)
    
    recommendations = set(recommended_events) | set(additional_events)
    
    final_recommendations = set()
    for i in recommendations:
        if i.approved  :
            if list(attended_events).__contains__(i):
                continue
            else:
                final_recommendations.add(i)
        
    return final_recommendations

@login_required        
def admin_dashboard(request):
    events = Event.objects.all()  
    users = User.objects.all() 
    pending_events = Event.objects.filter(approved=False)  

    context = {
        'events': events,
        'users': users,
        'pending_events': pending_events,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def approve_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.approved = True
    event.save()
    messages.success(request, "Etkinlik onaylandı.")
    return redirect('admin_dashboard')

@login_required
def reject_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, "Etkinlik reddedildi ve silindi.")
    return redirect('admin_dashboard')

@login_required
def admin_user_update(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        user.is_active = 'is_active' in request.POST
        user.save()
        messages.success(request, "Kullanıcı başarıyla güncellendi.")
        return redirect('admin_dashboard')
    return render(request, 'admin_user_update.html', {'chosen_user': user})

@login_required
def edit_profile2(request,user_id):
    user = get_object_or_404(User, id=user_id) 
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES,user=user, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil başarıyla güncellendi.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Lütfen formu doğru bir şekilde doldurun.')
    else:
        form = UserEditForm(user=user, instance=user)

    return render(request, 'edit_profile.html', {'form': form})

def events_messages(request):
    user = request.user
    if user.is_admin:
        attended_events=Messages.objects.all()
    else:
        attended_events = get_attended_events(user)
    return render(request, 'messages.html',{'messages':attended_events})

def attended_events(request):
    user = request.user
    print(user)
    attended_events = get_attended_events(user)
    return render(request,'attended_events.html',{'events': attended_events})


def get_attended_events(user):
    return Event.objects.filter(participation__user=user)

def event_messages(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    messages = Messages.objects.filter(event=event).order_by('-created_at')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Messages.objects.create(event=event, user=request.user, content=content)
            return JsonResponse({'status': 'success', 'message': 'Mesaj gönderildi.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Mesaj içeriği boş olamaz.'})

    return render(request, 'event_messages.html', {'event': event, 'messages': messages})

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Messages, id=message_id, user=request.user)
    if request.method == 'POST':
        message.delete()
        return JsonResponse({'status': 'success', 'message': 'Mesaj başarıyla silindi.'})
    return JsonResponse({'status': 'error', 'message': 'Mesaj silinemedi.'})

@csrf_exempt
def cancel_attend(request,event_id):
    user = request.user
    attend = get_object_or_404(Participation,event=event_id,user=user)
    if request.method == 'POST':
        attend.delete()  
        messages.success(request, 'Etkinlikten başarıyla ayrıldınız.')
        user.score = calculate_score(user)
        user.save()
        return redirect('attended_events')  

    messages.error(request, 'Geçersiz istek.')
    return redirect('attended_events')
    
def send_message_notification(event, sender, message_content):
    participants = Participation.objects.filter(event=event).exclude(user=sender)  
    participant_users = participants.values_list('user', flat=True) 
    for participation in participants:
        Notification.objects.create(
            user=participation.user,
            message=f"{event.title} etkinliğinde yeni bir mesaj: {message_content}"
        )
        

def notifications_context(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        unread_count = notifications.filter(is_read=False).count()
        return {'notifications': notifications[:5], 'unread_count': unread_count}  
    return {'notifications': [], 'unread_count': 0}

@login_required
def mark_notification_as_read(request, notification_id):
    
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.get_absolute_url())

def send_message(request, event_id):
    ...
    event = get_object_or_404(Event, id=event_id)
    participants = Participation.objects.filter(event=event).exclude(user=request.user)
    for participant in participants:
        Notification.objects.create(
            user=participant.user,
            message=f"'{event.title}' etkinliğinde yeni bir mesaj var!"
        )
    ...


def notifications_list(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'notification_list.html', {'notifications': notifications})
    return redirect('login')

def create_message_notification(message):
    event = message.event
    sender = message.user

    participants = Participation.objects.filter(event=event).exclude(user=sender)
    
    notifications = []
    for participant in participants:
        notifications.append(Notification(
            user=participant.user,
            event=event,
            message=message,
            content=f"{sender.username} yeni bir mesaj gönderdi: {message.content[:30]}..."
        ))
    
    Notification.objects.bulk_create(notifications)
    
@receiver(post_save, sender=Messages)
def create_notifications_for_message(sender, instance, created, **kwargs):
    if created:
        create_message_notification(instance)
        
def calculate_score(user):
    first_score = 20
    events_attended = get_attended_events(user)
    events_created = Event.objects.filter(created_by=user)
    return (first_score+(10*events_attended.count())+(15*events_created.count()))

def show_participations(request,event_id):
    event = get_object_or_404(Event, id=event_id)
    participations = Participation.objects.filter(event=event)
    return render(request,'participations_list.html',{'participations':participations ,'event':event})

def admin_cancel_attend(request,event_id,participation_id):
    attend = get_object_or_404(Participation,id=participation_id)
    attend.delete()  
    return redirect('admin_dashboard')  

def admin_attended_events(request,user_id):
    user = get_object_or_404(User,id=user_id)
    attended_events = get_attended_events(user)
    print(attended_events)
    return render(request,'admin_attended_events.html',{'events': attended_events,'selecteduser' : user})
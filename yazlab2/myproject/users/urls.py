from django.contrib import admin
from django.urls import path
from users import views
from django.conf import settings
from django.conf.urls.static import static
from .views import CustomPasswordChangeView

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('send_verification_code/', views.send_verification_code, name='send_verification_code'),  
    path('verify_code/', views.verify_code, name='verify_code'),  
    path('password_reset_complete/', views.password_reset_complete, name='password_reset_complete'), 
    path('homepages/', views.create_event, name='create_event'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/edit-interests/',views.edit_user_interests,name='edit_user_interests'),
    path('profile/change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/update/<int:event_id>/',views.update_event, name='update_event'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('event/created/',views.event_list,name='event_list'),
    path('user-events/', views.get_user_events, name='get_user_events'),  
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/join/', views.join_event, name='join_event'),
    path('event/<int:event_id>/participations', views.show_participations, name='participation_list'),
    path('event/<int:event_id>/participations/cancel<int:participation_id>', views.admin_cancel_attend, name='admin_cancel_Event'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('users/<int:user_id>/edit/', views.edit_profile2, name='admin_user_edit'),
    path('events/<int:event_id>/approve/', views.approve_event, name='approve_event'),
    path('events/<int:event_id>/reject/', views.reject_event, name='reject_event'),
    path('attended-events/', views.attended_events, name='attended_events'),
    path('attended-events/<int:user_id>', views.admin_attended_events, name='admin_attended_events'),
    path('event/<int:event_id>/messages/', views.event_messages, name='event_messages'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('events-json/',views.events_json,name='evets-json'),
    path('cancel-attend/<int:event_id>/',views.cancel_attend,name='cancel_attend'),
    path('notification/read/<int:notification_id>/', views.mark_notification_as_read, name='mark_as_read'),
    path('notification-list',views.notifications_list,name='notifications_list')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
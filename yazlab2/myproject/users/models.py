from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.hashers import make_password  
from django.conf import settings
from django.utils.timezone import now 

# Create your models here.

class User(AbstractUser):
    id = models.AutoField(primary_key=True)  
    username = models.CharField(max_length=150,unique=True)
    password = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    surname = models.CharField(max_length=150)
    birthdate = models.DateField(max_length=150)
    gender = models.CharField(max_length=150)
    email = models.EmailField(max_length=150,unique=True)
    phone_number = models.CharField(max_length=128)
    interests = models.CharField(max_length=150)
    profilepicture=models.ImageField(upload_to='uploads/profile_pictures/', null=True, blank=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    location = models.CharField(max_length=100,default="İstanbul")
    latitude = models.FloatField(blank=True, null=True)  # Enlem
    longitude = models.FloatField(blank=True, null=True)  # Boylam
    is_admin = models.BooleanField(default=False)
    score = models.IntegerField(default=20)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_groups',  # Özel ilişkili ad
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_permissions',  # Özel ilişkili ad
        blank=True,
    )
    

class Event(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    date = models.DateField(default=now)
    start_time = models.TimeField(default=now)
    end_time = models.TimeField(default=now)
    latitude = models.FloatField(blank=True, null=True)  # Enlem
    longitude = models.FloatField(blank=True, null=True)  # Boylam
    category = models.CharField(max_length=100, default="Genel") 
    approved = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_events",
        default=1  # Varsayılan kullanıcı ID'si
    )
    def save(self, *args, **kwargs):
        # Saniye kısmını sıfırla
        if self.start_time:
            self.start_time = self.start_time.replace(second=0, microsecond=0)
        if self.end_time:
            self.end_time = self.end_time.replace(second=0, microsecond=0)
        super(Event, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.title

    
class Interest(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
   
class Participation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    participation_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'event')

class UserInterests(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    interests = models.ManyToManyField(Interest)
    def __str__(self):
        return f"{self.user.username}'s Interests"
    
class Comment(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
    
class Messages(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}..."
    
class Notification(models.Model):
    user = models.ForeignKey(User, default=0,on_delete=models.CASCADE, related_name='notifications')
    event = models.ForeignKey(Event,default=0,on_delete=models.CASCADE)  # İlgili etkinlik
    message = models.ForeignKey('Messages', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField(default='') 
    created_at = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)  # Bildirim okundu mu?

    def get_absolute_url(self):
        """
        Bildirime tıklandığında gidilecek URL.
        Eğer bir mesaja bağlıysa mesaj sayfasına yönlendirin.
        """
        if self.message:
            return f"/event/{self.event.id}/messages/#{self.message.id}"
        return f"/event/{self.event.id}/messages/"
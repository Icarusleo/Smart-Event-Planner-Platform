from django import forms
from .models import User,Event,UserInterests,Interest

from django import forms
from .models import User, Interest, UserInterests,Comment

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Şifre', 'class': 'form-control'}),
        label="Şifre"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Şifreyi Onayla', 'class': 'form-control'}),
        label="Şifreyi Onayla"
    )
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="İlgi Alanları"
    )

    class Meta:
        model = User
        fields = [
            'username', 'password', 'name', 'surname', 'email',
            'birthdate', 'gender', 'phone_number', 'profilepicture'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Kullanıcı Adı', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ad', 'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'placeholder': 'Soyad', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'E-posta', 'class': 'form-control'}),
            'birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(choices=[('Male', 'Erkek'), ('Female', 'Kadın')], attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Telefon Numarası', 'class': 'form-control'}),
            'profilepicture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            self.add_error('confirm_password', 'Şifreler eşleşmiyor.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super(RegisterForm, self).save(commit=False)
        instance.set_password(self.cleaned_data['password'])  # Şifreyi hashle
        if commit:
            instance.save()

           
            interests = self.cleaned_data['interests']
            user_interests = UserInterests.objects.create(user=instance)
            user_interests.interests.set(interests)
            user_interests.save()

        return instance


class UserEditForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),  
        widget=forms.CheckboxSelectMultiple, 
        required=False, 
        label="İlgi Alanları" 
    )

    class Meta:
        model = User
        fields = [
            'username', 'name', 'surname', 'birthdate',
            'gender', 'email', 'phone_number', 
            'profilepicture', 'location'
        ]
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(choices=[('Male', 'Erkek'), ('Female', 'Kadın')]),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super(UserEditForm, self).__init__(*args, **kwargs)

        if user:
            user_interests = UserInterests.objects.filter(user=user).first()
            if user_interests:
                self.fields['interests'].initial = user_interests.interests.all()

    def save(self, commit=True):

        instance = super(UserEditForm, self).save(commit=False)

        if commit:
            instance.save()  

            interests = self.cleaned_data['interests']
            user_interests, created = UserInterests.objects.get_or_create(user=instance)
            user_interests.interests.set(interests)  
            user_interests.save()
        
        return instance
        

class EventForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Interest.objects.all(),  
        empty_label="Bir kategori seçin",
        label="Kategori",
        widget=forms.Select(attrs={'class': 'form-control'}) 
    )

    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'start_time','end_time',  'latitude', 'longitude', 'category']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'latitude': forms.HiddenInput(),  
            'longitude': forms.HiddenInput(), 
        }
        
class UserInterestsForm(forms.ModelForm):
    class Meta:
        model = UserInterests
        fields = ['interests']
        widgets = {
            'interests': forms.CheckboxSelectMultiple,  
        }      
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Yorumunuzu yazın...', 'rows': 4}),
        } 

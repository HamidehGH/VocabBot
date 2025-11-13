from django import forms
from .models import Vocabulary, UserProfile, VocabularyImage
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory


class CustomRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label="username",
        widget=forms.TextInput(attrs={'class': 'form-control eng-alignmant'}))
    password = forms.CharField(min_length= 8, label="password", strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control eng-alignmant'}),
        error_messages={'min_length':'minimum lenght is 8 characters'})
    password2 = forms.CharField(label="Password confirmation", strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control eng-alignmant'}))

    # Checks if the username is already taken
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    # Checks that the two password fields match.
    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    # Creates the User and updates the related UserProfile.
    def save(self, commit=True):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = UserProfile.objects.create(
            username = username,
            password = password,
        )
        return user



class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150,widget=forms.TextInput(attrs={'class': 'form-control eng-alignmant'}))
    password = forms.CharField(max_length=150,widget=forms.PasswordInput(attrs={'class': 'form-control eng-alignmant'}))

    class Meta:
        model = User
        fields = ['username', 'password']



class VocabularyForm(forms.ModelForm):
    class Meta:
        model = Vocabulary
        fields = ['word', 'meaning', 'description']
        widgets = {
            'word': forms.TextInput(attrs={'class': 'form-control'}),
            'meaning': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control','rows': 4}),
        }

# Creates a formset for managing multiple images related to a Vocabulary
VocabularyImageFormSet = inlineformset_factory(
    Vocabulary,             
    VocabularyImage,        
    fields=['image', 'caption'], 
    extra=1, 
    min_num=1,       
    can_delete=True,      
    widgets={
        'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        'caption': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Where did you see this word?', 'rows': 4}),
    },
)


class AdminUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user', 'chat_id']















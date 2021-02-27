from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from account.models import Account, Group


class AccountAuthenticationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ('email', 'password')

    def clean(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']
            if not authenticate(email=email, password=password):
                raise forms.ValidationError('Invalid Login')

    def clean_email(self):
        data = self.cleaned_data['email']
        return data.lower()


class AccountUpdateForm(forms.ModelForm):
    email = forms.EmailField(max_length=60,
                             help_text='Required. Add a valid email address')

    class Meta:
        model = Account
        fields = ('email', 'username', 'first_name', 'last_name')

    def clean_email(self):
        data = self.cleaned_data['email']
        return data.lower()

    def __init__(self, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class AccountView(forms.ModelForm):
    class Meta:
        model = Account
        exclude = ['password']

    def __init__(self, *args, **kwargs):
        super(AccountView, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=60,
                             help_text='Required. Add a valid email address')

    class Meta:
        model = Account
        exclude = ['is_superuser', 'is_active', 'profile_picture_path', 'is_accepted', 'password']

    def clean_email(self):
        data = self.cleaned_data['email']
        return data.lower()

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class ChangePasswordForm(UserCreationForm):
    class Meta:
        model = Account
        fields = ['password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList

from .models import Account, PatientInformation, Image, SurgeryInformation, ProcedureCodes, EventLog, Group


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


class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('email', 'username', 'first_name', 'last_name', 'profile_picture_path')

    def clean_email(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            try:
                account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
            except Account.DoesNotExist:
                return email
            raise forms.ValidationError('Email "%s" is already in use.' % email)

    def clean_username(self):
        if self.is_valid():
            username = self.cleaned_data['username']
            try:
                account = Account.objects.exclude(pk=self.instance.pk).get(username=username)
            except Account.DoesNotExist:
                return username
            raise forms.ValidationError('Username "%s" is already in use.' % username)

    def clean_first_name(self):
        if self.is_valid():
            first_name = self.cleaned_data['first_name']
            return first_name

    def clean_last_name(self):
        if self.is_valid():
            last_name = self.cleaned_data['last_name']
            return last_name

    def clean_profile_picture_path(self):
        if self.is_valid():
            profile_picture_path = self.cleaned_data['profile_picture_path']
            return profile_picture_path

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


class AddPatient(forms.ModelForm):
    class Meta:
        model = PatientInformation
        exclude = [
            'uploaded',
            'number_of_surgeries',
            'slug'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'first_name': forms.TextInput(attrs={'required': 'true'}),
            'last_name': forms.TextInput(attrs={'required': 'true'})
        }

    def __init__(self, *args, **kwargs):
        super(AddPatient, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if visible.name != 'in_waiting_room':
                visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['rows'] = '4'


class CSVForm(forms.Form):
    date_start = forms.DateField()
    date_end = forms.DateField()
    fields = forms.TextInput(attrs=None)


class EmailForm(forms.Form):
    to = forms.CharField(widget=forms.TextInput, help_text='Separate with Commas')
    cc = forms.CharField(widget=forms.TextInput, required=False, help_text='Separate with Commas')
    bcc = forms.CharField(widget=forms.TextInput, required=False, help_text='Separate with Commas')
    from_email = forms.EmailInput()
    title = forms.CharField(widget=forms.TextInput, required=False, help_text='Optional')
    message = forms.CharField(widget=forms.Textarea, required=False, help_text='Optional')

    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['rows'] = '4'


class EventLogForm(forms.ModelForm):
    class Meta:
        model = EventLog
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EventLogForm, self).__init__(*args, **kwargs)
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


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image', 'date_of_upload_image')
        widgets = {
            'date_of_upload_image': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'})
        }


class PatientView(forms.ModelForm):
    class Meta:
        model = PatientInformation
        exclude = ['patient_image', 'injury_image', 'slug']


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = ProcedureCodes
        fields = ('procedure_codes',)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=60,
                             help_text='Required. Add a valid email address')

    class Meta:
        model = Account
        exclude = ['is_superuser', 'is_active', 'profile_picture_path', 'is_accepted', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class SurgeryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SurgeryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if visible.name != 'consent':
                visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['rows'] = '4'

    class Meta:
        model = SurgeryInformation
        exclude = [
            'date_of_upload',
            'is_approved',
            'is_denied',
            'reason'
        ]
        widgets = {
            'date_of_admission': forms.DateInput(attrs={'type': 'date'}),
            'date_of_discharge': forms.DateInput(attrs={'type': 'date'}),
            'date_of_evaluation': forms.DateInput(attrs={'type': 'date'}),
            'date_of_surgery': forms.DateInput(attrs={'type': 'date'}),
            'consent': forms.CheckboxInput(attrs={'class': 'form-check'}),
            'type_of_sponsor': forms.Select(choices=[
                ('', ''),
                ('Resurge', 'Resurge'),
                ('HUI', 'HUI'),
                ('Private', 'Private'),
                ('Government', 'Government'),
                ('Third Party', 'Third Party'),
                ('Other', 'Other'),
            ], attrs={'onchange': 'selected(\'type_of_sponsor\')'}),
            'cause_of_burn': forms.Select(choices=[
                ('', ''),
                ('Accidental', 'Accidental'),
                ('Suicidal', 'Suicidal'),
                ('Homicidal', 'Homicidal'),
            ]),
            'type_of_burn': forms.Select(choices=[
                ('', ''),
                ('Scald Burn', 'Scald Burn'),
                ('Open Flame', 'Open Flame'),
                ('Chemical Burn', 'Chemical Burn'),
                ('Gasoline Burn', 'Gasoline Burn'),
                ('Electrical Burn', 'Electrical Burn'),
                ('Contact Burn', 'Contact Burn'),
                ('Other', 'Other'),
            ], attrs={'onchange': 'selected(\'type_of_burn\')'})
        }


class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return '<div class="d-flex justify-content-center align-items-center" style="padding-bottom: 5px">%s</div>' % ''.join(
            ['<div class="alert alert-danger w-100" style="margin: 0"><strong>%s</strong></div>' % e for e in self])


class AddImage(forms.ModelForm):
    class Meta:
        model = Image
        fields = '__all__'
        widgets = {
            'date_of_upload_image': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'})
        }


class ReportForm(forms.Form):
    title = forms.CharField(label='Title', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}),
                            required=True)
    description = forms.CharField(label='Description', widget=forms.Textarea(attrs={'class': 'form-control'}),
                                  required=True)


class WaitingRoomForm(forms.ModelForm):
    class Meta:
        model = PatientInformation
        fields = ['first_name', 'last_name', 'age', 'address', 'story']

    def __init__(self, *args, **kwargs):
        super(WaitingRoomForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['rows'] = '3'

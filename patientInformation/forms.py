from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

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


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=60,
                             help_text='Required. Add a valid email address')

    class Meta:
        model = Account
        exclude = ['is_superuser', 'is_active', 'profile_picture_path', 'is_accepted']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class AddPatient(forms.ModelForm):
    class Meta:
        model = PatientInformation
        fields = [
            'patient_record_number',
            'patient_image',
            'injury_image',
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'age',
            'gender',
            'address',
            'telephone_number',
            'parents',
            'relationship',
            'parent_occupation',
            'diagnosis',
            'weight',
            'height',
            'burn_injury',
            'cleft_injury',
            'hand_injury',
            'prior_surgery',
            'doctor_notes',
            'story'
        ]

    def __init__(self, *args, **kwargs):
        super(AddPatient, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image', 'date_of_upload_image')


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = ProcedureCodes
        fields = ('procedure_codes',)


class SurgeryForm(forms.ModelForm):
    class Meta:
        model = SurgeryInformation
        fields = [
            'patient',
            'hospital',
            'referral',
            'patient_district',
            'type_of_sponsor',
            'drug_allergy',
            'name_of_evaluation',
            'date_of_evaluation',
            'cause_of_burn',
            'year_of_burn',
            'type_of_burn',
            'diagnosis_admission',
            'date_of_admission',
            'date_of_surgery',
            'date_of_discharge',
            'surgeons',
            'details_of_surgery',
            'anesthesiologist',
            'anesthesia',
            'duration',
            'burn_operation_number',
            'type_of_surgery',
            'area_operated',
            'complications',
            'consent',
        ]

    def __init__(self, *args, **kwargs):
        super(SurgeryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class CSVForm(forms.Form):
    date_start = forms.DateField()
    date_end = forms.DateField()
    fields = forms.TextInput(attrs=None)


class EmailForm(forms.Form):
    to = forms.TextInput()
    cc = forms.TextInput()
    bcc = forms.TextInput()
    from_email = forms.EmailInput()
    title = forms.TextInput()
    message = forms.TextInput()


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


class AccountView(forms.ModelForm):
    class Meta:
        model = Account
        exclude = ['password']

    def __init__(self, *args, **kwargs):
        super(AccountView, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

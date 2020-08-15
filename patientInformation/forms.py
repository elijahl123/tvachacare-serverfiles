from django import forms
from django.contrib.auth import authenticate

from .models import Account, PatientInformation


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


class AddPatient(forms.ModelForm):
    class Meta:
        model = PatientInformation
        fields = [
            'firstName',
            'lastName',
            'patientRecordNumber',
            'preferredName',
            'dateOfBirth',
            'ageAtSurgery',
            'patientSex',
            'siteCountry',
            'siteRegion',
            'hospitalName',
            'preoperativeDiagnostic1',
            'preoperativeDiagnostic2',
            'preoperativeDiagnostic3',
            'preoperativeDiagnostic4',
            'burnInjury',
            'TBSA',
            'degreeOfBurn',
            'causeOfBurn',
            'approximateYearOfInjury',
            'occupation',
            'patientAddress',
            'patientPhoneNumber',
            'parentFirstName',
            'parentMiddleName',
            'parentLastName',
            'relationshipToParent',
            'referral',
            'patientWeight',
            'patientHeight',
            'currentMedication',
            'patient_image',
            'injury_image',
        ]

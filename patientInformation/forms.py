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

    def clean_profile_picture_path(self):
        if self.is_valid():
            profile_picture_path = self.cleaned_data['profile_picture_path']
            return profile_picture_path


class AddPatient(forms.ModelForm):
    class Meta:
        model = PatientInformation
        fields = [
            'registration_number',
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'age',
            'gender',
            'race',
            'address',
            'telephone_number',
            'parents',
            'relationship',
            'hospital',
            'referral',
            'diagnosis',
            'weight',
            'height',
            'prior_surgery',
            'drug_allergy',
            'name_of_evaluation',
            'date_of_evaluation',
            'cause_of_burn',
            'year_of_burn',
            'diagnosis_admission',
            'date_of_admission',
            'date_of_surgery',
            'date_of_discharge',
            'surgeons',
            'anesthesiologist',
            'anesthesia',
            'duration',
            'burn_operation_number',
            'type_of_surgery',
            'area_operated',
            'complications'
        ]

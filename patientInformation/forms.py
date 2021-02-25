from django import forms
from django.forms.utils import ErrorList

from .models import PatientInformation, Image, SurgeryInformation, ProcedureCodes, EventLog


class AddPatient(forms.ModelForm):
    class Meta:
        model = PatientInformation
        exclude = [
            'uploaded',
            'number_of_surgeries',
            'slug',
            'age'
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
            'reason',
            'approver'
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
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'surgery': forms.Select(attrs={'class': 'form-control'})
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

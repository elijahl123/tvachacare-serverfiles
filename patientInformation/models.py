#  Copyright (c) 2020 Elijah Lopez
#
#  TvachaCare grants to you a personal, non-exclusive, non-assignable and
#  non-transferable license to use and display the software provided by
#  or on behalf of TvachaCare (including any updates) only for the purpose
#  of accessing the Service ("Software") on any computer(s) on which you
#  are the primary user or which you are authorized to use. Our Privacy
#  Policies provide important information about the Software applications
#  we utilize. Please read the terms very carefully, as they contain important
#  disclosures about the use and security of data transmitted to and from
#  your computer. Unauthorized copying of the Software, including, without
#  limitation, software that has been modified, merged or included with
#  the Software, or the written materials associated therewith, is expressly
#  forbidden. You may not sublicense, assign, or transfer this license or
#  the Software except as permitted in writing by TvachaCare. Any attempt
#  to sublicense, assign or transfer any of the rights, duties or obligations
#  under this license is void and may result in termination by TvachaCare
#  of this license. You agree that you shall not copy or duplicate or permit
#  anyone else to copy or duplicate any part of the Software, or create
#  or attempt to create, or permit others to create or attempt to create,
#  by reverse engineering or otherwise, the source programs or any part
#  thereof from the object programs or from other information made available
#  under this Agreement.
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#

import datetime
import uuid

from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, QuerySet
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver

from account.models import Account
from base.models import BaseModel


def upload_location(instance, filename):
    file_path = 'patientInformation/{surgery}/{filename}'.format(
        surgery=str(instance.surgery), filename=filename)
    return file_path


def upload_patient_images(instance, filename):
    file_path = 'patientInformation/{patient_record_number}/{filename}'.format(
        patient_record_number=str(instance.patient_record_number), filename=filename
    )
    return file_path


def upload_profile_picture(instance, filename):
    file_path = 'profilePictures/{username}/{filename}'.format(
        username=str(instance.username), filename=filename
    )
    return file_path


# Create your models here.
class PatientInformation(models.Model):
    admin_form = 'AddPatient'

    different_fields = ['patient_image', 'injury_image']

    SEXCHOICES = [('Female', 'Female'), ('Male', 'Male')]
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    uploaded = models.DateField(auto_now_add=True, verbose_name='date of upload')
    patient_record_number = models.SlugField(blank=True, null=True, unique=True)
    patient_image = models.ImageField(null=True, blank=True, upload_to=upload_patient_images)
    injury_image = models.ImageField(null=True, blank=True, upload_to=upload_patient_images)
    first_name = models.CharField(max_length=120, blank=True, null=True)
    middle_name = models.CharField(max_length=120, blank=True, null=True)
    last_name = models.CharField(max_length=120, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(blank=True, max_length=6, choices=SEXCHOICES, default='male')
    address = models.TextField(blank=True, null=True)
    telephone_number = models.CharField(max_length=15, blank=True, null=True)
    parents = models.TextField(blank=True, null=True)
    relationship = models.CharField(max_length=120, blank=True, null=True)
    parent_occupation = models.TextField(null=True, blank=True)
    diagnosis = models.TextField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    burn_injury = models.TextField(blank=True, null=True, verbose_name='Burn Injury?')
    cleft_injury = models.TextField(blank=True, null=True, verbose_name='Cleft Injury?')
    hand_injury = models.TextField(blank=True, null=True, verbose_name='Hand Injury?')
    prior_surgery = models.TextField(blank=True, null=True, verbose_name='Prior Surgery?')
    doctor_notes = models.TextField(blank=True, null=True)
    story = models.TextField(blank=True, null=True)
    slug = models.SlugField(default=uuid.uuid4, editable=False)
    in_waiting_room = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    def surgery_count(self):
        return SurgeryInformation.objects.filter(patient=self).count()

    def surgeries(self) -> QuerySet:
        return SurgeryInformation.objects.filter(patient=self)

    class Meta:
        ordering = ['last_name']
        unique_together = ['first_name', 'last_name', 'date_of_birth']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'


class SurgeryGroup(models.Model):
    name = models.CharField(max_length=120, null=True, blank=False, unique=True)
    description = models.TextField(blank=True, null=True)
    locked = models.BooleanField(default=False)
    threshold = models.PositiveIntegerField(default=25, help_text='Percentage of surgeries required to be reviewed')

    def __str__(self):
        return self.name

    def percent_completed(self):
        threshold = self.threshold / 100
        goal = round(self.surgery_count() * threshold)
        approved = SurgeryInformation.objects.filter(group=self, is_approved=True).count()
        try:
            out = int((approved / goal) * 100)
            return out if out <= 100 else 100
        except ZeroDivisionError:
            return 100

    def surgery_count(self):
        return SurgeryInformation.objects.filter(group=self).count()

    def surgery_count_formatted(self):
        count = self.surgery_count()
        if count > 1:
            return f'{count} Surgeries'
        return f'{count} Surgery'


class SurgeryInformation(models.Model):
    admin_form = 'SurgeryForm'

    DURATION_CHOICES = [
        ('Up to 1 Hour', 'Up to 1 Hour'),
        ('1.5 - 2 Hours', '1.5 - 2 Hours'),
        ('2-3 Hours', '2-3 Hours'),
        ('3+ Hours', '3+ Hours')
    ]
    patient = models.ForeignKey('PatientInformation', on_delete=models.CASCADE)
    date_of_upload = models.DateField(auto_now_add=True, verbose_name='date of upload')
    group = models.ForeignKey(SurgeryGroup, on_delete=models.SET_NULL, null=True, blank=True,
                              limit_choices_to={'locked': False})
    hospital = models.TextField(blank=True, null=True)
    referral = models.CharField(max_length=120, blank=True, null=True)
    patient_district = models.CharField(blank=True, null=True, max_length=120)
    type_of_sponsor = models.TextField(blank=True, null=True)
    drug_allergy = models.TextField(blank=True, null=True)
    name_of_evaluation = models.CharField(max_length=120, blank=True, null=True)
    date_of_evaluation = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)
    cause_of_burn = models.TextField(blank=True, null=True)
    year_of_burn = models.IntegerField(blank=True, null=True)
    type_of_burn = models.CharField(max_length=120, blank=True, null=True)
    diagnosis_admission = models.TextField(blank=True, null=True)
    date_of_admission = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)
    date_of_surgery = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)
    date_of_discharge = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)
    surgeons = models.TextField(blank=True, null=True)
    anesthesiologist = models.CharField(max_length=120, blank=True, null=True)
    anesthesia = models.CharField(max_length=120, blank=True, null=True)
    duration = models.CharField(max_length=120, blank=True, null=True, choices=DURATION_CHOICES)
    burn_operation_number = models.SlugField(null=True, blank=True)
    type_of_surgery = models.TextField(blank=True, null=True)
    area_operated = models.CharField(max_length=120, blank=True, null=True)
    complications = models.TextField(blank=True, null=True)
    consent = models.BooleanField(default=False, verbose_name='Does this patient give consent for photos?')
    is_approved = models.BooleanField(default=False, blank=True, null=True)
    is_denied = models.BooleanField(default=False, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    approver = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    number_of_procedures = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])

    def __str__(self):
        return str(self.id)

    def status(self):
        if self.is_approved:
            return 'Approved'
        elif self.is_denied:
            return 'Denied'
        else:
            return 'Awaiting Approval'

    class Meta:
        ordering = ['-date_of_upload']
        verbose_name = 'Surgery'
        verbose_name_plural = 'Surgeries'


class Image(models.Model):
    different_fields = ['surgery']
    admin_form = 'AddImage'

    surgery = models.ForeignKey('SurgeryInformation', on_delete=models.CASCADE, null=True, blank=False)
    image = models.ImageField(null=True, blank=True, upload_to=upload_location)
    date_of_upload_image = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)

    def __str__(self):
        try:
            url = self.image.url
        except ValueError:
            url = None
        return url

    class Meta:
        ordering = ['-date_of_upload_image']
        verbose_name = 'Image'
        verbose_name_plural = 'Images'


class ProcedureCodes(models.Model):
    surgery = models.ForeignKey('SurgeryInformation', on_delete=models.CASCADE, null=True, blank=True)
    procedure_codes = models.TextField(blank=True, null=True, verbose_name='Procedures')


class EventLog(BaseModel):
    admin_form = 'EventLogForm'

    COLOR_CHOICES = [
        ('success', 'success'),
        ('danger', 'danger'),
        ('tvachacare', 'tvachacare'),
    ]

    ICON_CHOICES = [
        ('fas fa-plus', 'fas fa-plus'),
        ('fas fa-minus', 'fas fa-minus'),
        ('fas fa-check', 'fas fa-check'),
        ('fas fa-times', 'fas fa-times'),
        ('fas fa-edit', 'fas fa-edit')
    ]

    event_type = models.CharField(blank=True, null=True, max_length=60)
    event_time = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=120, default='tvachacare', choices=COLOR_CHOICES)
    icon = models.CharField(max_length=120, default='fas fa-edit', choices=COLOR_CHOICES)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.event_type

    class Meta:
        ordering = ['-event_time']
        verbose_name = 'Event Log'
        verbose_name_plural = 'Event Logs'


class Appeal(BaseModel):
    uploaded = models.DateTimeField(auto_now_add=True)
    surgery = models.ForeignKey(SurgeryInformation, on_delete=models.CASCADE, null=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.message

    class Meta:
        ordering = ['-uploaded']


@receiver(post_delete, sender=Image)
def submission_delete(sender, instance, **kwargs):
    instance.image.delete(True)


@receiver(post_save, sender=PatientInformation)
def patient_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        event_type = 'Add Patient'
        event_notes = f'Patient {instance.patient_record_number} was uploaded'
        color = 'success'
        icon = 'fas fa-plus'
    else:
        event_type = 'Edit Patient'
        event_notes = f'Patient {instance.patient_record_number} was edited'
        color = 'tvachacare'
        icon = 'fas fa-edit'

    event = EventLog(event_type=event_type, notes=event_notes, color=color, icon=icon)
    event.save()


@receiver(post_save, sender=SurgeryInformation)
def surgery_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        event_type = 'Add Surgery'
        event_notes = f'Surgery #{instance.id} was uploaded'
        color = 'success'
        icon = 'fas fa-plus'
    else:
        event_type = 'Edit Surgery'
        event_notes = f'Surgery #{instance.id} was edited'
        color = 'tvachacare'
        icon = 'fas fa-edit'

    event = EventLog(event_type=event_type, notes=event_notes, color=color, icon=icon)
    event.save()


@receiver(post_delete, sender=PatientInformation)
def patient_post_delete(sender, instance, **kwargs):
    event_notes = f'Patient {instance.patient_record_number} was deleted'
    event = EventLog(event_type='Patient Deleted', notes=event_notes, color='danger', icon='fas fa-minus')
    event.save()
    instance.patient_image.delete(True)
    instance.injury_image.delete(True)


@receiver(post_delete, sender=SurgeryInformation)
def surgery_post_delete(sender, instance, **kwargs):
    event_notes = f'Surgery #{instance.id} was deleted'
    event = EventLog(event_type='Surgery Deleted', notes=event_notes, color='danger', icon='fas fa-minus')
    event.save()


@receiver(post_save, sender=EventLog)
def submission_save(sender, instance, **kwargs):
    accounts = Account.objects.all()
    accounts.update(unread_activity=F('unread_activity') + 1)


@receiver(post_save, sender=Appeal)
def submission_save_appeals(sender, instance, **kwargs):
    accounts = Account.objects.all()
    accounts.update(unread_appeals=F('unread_appeals') + 1)


def calculate_age(birth_date):
    today = datetime.date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def pre_save_patient_information_receiver(sender, instance, *args, **kwargs):
    instance.age = calculate_age(instance.date_of_birth) if instance.date_of_birth else None


pre_save.connect(pre_save_patient_information_receiver, sender=PatientInformation)

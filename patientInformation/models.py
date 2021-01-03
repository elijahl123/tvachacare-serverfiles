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

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils.text import slugify


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
    slug = models.SlugField(blank=True, unique=True, null=True)
    in_waiting_room = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    def surgery_count(self):
        return SurgeryInformation.objects.filter(patient=self).count()

    class Meta:
        ordering = ['last_name']
        unique_together = ['first_name', 'last_name']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'


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
    number_of_procedures = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ['-date_of_upload']
        verbose_name = 'Surgery'
        verbose_name_plural = 'Surgeries'


class Image(models.Model):
    different_fields = ['surgery']
    admin_form = 'ImageForm'

    surgery = models.ForeignKey('SurgeryInformation', on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=upload_location)
    date_of_upload_image = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)


class ProcedureCodes(models.Model):
    surgery = models.ForeignKey('SurgeryInformation', on_delete=models.CASCADE, null=True, blank=True)
    procedure_codes = models.TextField(blank=True, null=True, verbose_name='Procedures')


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        if not first_name:
            raise ValueError('Users must have a First Name')
        if not last_name:
            raise ValueError('Users must have a Last Name')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser):
    admin_form = 'RegistrationForm'

    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    profile_picture_path = models.ImageField(upload_to=upload_profile_picture, null=True, blank=True)
    first_name = models.CharField(max_length=20, null=True)
    last_name = models.CharField(max_length=20, null=True)
    group = models.ForeignKey('Group', on_delete=models.CASCADE, default=1)
    is_accepted = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    class Meta:
        ordering = ['email']
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return self.email

        # For checking permissions. to keep it simple all admin have ALL permissions

    def has_perm(self, perm, obj=None):
        return self.is_admin

        # Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)

    def has_module_perms(self, app_label):
        return True


class Group(models.Model):
    admin_form = 'GroupForm'

    name = models.CharField(max_length=120, unique=True)
    can_approve = models.BooleanField(default=False)
    can_add_patients = models.BooleanField(default=False)
    can_add_surgeries = models.BooleanField(default=False)
    can_add_accounts = models.BooleanField(default=False)
    can_edit_patients = models.BooleanField(default=False)
    can_edit_surgeries = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'


class EventLog(models.Model):
    admin_form = 'EventLogForm'

    user = models.EmailField(blank=True, null=True)
    event_type = models.CharField(blank=True, null=True, max_length=60)
    event_time = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.event_type

    class Meta:
        ordering = ['-event_time']
        verbose_name = 'Event Log'
        verbose_name_plural = 'Event Logs'


@receiver(post_delete, sender=Image)
def submission_delete(sender, instance, **kwargs):
    instance.image.delete(True)


@receiver(post_delete, sender=PatientInformation)
def submission_delete(sender, instance, **kwargs):
    instance.patient_image.delete(True)
    instance.injury_image.delete(True)


def pre_save_patient_information_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify("HUI-" + str(abs(hash(str(datetime.datetime) + str(instance.id))) % (10 ** 10)))


pre_save.connect(pre_save_patient_information_receiver, sender=PatientInformation)

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
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
    SEXCHOICES = [('Female', 'Female'), ('Male', 'Male')]
    current_time = models.DateTimeField(auto_now=True)
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
    burn_injury = models.TextField(blank=True, null=True)
    cleft_injury = models.TextField(blank=True, null=True)
    hand_injury = models.TextField(blank=True, null=True)
    prior_surgery = models.TextField(blank=True, null=True)
    doctor_notes = models.TextField(blank=True, null=True)
    story = models.TextField(blank=True, null=True)
    slug = models.SlugField(blank=True, unique=True, null=True)
    is_approved = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class SurgeryInformation(models.Model):
    patient = models.ForeignKey('PatientInformation', on_delete=models.CASCADE)
    date_of_upload = models.DateField(auto_now_add=True, verbose_name='date of upload')
    hospital = models.TextField(blank=True, null=True)
    referral = models.CharField(max_length=120, blank=True, null=True)
    patient_district = models.IntegerField(blank=True, null=True)
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
    details_of_surgery = models.TextField(blank=True, null=True)
    anesthesiologist = models.CharField(max_length=120, blank=True, null=True)
    anesthesia = models.CharField(max_length=120, blank=True, null=True)
    duration = models.CharField(max_length=120, blank=True, null=True)
    burn_operation_number = models.SlugField(null=True, unique=True)
    type_of_surgery = models.TextField(blank=True, null=True)
    area_operated = models.CharField(max_length=120, blank=True, null=True)
    complications = models.TextField(blank=True, null=True)
    consent = models.BooleanField(default=False, verbose_name='Consent?')

    def __str__(self):
        return self.burn_operation_number


class Image(models.Model):
    surgery = models.ForeignKey('SurgeryInformation', on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=upload_location)


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
    GROUPS = [('Admin', 'Admin'), ('Approver', 'Approver'), ('Data Entry', 'Data Entry')]
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
    group = models.CharField(max_length=10, choices=GROUPS, default='Admin')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

        # For checking permissions. to keep it simple all admin have ALL permissions

    def has_perm(self, perm, obj=None):
        return self.is_admin

        # Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)

    def has_module_perms(self, app_label):
        return True


@receiver(post_delete, sender=Image)
def submission_delete(sender, instance, **kwargs):
    instance.image.delete(True)


@receiver(post_delete, sender=PatientInformation)
def submission_delete(sender, instance, **kwargs):
    instance.patient_image.delete(True)
    instance.injury_image.delete(True)


def pre_save_patient_information_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify("HUI-" + abs(hash(str(instance.current_time))) % (10 ** 10))


pre_save.connect(pre_save_patient_information_receiver, sender=PatientInformation)

# TODO: make it so that users can add fields

# TODO: make the csv thing

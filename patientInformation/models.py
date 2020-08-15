from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils.text import slugify


def upload_location(instance, filename):
    file_path = 'patientInformation/{patientRecordNumber}/{filename}'.format(
        patientRecordNumber=str(instance.patientRecordNumber), filename=filename)
    return file_path


def upload_profile_picture(instance, filename):
    file_path = 'profilePictures/{username}/{filename}'.format(
        username=str(instance.username), filename=filename
    )
    return file_path


# Create your models here.
class PatientInformation(models.Model):
    SEXCHOICES = [('Female', 'Female'), ('Male', 'Male')]
    firstName = models.CharField(blank=True, max_length=120, null=True)
    lastName = models.CharField(blank=True, max_length=120, null=True)
    patientRecordNumber = models.SlugField(blank=True, max_length=11, null=True, unique=True)
    preferredName = models.CharField(max_length=120, blank=True, null=True)
    dateOfBirth = models.DateField(blank=True, auto_now=False, auto_now_add=False, null=True)
    ageAtSurgery = models.IntegerField(blank=True, null=True)
    patientSex = models.CharField(blank=True, max_length=6, choices=SEXCHOICES, default='male')
    siteCountry = models.CharField(blank=True, max_length=120, null=True)
    siteRegion = models.CharField(blank=True, max_length=120, null=True)
    hospitalName = models.TextField(blank=True, null=True)
    preoperativeDiagnostic1 = models.TextField(blank=True, null=True)
    preoperativeDiagnostic2 = models.TextField(blank=True, null=True)
    preoperativeDiagnostic3 = models.TextField(blank=True, null=True)
    preoperativeDiagnostic4 = models.TextField(blank=True, null=True)
    burnInjury = models.BooleanField(blank=True, null=True, default=False)
    TBSA = models.FloatField(blank=True, null=True)
    degreeOfBurn = models.IntegerField(blank=True, null=True)
    causeOfBurn = models.TextField(blank=True, null=True)
    approximateYearOfInjury = models.IntegerField(blank=True, null=True)
    occupation = models.CharField(blank=True, max_length=120, null=True)
    patientAddress = models.TextField(blank=True, null=True)
    patientPhoneNumber = models.CharField(max_length=12, blank=True, null=True)
    parentFirstName = models.CharField(max_length=120, blank=True, null=True)
    parentMiddleName = models.CharField(max_length=120, blank=True, null=True)
    parentLastName = models.CharField(max_length=120, blank=True, null=True)
    relationshipToParent = models.CharField(max_length=120, blank=True, null=True)
    referral = models.CharField(max_length=120, blank=True, null=True)
    patientWeight = models.IntegerField(blank=True, null=True)
    patientHeight = models.IntegerField(blank=True, null=True)
    currentMedication = models.TextField(blank=True, null=True)
    patient_image = models.ImageField(upload_to=upload_location, null=True, blank=True)
    injury_image = models.ImageField(upload_to=upload_location, null=True, blank=True)
    slug = models.SlugField(blank=True, unique=True, null=True)
    is_approved = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.patientRecordNumber


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


@receiver(post_delete, sender=PatientInformation)
def submission_delete(sender, instance, **kwargs):
    instance.image1.delete(False)
    instance.image2.delete(False)
    instance.image3.delete(False)


def pre_save_patient_information_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.patientRecordNumber)


pre_save.connect(pre_save_patient_information_receiver, sender=PatientInformation)

# TODO: make it so that users can add fields

# TODO: make the csv thing

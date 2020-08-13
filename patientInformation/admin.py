from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PatientInformation, Account


# Register your models here.


class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'date_joined', 'last_login', 'is_admin', 'is_staff', 'group')
    search_fields = ('email', 'username')
    readonly_fields = ('date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class PatientAdmin(admin.ModelAdmin):
    list_display = ('firstName', 'lastName', 'patientRecordNumber', 'ageAtSurgery')
    search_fields = ('firstName', 'lastName', 'patientRecordNumber')
    readonly_fields = ()

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(Account, AccountAdmin)
admin.site.register(PatientInformation, PatientAdmin)

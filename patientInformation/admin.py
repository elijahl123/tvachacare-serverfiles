from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PatientInformation, Account, Image, SurgeryInformation, EventLog


# Register your models here.


class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'date_joined', 'last_login', 'is_admin', 'is_staff', 'group')
    search_fields = ('email', 'username')
    readonly_fields = ('date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'patient_record_number', 'slug')
    search_fields = ('first_name', 'last_name', 'patient_record_number', 'slug')
    readonly_fields = ()

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class SurgeryAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'burn_operation_number')
    search_fields = ('id', 'patient', 'burn_operation_number')
    readonly_fields = ()

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class EventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'event_time', 'notes')
    search_fields = ('user', 'event_type', 'event_time', 'notes')
    readonly_fields = ()

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(Account, AccountAdmin)
admin.site.register(PatientInformation, PatientAdmin)
admin.site.register(Image)
admin.site.register(SurgeryInformation, SurgeryAdmin)
admin.site.register(EventLog, EventAdmin)

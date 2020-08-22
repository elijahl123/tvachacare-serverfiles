from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PatientInformation, Account, Image


# Register your models here.


class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'date_joined', 'last_login', 'is_admin', 'is_staff', 'group')
    search_fields = ('email', 'username')
    readonly_fields = ('date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'registration_number', 'age')
    search_fields = ('first_name', 'last_name', 'registration_number')
    readonly_fields = ()

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(Account, AccountAdmin)
admin.site.register(PatientInformation, PatientAdmin)
admin.site.register(Image)

from django.contrib import admin
from .models import *


@admin.register(PatientInformation)
class PatientInformationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name')
    list_filter = ('last_name',)
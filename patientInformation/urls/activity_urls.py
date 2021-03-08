from django.urls import path

from patientInformation import views

urlpatterns = [
    path('', views.activity, name='activity')
]
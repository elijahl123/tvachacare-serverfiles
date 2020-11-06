"""TvachaCare URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path

from patientInformation import views

urlpatterns = [
    path('admin/', views.admin, name='admin-console'),
    path('', views.index, name='home'),
    path('login/', views.loginPage, name="login"),
    path('login/admin/', views.loginadmin, name="loginAdmin"),
    path('addpatient/', views.addpatient, name='addPatient'),
    path('logout', views.logout, name='logout'),
    path('patient/<slug>/', views.patient_page, name='patient_page'),
    path('patient/<slug>/delete-patient', views.delete_patient, name='delete_patient'),
    path('patient/<slug>/delete-images', views.delete_images, name='delete_images'),
    path('patient/<slug>/surgery/<id>/approve', views.approve_surgery, name='approve_surgery'),
    path('patient/<slug>/surgery/<id>/deny', views.deny_surgery, name='deny_surgery'),
    path('patient/<slug>/add-surgery', views.add_surgery, name='add_surgery'),
    path('patient/<slug>/surgery/<id>', views.surgery_page, name='surgery_page'),
    path('patient/<slug>/surgery/<id>/delete-surgery', views.delete_surgery, name='delete_surgery'),
    path('patient/<slug>/surgery/<id>/delete-surgery-images', views.delete_surgery_images,
         name='delete_surgery_images'),
    path('filter/', views.filter_by_date, name='filter_by_date'),
    path('hui-report/', views.hui_report, name='hui_report'),
    path('patient/edit/<slug>', views.edit_patient, name='edit_patient'),
    re_path(r'^filter.csv', views.send_file, name='send_file'),
    path('calendar/<year>/<current_month>', views.calendar_events, name='calendar'),
    path('privacy-policy/', views.privacyPolicy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('admin/<model>/', views.admin_template, name='admin_template'),
    path('admin/<model>/edit/<id>/', views.admin_edit, name='admin_edit'),
    path('admin/<model>/delete/<id>/', views.admin_delete, name='admin_delete')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

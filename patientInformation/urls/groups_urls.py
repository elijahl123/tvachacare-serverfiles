from django.urls import path

from patientInformation import views

urlpatterns = [
    path('', views.groups, name='groups'),
    path('add/', views.add_group, name='add_group'),
    path('edit/<id>/', views.edit_group, name='edit_group'),
    path('delete/<id>/', views.delete_group, name='delete_group'),
    path('lock-unlock/<group_id>/', views.lock_unlock_group, name='lock_unlock_group'),
    path('view/<id>/', views.group_page, name='group_page'),
    path('view/<id>/add-surgeries/', views.group_add_surgeries, name='group_add_surgeries')
]
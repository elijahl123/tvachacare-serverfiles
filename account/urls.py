from django.urls import path

from account import views

urlpatterns = [
    path('', views.admin, name='admin-console'),
    path('<model>/', views.admin_template, name='admin_template'),
    path('<model>/edit/<id>/', views.admin_edit, name='admin_edit'),
    path('<model>/delete/<id>/', views.admin_delete, name='admin_delete'),
    path('<model>/view/<id>/', views.admin_view, name='admin_view'),
]

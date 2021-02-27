from django.urls import path

from account import views

urlpatterns = [
    path('', views.account, name='account'),
    path('change-password/', views.change_password, name='change_password')
]
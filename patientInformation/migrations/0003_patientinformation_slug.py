# Generated by Django 3.0.8 on 2020-08-06 04:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patientInformation', '0002_auto_20200805_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientinformation',
            name='slug',
            field=models.SlugField(blank=True, unique=True),
        ),
    ]
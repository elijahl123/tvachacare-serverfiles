# Generated by Django 3.0.8 on 2020-08-07 04:28

from django.db import migrations, models
import patientInformation.models


class Migration(migrations.Migration):

    dependencies = [
        ('patientInformation', '0006_auto_20200806_1906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='profile_picture_path',
            field=models.ImageField(blank=True, null=True, upload_to=patientInformation.models.upload_location),
        ),
    ]

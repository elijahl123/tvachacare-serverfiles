# Generated by Django 3.0.8 on 2020-08-06 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patientInformation', '0004_auto_20200806_0052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientinformation',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ]
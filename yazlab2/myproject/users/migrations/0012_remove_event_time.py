# Generated by Django 5.0.4 on 2024-11-27 13:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_event_end_time_event_start_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='time',
        ),
    ]

# Generated by Django 5.0.4 on 2024-11-10 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='verification_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
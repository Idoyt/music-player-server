# Generated by Django 5.0.4 on 2024-04-22 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='username',
            field=models.CharField(default='miku fans', max_length=150),
        ),
    ]
# Generated by Django 4.2.2 on 2024-11-28 10:47

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chats", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="chatmessage",
            name="user",
        ),
    ]

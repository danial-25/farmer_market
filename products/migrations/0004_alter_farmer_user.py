# Generated by Django 4.2.2 on 2024-11-19 08:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("products", "0003_farmer_user_alter_product_popularity"),
    ]

    operations = [
        migrations.AlterField(
            model_name="farmer",
            name="user",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="farmer_profile",
                to="users.customuser",
            ),
        ),
    ]

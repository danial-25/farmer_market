# Generated by Django 4.2.2 on 2024-11-30 17:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0012_remove_order_total_price_remove_orderitem_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryOption",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "option_type",
                    models.CharField(
                        choices=[
                            ("HOME_DELIVERY", "Home Delivery"),
                            ("PICKUP_POINT", "Pickup Point"),
                            ("THIRD_PARTY", "Third-Party Delivery"),
                        ],
                        max_length=50,
                    ),
                ),
                ("details", models.TextField(blank=True, null=True)),
                (
                    "farmer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delivery_options",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_option",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="users.deliveryoption",
            ),
        ),
    ]
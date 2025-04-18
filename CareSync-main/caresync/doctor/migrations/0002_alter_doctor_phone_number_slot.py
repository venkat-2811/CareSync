# Generated by Django 5.0.6 on 2025-03-21 16:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("doctor", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="doctor",
            name="phone_number",
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.CreateModel(
            name="Slot",
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
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("available", "Available"),
                            ("booked", "Booked"),
                            ("closed", "Closed"),
                        ],
                        default="available",
                        max_length=10,
                    ),
                ),
                (
                    "doctor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

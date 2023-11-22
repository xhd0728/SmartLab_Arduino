# Generated by Django 4.2.3 on 2023-10-10 21:18

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="datalog",
            name="create_time",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="记录时间"
            ),
        ),
    ]
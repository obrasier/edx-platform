# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0006_auto_20160929_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classset',
            name='class_name',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='classset',
            name='short_name',
            field=models.CharField(max_length=32, null=True),
        ),
    ]

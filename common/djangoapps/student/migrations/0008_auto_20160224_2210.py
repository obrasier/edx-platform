# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_auto_20160214_2333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classset',
            name='class_name',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='classset',
            name='short_name',
            field=models.CharField(max_length=12, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='postcode',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='school',
            name='state',
            field=models.CharField(max_length=10),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0005_auto_20160602_0129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='acara_id',
            field=models.IntegerField(unique=True, null=True),
        ),
    ]

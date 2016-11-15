# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_auto_20161114_1343'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitionsubmission',
            name='viewed',
            field=models.BooleanField(default=False),
        ),
    ]

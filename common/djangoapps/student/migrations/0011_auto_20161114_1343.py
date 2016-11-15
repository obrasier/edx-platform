# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0010_auto_20161114_1331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competitionsubmission',
            name='judging_comments',
            field=models.CharField(db_index=True, max_length=700, blank=True),
        ),
    ]

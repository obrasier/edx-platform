# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_competitionsubmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitionsubmission',
            name='judging_comments',
            field=models.CharField(db_index=True, max_length=767, blank=True),
        ),
        migrations.AddField(
            model_name='competitionsubmission',
            name='short_listed',
            field=models.BooleanField(default=False),
        ),
    ]

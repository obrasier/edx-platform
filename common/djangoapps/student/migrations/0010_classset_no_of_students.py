# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20160225_0842'),
    ]

    operations = [
        migrations.AddField(
            model_name='classset',
            name='no_of_students',
            field=models.IntegerField(null=True),
        ),
    ]

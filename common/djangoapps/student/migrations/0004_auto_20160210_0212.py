# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_auto_20160201_0931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacherprofile',
            name='phone',
            field=models.CharField(max_length=25, null=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0002_auto_20160414_1559'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classset',
            name='subject',
        ),
        migrations.AddField(
            model_name='classset',
            name='subject',
            field=models.CharField(max_length=12, null=True),
        ),
    ]

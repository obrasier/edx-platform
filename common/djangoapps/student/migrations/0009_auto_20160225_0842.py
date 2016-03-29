# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_auto_20160224_2210'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classset',
            name='grade',
        ),
        migrations.AddField(
            model_name='classset',
            name='grade',
            field=models.CharField(max_length=12, null=True),
        ),
        migrations.AlterField(
            model_name='subject',
            name='description',
            field=models.CharField(max_length=30),
        ),
    ]

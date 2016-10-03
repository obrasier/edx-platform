# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_auto_20161003_1119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classset',
            name='grade',
            field=models.CharField(max_length=32, null=True),
        ),
    ]

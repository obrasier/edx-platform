# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0005_auto_20160226_0124'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolregion',
            name='region_type',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='schoolregion',
            name='region_id',
            field=models.IntegerField(),
        ),
    ]

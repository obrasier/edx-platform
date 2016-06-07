# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_auto_20160512_0233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentprofile',
            name='classSet',
            field=models.ManyToManyField(to='student.ClassSet'),
        ),
    ]

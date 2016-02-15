# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0005_auto_20160213_2055'),
    ]

    operations = [
        migrations.AddField(
            model_name='classset',
            name='encrypted_pk',
            field=models.CharField(default='', unique=True, max_length=9, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='classset',
            name='class_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='classset',
            name='grade',
            field=models.ManyToManyField(to='student.SchoolGrade', blank=True),
        ),
        migrations.AlterField(
            model_name='classset',
            name='subject',
            field=models.ManyToManyField(to='student.Subject', blank=True),
        ),
    ]

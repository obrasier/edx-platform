# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_auto_20160225_2314'),
    ]

    operations = [
        migrations.RenameField(
            model_name='schoolprofile',
            old_name='female_enrolments',
            new_name='female_enrollments',
        ),
        migrations.RenameField(
            model_name='schoolprofile',
            old_name='icsea_value',
            new_name='icsea',
        ),
        migrations.RenameField(
            model_name='schoolprofile',
            old_name='ind_enrolments_pct',
            new_name='ind_enrollments_pct',
        ),
        migrations.RenameField(
            model_name='schoolprofile',
            old_name='male_enrolments',
            new_name='male_enrollments',
        ),
        migrations.RenameField(
            model_name='schoolprofile',
            old_name='total_enrolments',
            new_name='total_enrollments',
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='smcl_id',
            field=models.IntegerField(default=0, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='schoolprofile',
            name='area',
            field=models.ForeignKey(to='student.RegionOne', null=True),
        ),
    ]

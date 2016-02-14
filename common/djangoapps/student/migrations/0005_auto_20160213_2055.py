# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_auto_20160210_0212'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentprofile',
            name='year_of_birth',
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 2, 13, 20, 54, 43, 359390), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='school_grade',
            field=models.CharField(blank=True, max_length=2, choices=[(b'K', b'K'), (b'1', b'Year 1'), (b'2', b'Year 2'), (b'3', b'Year 3'), (b'4', b'Year 4'), (b'5', b'Year 5'), (b'6', b'Year 6'), (b'7', b'Year 7'), (b'8', b'Year 8'), (b'9', b'Year 9'), (b'10', b'Year 10'), (b'11', b'Year 11'), (b'12', b'Year 12'), (b'T', b'Tertiary')]),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 2, 13, 20, 55, 2, 271218), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='teacherprofile',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 2, 13, 20, 55, 9, 895776), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='teacherprofile',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 2, 13, 20, 55, 18, 914481), auto_now=True),
            preserve_default=False,
        ),
    ]

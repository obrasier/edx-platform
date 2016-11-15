# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import jsonfield.fields
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_auto_20161003_1126'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompetitionSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(db_index=True, version=1, editable=False, blank=True)),
                ('attempt_number', models.PositiveIntegerField()),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, db_index=True)),
                ('media_release', jsonfield.fields.JSONField(db_column=b'raw_answer', blank=True)),
                ('src_code_entry', jsonfield.fields.JSONField(db_column=b'src_code', blank=True)),
                ('video_entry', jsonfield.fields.JSONField(db_column=b'video', blank=True)),
                ('contact_name', models.CharField(max_length=255, db_index=True)),
                ('contact_ph', models.CharField(max_length=255, db_index=True)),
                ('contact_email', models.CharField(max_length=255, db_index=True)),
                ('device_name', models.CharField(max_length=255, db_index=True)),
                ('device_description', models.TextField(max_length=700)),
                ('acknowledge_toc', models.BooleanField(default=False)),
                ('viewed', models.BooleanField(default=False)),
                ('short_listed', models.BooleanField(default=False)),
                ('judging_comments', models.TextField(max_length=700, blank=True)),
                ('class_set', models.ForeignKey(to='student.ClassSet')),
                ('school', models.ForeignKey(to='student.School')),
            ],
            options={
                'ordering': ['-submitted_at', '-id'],
            },
        ),
    ]

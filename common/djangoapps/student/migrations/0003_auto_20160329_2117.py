# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0002_auto_20151208_1034'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('class_code', models.CharField(unique=True, max_length=9, db_index=True)),
                ('short_name', models.CharField(max_length=12, null=True)),
                ('class_name', models.CharField(max_length=50, null=True)),
                ('course_id', xmodule_django.models.CourseKeyField(db_index=True, max_length=255, blank=True)),
                ('grade', models.CharField(max_length=12, null=True)),
                ('assessment', models.BooleanField(default=False)),
                ('no_of_students', models.IntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ClassTime',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_from', models.TimeField()),
                ('time_to', models.TimeField()),
                ('day', models.CharField(max_length=3, choices=[(b'MON', b'Monday'), (b'TUE', b'Tuesday'), (b'WED', b'Wednesday'), (b'THU', b'Thursday'), (b'FRI', b'Friday')])),
                ('timezone', models.CharField(max_length=4, choices=[(b'AEST', b'Australian Eastern Standard Time'), (b'AEDT', b'Australian Eastern Daylight Time'), (b'ACST', b'Australian Central Standard Time'), (b'ACDT', b'Australian Central Daylight Time'), (b'AWST', b'Australian Western Standard Time')])),
                ('comments', models.CharField(max_length=100, null=True, blank=True)),
                ('classSet', models.ForeignKey(to='student.ClassSet')),
            ],
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acara_id', models.IntegerField(unique=True)),
                ('school_name', models.CharField(max_length=100)),
                ('street_address', models.CharField(max_length=100)),
                ('suburb', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=10)),
                ('postcode', models.CharField(max_length=10)),
                ('school_sector', models.CharField(max_length=1, choices=[(b'G', b'Government'), (b'C', b'Catholic'), (b'I', b'Independent')])),
                ('school_type', models.CharField(max_length=1, choices=[(b'P', b'Primary'), (b'S', b'Secondary'), (b'C', b'Combined'), (b'O', b'Special')])),
            ],
        ),
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('school_grade', models.CharField(blank=True, max_length=2, choices=[(b'K', b'K'), (b'1', b'Year 1'), (b'2', b'Year 2'), (b'3', b'Year 3'), (b'4', b'Year 4'), (b'5', b'Year 5'), (b'6', b'Year 6'), (b'7', b'Year 7'), (b'8', b'Year 8'), (b'9', b'Year 9'), (b'10', b'Year 10'), (b'11', b'Year 11'), (b'12', b'Year 12'), (b'T', b'Tertiary')])),
                ('indigenous', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('classSet', models.ManyToManyField(to='student.ClassSet')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=30)),
                ('default_list', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TeacherProfile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('phone', models.CharField(max_length=25, null=True)),
                ('hear_about_us', models.CharField(blank=True, max_length=2, null=True, choices=[(b'MM', b'Participated in MadMaker 2015'), (b'FR', b'Friend'), (b'FA', b'Family Member'), (b'CO', b'Colleague'), (b'SY', b'Sydney Uni Marketing & Comms'), (b'SM', b'Social Media'), (b'SE', b'Search Engine'), (b'CE', b'Conference or Event'), (b'O', b'Other')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school', models.ForeignKey(to='student.School', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='classset',
            name='created_by',
            field=models.ForeignKey(related_name='classes_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='classset',
            name='school',
            field=models.ForeignKey(to='student.School'),
        ),
        migrations.AddField(
            model_name='classset',
            name='subject',
            field=models.ManyToManyField(to='student.Subject', blank=True),
        ),
        migrations.AddField(
            model_name='classset',
            name='teacher',
            field=models.ForeignKey(related_name='classes_taught', to=settings.AUTH_USER_MODEL),
        ),
    ]

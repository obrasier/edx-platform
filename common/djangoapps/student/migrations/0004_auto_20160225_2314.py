# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_auto_20160225_0034'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year_of_data', models.IntegerField()),
                ('location', models.CharField(max_length=1, choices=[(b'M', b'Metropolitan'), (b'P', b'Provincial'), (b'R', b'Remote'), (b'V', b'Very Remote')])),
                ('icsea_value', models.IntegerField(null=True)),
                ('teaching_staff', models.IntegerField(null=True)),
                ('total_enrolments', models.IntegerField(default=0)),
                ('female_enrolments', models.IntegerField(default=0)),
                ('male_enrolments', models.IntegerField(default=0)),
                ('ind_enrolments_pct', models.IntegerField(default=0)),
                ('lang_other_than_eng', models.IntegerField(default=0)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
                ('school', models.ForeignKey(to='student.School')),
            ],
        ),
        migrations.CreateModel(
            name='SchoolRegion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('region_id', models.IntegerField(unique=True)),
                ('region_name', models.CharField(max_length=125)),
            ],
        ),
        migrations.CreateModel(
            name='RegionOne',
            fields=[
                ('schoolregion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='student.SchoolRegion')),
            ],
            bases=('student.schoolregion',),
        ),
        migrations.CreateModel(
            name='RegionThree',
            fields=[
                ('schoolregion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='student.SchoolRegion')),
            ],
            bases=('student.schoolregion',),
        ),
        migrations.CreateModel(
            name='RegionTwo',
            fields=[
                ('schoolregion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='student.SchoolRegion')),
                ('region_three', models.ForeignKey(to='student.RegionThree')),
            ],
            bases=('student.schoolregion',),
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='area',
            field=models.ForeignKey(to='student.RegionOne'),
        ),
        migrations.AddField(
            model_name='regionone',
            name='region_two',
            field=models.ForeignKey(to='student.RegionTwo'),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0006_auto_20160214_2312'),
    ]

    operations = [
        migrations.RenameField(
            model_name='classset',
            old_name='encrypted_pk',
            new_name='class_code',
        ),
    ]

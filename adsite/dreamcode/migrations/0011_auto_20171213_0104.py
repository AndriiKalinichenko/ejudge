# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-13 01:04
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('dreamcode', '0010_auto_20171212_2148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest',
            name='end',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 13, 1, 4, 36, 623816, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='contest',
            name='start',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 13, 1, 4, 36, 623769, tzinfo=utc)),
        ),
    ]
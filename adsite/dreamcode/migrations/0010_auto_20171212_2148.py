# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-12 21:48
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('dreamcode', '0009_auto_20171212_2104'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='result',
            field=models.CharField(choices=[('NT', 'Not Tested'), ('CE', 'Compile Error'), ('PD', 'Pending'), ('TS', 'Tested'), ('OK', 'Accepted'), ('FA', 'Failed')], default='NT', max_length=2),
        ),
        migrations.AlterField(
            model_name='contest',
            name='end',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 12, 21, 48, 7, 997830, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='contest',
            name='start',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 12, 21, 48, 7, 997786, tzinfo=utc)),
        ),
    ]
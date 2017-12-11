# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-11 19:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import ejudge.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug_name', models.SlugField(unique=True)),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('contestants', models.ManyToManyField(null=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug_name', models.SlugField(unique=True)),
                ('statement', models.TextField(default='')),
                ('max_score', models.IntegerField(default=500)),
                ('contest', models.ForeignKey(default=ejudge.models.get_or_create_default_contest, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ejudge.Contest')),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('NT', 'Not Tested'), ('CE', 'Compile Error'), ('PD', 'Pending'), ('TS', 'Tested')], default='NT', max_length=2)),
                ('score_percent', models.IntegerField(default=-1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('is_public', models.BooleanField(default=False)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ejudge.Problem')),
            ],
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input', models.FileField(upload_to=ejudge.models.test_case_input_path)),
                ('output', models.FileField(upload_to=ejudge.models.test_case_output_path)),
                ('cpu_time_limit', models.IntegerField(default=2000)),
                ('wall_clock_time_limit', models.IntegerField(default=6000)),
                ('memory_limit', models.IntegerField(default=8388608)),
                ('is_public', models.BooleanField(default=False)),
                ('hint', models.TextField(blank=True, default='')),
                ('type', models.CharField(choices=[('IO', 'Input - Output'), ('MD', 'Mandatory - Denied')], default='IO', max_length=2)),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ejudge.Problem')),
            ],
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(default='', max_length=255)),
                ('status', models.CharField(choices=[('PD', 'Pending'), ('OK', 'Okay'), ('RF', 'Restricted Function'), ('ML', 'Memory Limit Exceed'), ('OL', 'Output Limit Exceed'), ('TL', 'Time Limit Exceed'), ('RT', 'Run Time Error (SIGSEGV, SIGFPE, ...)'), ('AT', 'Abnormal Termination'), ('IE', 'Internal Error (of sandbox executor)'), ('BP', 'Bad Policy'), ('R0', 'Reserved result type 0'), ('R1', 'Reserved result type 1'), ('R2', 'Reserved result type 2'), ('R3', 'Reserved result type 3'), ('R4', 'Reserved result type 4'), ('R5', 'Reserved result type 5'), ('EX', 'Exception')], default='PD', max_length=2)),
                ('memory', models.IntegerField(default=0)),
                ('cpu_time', models.IntegerField(default=0)),
                ('result', models.CharField(choices=[('PD', 'Pending'), ('OK', 'Accepted'), ('PE', 'Presentation error'), ('FA', 'Failed')], default='PD', max_length=2)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results', to='ejudge.Submission')),
                ('test_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results', to='ejudge.TestCase')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='testresult',
            unique_together=set([('submission', 'test_case')]),
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set([('author', 'problem')]),
        ),
    ]
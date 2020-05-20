# Generated by Django 2.2.7 on 2019-11-25 11:45

from django.db import migrations
import vino.sharekernel.models


class Migration(migrations.Migration):

    dependencies = [
        ('sharekernel', '0002_auto_20191125_1243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='viabilityproblem',
            name='constraints',
            field=vino.sharekernel.models.InequationsField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='viabilityproblem',
            name='controls',
            field=vino.sharekernel.models.InequationsField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='viabilityproblem',
            name='domain',
            field=vino.sharekernel.models.InequationsField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='viabilityproblem',
            name='dynamics',
            field=vino.sharekernel.models.EquationsField(blank=True, max_length=200),
        ),
    ]

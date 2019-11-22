# Generated by Django 2.2.7 on 2019-11-25 11:43

from django.db import migrations
import vino.sharekernel.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sharekernel', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='viabilityproblem',
            name='constraints',
            field=vino.sharekernel.fields.StatementsField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='viabilityproblem',
            name='controls',
            field=vino.sharekernel.fields.StatementsField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='viabilityproblem',
            name='domain',
            field=vino.sharekernel.fields.StatementsField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='viabilityproblem',
            name='dynamics',
            field=vino.sharekernel.fields.StatementsField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='viabilityproblem',
            name='target',
            field=vino.sharekernel.fields.StatementsField(blank=True, max_length=200),
        ),
    ]

# Generated by Django 5.0.6 on 2024-05-31 03:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0003_remove_user_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=1, unique=True, verbose_name='分类代码')),
                ('name', models.CharField(max_length=255, verbose_name='分类名称')),
            ],
            options={
                'verbose_name': '书籍分类',
                'verbose_name_plural': '书籍分类',
                'db_table': 'categories',
                'managed': True,
            },
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(fields=('code',), name='unique_code'),
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.CheckConstraint(check=models.Q(('code__regex', '^[A-Z]$')), name='valid_code'),
        ),
        migrations.AddField(
            model_name='book',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='library.category', verbose_name='分类'),
        ),
    ]
# Generated by Django 2.2 on 2019-06-17 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0009_auto_20190611_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(default='', max_length=50, verbose_name='Содержимое')),
                ('viewed', models.BooleanField(default=False, verbose_name='Просмотрено')),
                ('name', models.CharField(default='', max_length=20, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
            },
        ),
        migrations.AddField(
            model_name='advuser',
            name='notifications',
            field=models.ManyToManyField(blank=True, related_name='notifications', to='articles.Notification', verbose_name='Уведомления'),
        ),
    ]
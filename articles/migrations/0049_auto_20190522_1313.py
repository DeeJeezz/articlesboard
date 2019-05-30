# Generated by Django 2.2 on 2019-05-22 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0048_auto_20190522_1311'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='image_url',
            field=models.URLField(blank=True, help_text='Изображение на плитке на главной странице.', null=True, verbose_name='Ссылка на изображение'),
        ),
    ]
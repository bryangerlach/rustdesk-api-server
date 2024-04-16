# Generated by Django 5.0.3 on 2024-04-09 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_filelog_filesize'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filelog',
            name='sent_from',
        ),
        migrations.RemoveField(
            model_name='filelog',
            name='sent_to',
        ),
        migrations.RemoveField(
            model_name='filelog',
            name='sent_to_ip',
        ),
        migrations.AddField(
            model_name='filelog',
            name='direction',
            field=models.IntegerField(default=0, verbose_name='Direction'),
        ),
        migrations.AddField(
            model_name='filelog',
            name='remote_id',
            field=models.CharField(default='0', max_length=20, verbose_name='Remote ID'),
        ),
        migrations.AddField(
            model_name='filelog',
            name='user_id',
            field=models.CharField(default='0', max_length=20, verbose_name='User ID'),
        ),
        migrations.AddField(
            model_name='filelog',
            name='user_ip',
            field=models.CharField(default='0', max_length=20, verbose_name='User IP'),
        ),
    ]
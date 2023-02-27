import os

from datetime import timedelta
from celery import Celery
from celery.schedules import crontab

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = settings.TIME_ZONE
app.autodiscover_tasks()

app.conf.beat_schedule = {
    #'comment_pages_asc': {
    #    'task': 'applications.core.tasks.comment_public_pages_asc',
    #    'schedule': crontab(minute=0, hour='9,11,17,19,21,23'),
    #},
    #'comment_pages_desc': {
    #    'task': 'applications.core.tasks.comment_public_pages_desc',
    #    'schedule': crontab(minute=0, hour='10,12,18,20,22,0'),
    #},
    'collect_insta_posts': {
        'task': 'applications.core.tasks.collect_new_instagram_posts',
        'schedule': crontab(minute=30, hour=0), # everyday at 00:30
    }
}

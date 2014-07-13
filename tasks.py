from celery import Celery
import os

celery = Celery(__name__,
                backend='amqp',
                broker=os.environ['CLOUDAMQP_URL'])

@celery.task
def send_email(frm, to, subject, content):
    raise "Hey"

web:    gunicorn app:app --log-file=-
worker: celery worker -A tasks.celery --loglevel=info

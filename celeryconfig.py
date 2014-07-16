import os

BROKER_URL = os.environ['CLOUDAMQP_URL']
BROKER_POOL_LIMIT = 3
CELERY_RESULT_BACKEND = os.environ['REDISCLOUD_URL']
CELERY_REDIS_MAX_CONNECTIONS = 10
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_EVENT_SERIALIZER = 'json'

# deliberately low settings because free addons are free for a reason
CELERY_TASK_RESULT_EXPIRES = 60
CELERY_MAX_CACHED_RESULTS = 10


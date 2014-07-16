import celery as C
import email_clients as clients

celery = C.Celery(__name__, config_source='celeryconfig')


@celery.task(bind=True)
def queue_email(self, from_email, to_email, subject, content):
    errors = []
    for client in clients.get_clients():
        try:
            client.send_email(from_email, to_email, subject, content)
        except clients.EmailClientException as e:
            errors.append(e)
        else:
            # TODO: Update record to indicate result of operation
            return client.__class__.__name__

    raise self.retry(exc=Exception(*errors))

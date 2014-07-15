import celery as C
import email_clients as clients
import os

celery = C.Celery(__name__,
                  backend='amqp',
                  broker=os.environ['CLOUDAMQP_URL'])


@celery.task(bind=True)
def queue_email(self, from_email, to_email, subject, content):
    errors = []
    for client in clients.get_clients():
        try:
            resp = client.send_email(from_email, to_email, subject, content)
        except clients.EmailClientException as e:
            errors.append(e.args)
        else:
            if resp.ok:
                # TODO: Update record to indicate result of operation
                return client.__class__.__name__, resp
            else:
                errors.append(resp)

    raise self.retry(exc=Exception(*errors))

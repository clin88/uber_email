uber_email
==========

Uber code challenge—email project for the back-end track.

Features a simple, RESTful, API for sending email. uber-email
is backed by the Mailgun and Mandrill services, which it rotates
between when sending emails.

# Author

Chen Lin

[My linkedin](https://www.linkedin.com/in/clin88)

There's a bunch of interesting things on my github, but the highlights are
probably:

  * [HaskTorrent](https://github.com/clin88/HaskTorrent) - A concurrent bittorrent client in Haskell using Software
        Transactional Memory.
  * [MathBit](https://github.com/clin88/MathBit) - A lightweight computer algebra
        system that does algebraic operations on expressions while yielding
        the steps it takes.

I haven't had a chance to improve the READMEs for either project, but
I'm happy to answer questions about them.

# Deployment

1.) Install Python dependencies using

`pip install -r requirements.txt`

2.) Update your environment with the following envvars:

```quote
DEBUG_MODE=<Flask Debug Mode. 1 for on (not recommended in production), 0 for off>
CLOUDAMQP_URL=<AMQP service url. Recommend RabbitMQ.>

MANDRILL_API_URL=https://mandrillapp.com/api/1.0
MANDRILL_API_KEY=<Mandrill API Key>

MAILGUN_API_URL=https://api.mailgun.net/v2
MAILGUN_API_KEY=<Mailgun Private API Key>
MAILGUN_DOMAIN=<Mailgun Sending Domain>
```

Note that you'll need to create accounts with Mandrill and Mailgun.

3.) A `Procfile` is included that details commands for launching application
processes. You can also use `foreman` to make this easier.

`foreman run web` starts the web server.
`foreman run worker` starts the celery worker.

This is also very easy to deploy on heroku.

# Use

You can use the included frontend at `/` or call the API directly.

Currently, the only endpoint is `/emails`, which accepts POST requests
with the following data:

  * `from_email`: email to send from
  * `to_email`: email to send to
  * `subject`: subject line
  * `content`: plain-text content

In python, you could write:

```python
import requests

data = { ... }

resp = requests.post('http://chenlin.io/emails', data)
assert resp.status_code == 200
```

Note that the response does not indicate if the email was successfully sent-
it only indicates if the email task was queued successfully. This allows
long running tasks to run asynchronously with processing of HTTP requests.

# Architecture and Design

## Processes

There are two processes in uber-email: `web` and `worker`.

  * `web` receives HTTP requests and queues up request events in
    a queue service (in this case, we use RabbitMQ).

  * `worker` takes celery tasks off RabbitMQ and executes them.

This architecture has several advantages:

  1.) Greater separation of concerns: Much easier to reason about
   `web` and `worker` since they do very different things.

  2.) More flexible scalability: If the workload at either end becomes
   too great, simply spin up more `web` or `worker` instances to alleviate
   the load.

  3.) Better reliability: If one worker fails or deadlocks, other workers
   can accomplish the same tasks.

One downside is that it's harder for users to discover the status of their
email-since emailing happens asynchronously with the processing of HTTP
requests, a successful HTTP response only indicates that the email task
was queued successfully.

One workaround could be to offer an optional timeout: we can have each
gunicorn worker wait up to x ms to see if a worker responds with a result.

## Clients

All email clients inherit from the abstract base class `BaseClient`,
allowing for a common interface to all email clients. To add or remove
clients, subclass BaseClient, implement `ping` and `send_email`, and
register the client in `email_clients._clients`.

## Dependencies

Uber-email uses `celery` and `flask`.

  * `flask` makes it easy to process HTTP requests, and is a much more
    lightweight framework than `django`, making it more suitable for this
    project.

  * `celery` is a distributed task system that handles queuing, scheduling,
    and execution of tasks. While complex, celery also provides some very
    useful features for free, like retry scheduling and serializing tasks.
    This allows developers to focus on business logic and not message passing.

# TODO: Add authentication
# TODO: Support sending to multiple recipients
# TODO: Support names
# TODO: Add logging

import flask
import os
import tasks
import re
import celery

app = flask.Flask(__name__)
app.debug = int(os.environ['DEBUG_MODE'])

@app.route('/', methods=['GET'])
def home():
    return flask.render_template('index.html')

@app.route('/emails', methods=['POST'])
def post_email():
    """Queues a new email, but does not necessarily send the email. Clients
    must register a webhook (not implemented) or poll the resource to discover
    the status of the email.

    Returns 201 with a 'Location' header pointing to the resource if successful.
    """
    request_schema = {
        'from_email': basestring,
        'to_email': basestring,
        'subject': basestring,
        'content': basestring
    }
    data = flask.request.values
    if not validate_schema(request_schema, data):
        return 'Wrong parameters.' + str(data.to_dict()), 400

    if not validate_email(data['from_email']):
        return 'Invalid from_email.', 400

    if not validate_email(data['to_email']):
        return 'Invalid to_email.', 400

    result = tasks.queue_email.delay(**data.to_dict())
    try:
        client = result.get(timeout=1)
    except celery.exceptions.TimeoutError:
        return 'Email successfully queued.', 200
    else:
        return 'Email successfully sent with {}.'.format(client)

    # note: other errors implicitly handled by flask. Use @errorhandler decorator to
    # customize response.


@app.route('/emails/<id>', methods=['GET'])
def get_email(id):
    return "Polling email status not implemented.", 501

def validate_schema(schema, data):
    """Simple framework for validating data against a schema.

    Schemas are simply dictionaries with expected types in place of
    values. All keys in schema are required, and all values of required
    keys must be an instance of the required type. Note that instances
    of subclasses of the required type are valid.
    """
    if len(data) != len(schema):
        return False

    for key, typ in schema.iteritems():
        if key not in data:
            return False

        if not isinstance(data[key], typ):
            return False

    return True

def validate_email(email):
    """Questionable if this is necessary, since this is handled better
    by our email client services. However, API users probably expect
    an error when invalid email addresses are entered.
    """
    if re.search(r'^[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]+$', email):
        return True
    return False

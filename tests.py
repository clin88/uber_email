import flask
import json
import mock
import email_clients as clients
import tasks
import celery
from app import app, post_email, validate_schema
from mock import patch, Mock, call, MagicMock

# def test_email_post():
#     data = {
#         'from': 'abc@def.edu',
#         'to': 'def@ghi.com',
#         'subject': 'hey',
#         'content': 'yo'
#     }
#     with app.test_request_context('/emails', data=json.dumps(data)):
#         post_email()

def test_validate_schema():
    data = {
        'int': 1,
        'float': 2.,
        'str': 'hey'
    }
    schema = {
        'int': int,
        'float': float,
        'str': str
    }
    assert validate_schema(schema, data) == True

# Test tasks.

def setup():
    # This ensures that celery tasks are run locally and synchronously
    # for unit testing.
    tasks.celery.conf.CELERY_ALWAYS_EAGER = True

@patch('tasks.QueueEmail.on_success')
@patch('tasks.queue_email.retry')
@patch('tasks.clients.get_clients')
def test_queue_email(client_list, retry, success_hook):
    mock_clients = [Mock(), Mock()]
    client_list.return_value = mock_clients
    tasks.queue_email.delay('a', 'b', 'c', 'd').get()

    assert mock_clients[0].send_email.call_count == 1
    #assert success_hook.call_count == 1
    assert not mock_clients[1].called
    assert not retry.called

@patch('tasks.queue_email.retry')
@patch('tasks.clients.get_clients')
def test_queue_email_failure(client_list, retry):
    mock_clients = [Mock(), Mock()]
    client_list.return_value = mock_clients
    mock_clients[0].send_email.return_value = Mock(ok=False)
    mock_clients[1].send_email.side_effect = clients.EmailClientException
    retry.side_effect = celery.exceptions.Retry

    result = tasks.queue_email.delay('a', 'b', 'c', 'd')
    result.get()

    assert mock_clients[0].send_email.called
    assert mock_clients[1].send_email.called
    assert retry.called

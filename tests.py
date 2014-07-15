import flask
import json
import mock
import email_clients as clients
import tasks
import celery
import unittest
from app import app, validate_schema
from mock import patch, Mock, call, MagicMock

################
# Test API.
################

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch('tasks.queue_email.delay')
    def test_email_post(self, task):
        data = {
           'from_email': 'abc@def.edu',
           'to_email': 'def@ghi.com',
           'subject': 'hey',
           'content': 'yo'
        }
        resp = self.app.post('/emails',
                             data=json.dumps(data),
                             base_url='http://test')
        assert resp.status_code == 201
        assert resp.headers['Location'] == 'http://test/NOTIMP'
        assert task.call_count == 1

    @patch('tasks.queue_email.delay')
    def test_email_post_fail(self, task):
        data = { 'abc': 'def' }
        resp = self.app.post('/emails', data=json.dumps(data))
        assert resp.status_code == 400

        resp = self.app.post('/emails', data='NOTJSON')
        assert resp.status_code == 400

        assert not task.called

    def test_validate_schema(self):
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

################
# Test tasks.
################

class TaskTests(unittest.TestCase):
    def setUp(self):
        # This ensures that celery tasks are run locally and synchronously
        # for unit testing.
        tasks.celery.conf.CELERY_ALWAYS_EAGER = True

    def tearDown(self):
        tasks.celery.conf.CELERY_ALWAYS_EAGER = False

    @patch('tasks.QueueEmail.on_success')
    @patch('tasks.queue_email.retry')
    @patch('tasks.clients.get_clients')
    def test_queue_email(self, client_list, retry, success_hook):
        mock_clients = [Mock(), Mock()]
        client_list.return_value = mock_clients
        tasks.queue_email.delay('a', 'b', 'c', 'd').get()

        assert mock_clients[0].send_email.call_count == 1
        #assert success_hook.call_count == 1
        assert not mock_clients[1].called
        assert not retry.called

    @patch('tasks.queue_email.retry')
    @patch('tasks.clients.get_clients')
    def test_queue_email_failure(self, client_list, retry):
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
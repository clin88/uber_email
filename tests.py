import json
import email_clients as clients
import tasks
import celery
import unittest
import requests
import nose
from app import app, validate_schema, validate_email
from mock import patch, Mock, call, MagicMock

################
# Test API
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
                             data=data,
                             base_url='http://test')
        assert resp.status_code == 201
        assert resp.headers['Location'] == 'http://test/NOTIMP'
        assert task.call_count == 1

    @patch('tasks.queue_email.delay')
    def test_email_post_fail(self, task):
        data = { 'abc': 'def' }
        resp = self.app.post('/emails', data=json.dumps(data))
        assert resp.status_code == 400

        resp = self.app.post('/emails', data='INVALID')
        assert resp.status_code == 400

        assert not task.called

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

def test_validate_email():
    assert validate_email('abc_@test.edu')
    assert validate_email('def_+annotation@yo.basdif')
    assert validate_email('hey@test.com')
    assert not validate_email('abcdef')
    assert not validate_email('abc@test.')
    assert not validate_email('@test.com')
    assert not validate_email('abc@test')

################################
# Test email clients
################################

class ClientTests(unittest.TestCase):
    def test_get_clients(self):
        "Ensures get_clients switches up the order."
        first = clients.get_clients()[:]
        for _ in range(10):
            if clients.get_clients() != first:
                assert True
                return

        assert False

    @patch('email_clients.requests.post')
    def test_mandrill(self, post):
        post.return_value.ok = True
        c = clients.Mandrill()
        resp = c.send_email('from', 'to', 'subj', 'content')

        assert post.call_count == 1
        assert resp is True

    @patch('email_clients.requests.post')
    def test_mandrill_fail(self, post):
        c = clients.Mandrill()
        post.side_effect = requests.RequestException
        nose.tools.assert_raises(clients.RequestError,
                                 c.send_email,
                                 'from', 'to', 'subj', 'content')

        post.side_effect = None
        post.return_value.ok = False
        nose.tools.assert_raises(clients.EmailClientException,
                                 c.send_email,
                                 'from', 'to', 'subj', 'content')

    def test_mailgun(self):
        c = clients.Mailgun()
        c._sess = Mock()
        c._sess.post.return_value.ok = True
        resp = c.send_email('from', 'to', 'subj', 'content')

        assert c._sess.post.call_count == 1
        assert resp is True

    def test_mailgun_fail(self):
        c = clients.Mailgun()
        c._sess = Mock()

        c._sess.post.side_effect = requests.RequestException
        nose.tools.assert_raises(clients.RequestError,
                                 c.send_email,
                                 'from', 'to', 'subj', 'content')

        c._sess.post.side_effect = None
        c._sess.post.return_value.ok = False
        nose.tools.assert_raises(clients.EmailClientException,
                                 c.send_email,
                                 'from', 'to', 'subj', 'content')

################
# Test tasks
################

class TaskTests(unittest.TestCase):
    def setUp(self):
        # This ensures that celery tasks are run locally and synchronously
        # for unit testing.
        tasks.celery.conf.CELERY_ALWAYS_EAGER = True

    def tearDown(self):
        tasks.celery.conf.CELERY_ALWAYS_EAGER = False

    @patch('tasks.queue_email.retry')
    @patch('tasks.clients.get_clients')
    def test_queue_email(self, client_list, retry):
        mock_clients = [Mock(), Mock()]
        client_list.return_value = mock_clients
        mock_clients[0].send_email.return_value = True
        mock_clients[1].send_email.return_value = True
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
        mock_clients[0].send_email.return_value = False
        mock_clients[1].send_email.side_effect = clients.EmailClientException
        retry.side_effect = celery.exceptions.Retry

        result = tasks.queue_email.delay('a', 'b', 'c', 'd')
        result.get()

        assert mock_clients[0].send_email.called
        assert mock_clients[1].send_email.called
        assert retry.called


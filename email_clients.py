import requests
import abc
import os
import json
import random

class EmailClientException(Exception):
    pass

class RequestError(EmailClientException):
    pass

class Unauthorized(EmailClientException):
    pass

class BadRequest(EmailClientException):
    pass

class PaymentRequired(EmailClientException):
    pass

class RequestFailed(EmailClientException):
    pass

class UnknownHTTPError(EmailClientException):
    pass


class BaseClient(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def ping(self):
        """Pings or makes a HEAD call to the API to validate the url and
        API KEY. Used exclusively for testing."""
        pass

    @abc.abstractmethod
    def send_email(self, frm, to, subject, content):
        """Sends an email. In some cases for all clients, this may just
        queue the email on their side for later sending. If successful,
        returns True or None. If error, raises EmailClientException."""
        pass

    def _process_response(self, resp):
        """Responsible for interpreting response and propagating errors.
        Should raise EmailClientException in case of error."""
        pass

class Mailgun(BaseClient):
    url = os.environ['MAILGUN_API_URL']
    api_key = os.environ['MAILGUN_API_KEY']
    domain = os.environ['MAILGUN_DOMAIN']

    def __init__(self):
        self._sess = requests.Session()
        self._sess.auth = ('api', self.api_key)

    def ping(self):
        resp = self._sess.get(self.url + '/domains')
        return resp.ok

    def send_email(self, frm, to, subject, content):
        message = {
            'from': frm,
            'to': to,
            'subject': subject,
            'text': content
        }
        url = '{}/{}/messages'.format(self.url, self.domain)
        try:
            resp = self._sess.post(url, message)
        except requests.RequestException as e:
            raise RequestError(e.__class__.__name__, *e.args)

        return self._process_response(resp)

    def _process_response(self, resp):
        args = resp.status_code, resp.reason, resp.text
        if resp.ok:
            return True
        elif resp.status_code == 400:
            raise BadRequest(*args)
        elif resp.status_code == 401:
            raise Unauthorized(*args)
        elif resp.status_code == 402:
            # TODO: Find out how to differentiate 'insufficient quota'.
            raise RequestFailed(*args)
        else:
            raise UnknownHTTPError(*args)


class Mandrill(BaseClient):
    url = os.environ['MANDRILL_API_URL']
    api_key = os.environ['MANDRILL_API_KEY']

    def ping(self):
        resp = requests.post(self.url + 'users/ping')
        return resp.ok

    def send_email(self, frm, to, subject, content):
        recipient = { 'email': to }
        message = {
            'from_email': frm,
            'to': [recipient],
            'text': content,
        }
        data = {
            'key': self.api_key,
            'async': True,
            'message': message,
        }
        data = json.dumps(data)
        try:
            resp = requests.post(self.url + '/messages/send.json', data=data)
        except requests.RequestException as e:
            raise RequestError(*e.args)

        return self._process_response(resp)

    def _process_response(self, resp):
        if resp.ok:
            return True

        try:
            data = resp.json()
        except ValueError:
            UnknownHTTPError(resp.status_code, resp.reason, resp.text)

        args = resp.status_code, resp.reason, data

        try:
            error_name = data['name']
            status = data['status']
        except KeyError:
            raise UnknownHTTPError(*args)

        if status != 'error':
            raise UnknownHTTPError(*args)
        elif error_name == 'Invalid_Key':
            raise Unauthorized(*args)
        elif error_name == 'PaymentRequired':
            raise PaymentRequired(*args)
        elif error_name == 'ValidationError':
            raise BadRequest(*args)
        else:
            raise UnknownHTTPError(*args)

_clients = (Mandrill(), Mailgun())
def get_clients():
    """Returns a list of clients, randomly ordered to get even
    load distribution.
    """
    clients = list(_clients)
    random.shuffle(clients)
    return clients

import requests
import abc
import os
import json
import random

class EmailClientException(Exception):
    pass

class BaseClient(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def ping(self):
        """Pings or makes a HEAD call to the API to validate the url and
        API KEY. Used exclusively for testing."""
        pass

    @abc.abstractmethod
    def send_email(self, frm, to, content, subject):
        """Sends an email."""
        pass

class Mailgun(BaseClient):
    url = os.environ['MAILGUN_API_URL']
    api_key = os.environ['MAILGUN_API_KEY']
    domain = os.environ['MAILGUN_DOMAIN']

    def __init__(self):
        self._sess = requests.Session(auth=('api', self.api_key))

    def ping(self):
        resp = self._sess.get(self.url + '/domains')
        return resp.status_code == 200

    def send_email(self, frm, to, content, subject):
        message = json.dumps({
            'from': frm,
            'to': to,
            'subject': subject,
            'text': content
        })
        url = '{}/{}/messages'.format(self.url, self.domain)
        resp = self._sess.post(url, message)
        #resp.raise_for_status()
        return resp

class Mandrill(BaseClient):
    url = os.environ['MANDRILL_API_URL']
    api_key = os.environ['MANDRILL_API_KEY']

    def ping(self):
        resp = requests.post(self.url + 'users/ping')
        return resp.json()['PING'] == 'PONG!'

    def send_email(self, frm, to, content, subject):
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
        resp = requests.post(self.url + '/send.json', data=data)
        #resp.raise_for_status()
        return resp


_clients = (Mandrill(), Mailgun())
def get_clients():
    """Returns a list of clients, randomly ordered to get even
    load distribution.
    """
    clients = list(_clients)
    random.shuffle(clients)
    return clients

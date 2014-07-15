"""Dangerous, effectful tests not meant for automated testing.

Mainly useful to play around with during development or to verify
that the environment is set up correctly.

Avoid including test_ in method names to keep nose from automatically
running them.
"""
import email_clients as clients

def clients_ping():
    for client in clients.get_clients():
        assert client.ping()

def clients_email():
    # test successful queuing
    for client in clients.get_clients():
        resp = client.send_email('a@b.com', 'c@d.com', 'content', 'subject')
        #assert resp.status_code == 200
        print client.__class__.__name__, resp.status_code, resp.reason, resp.text

def clients_email_fail():
    # test invalid emails
    for client in clients.get_clients():
        resp = client.send_email('what', 'oh', 'content', 'subject')
        assert resp.status_code != 200
        print client.__class__.__name__, resp.status_code, resp.reason, resp.text

    # test invalid emails
    for client in clients.get_clients():
        resp = client.send_email('what', 'oh', 'content', 'subject')
        assert resp.status_code != 200
        print client.__class__.__name__, resp.status_code, resp.reason, resp.text


# validation error

import flask
import json
import os
from tasks import celery

app = flask.Flask(__name__)
app.debug = os.environ['DEBUG_MODE']

@app.route('/emails', methods=['POST'])
def post_email():
    id = 'abcdef'
    return 'test', 201, {'Location': '/{}'.format(id)}

@app.route('/emails/<id>', methods=['GET'])
def get_email(id):
    return "Polling email status not implemented.", 501

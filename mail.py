import requests
from tornado.template import Loader

import db
import config


def send(to, subject, body):
    url = 'https://api.mailgun.net/v2/%s/messages' % config.mail.url
    return requests.post(
        url,
        auth=('api', config.mail.key),
        data={'from': config.mail.from_address,
              'to': to,
              'subject': subject,
              'text': body})


def send_confirmation(user):
    loader = Loader('templates/mail')
    body = loader.load('confirm.txt').generate(user=user, config=config.web)
    
    if not user.unsubscribed:
        send(user.email, 'Confirmation instructions', body)

import requests
from tornado.template import Loader

import db
import config


def send(to, subject, text=None, html=None):
    url = 'https://api.mailgun.net/v2/%s/messages' % config.mail.url
    data = {'from': config.mail.from_address,
            'to': to,
            'subject': subject}
    if text:
        data['text'] = text
        
    if html:
        data['html'] = html    

    return requests.post(url, auth=('api', config.mail.key), data=data)


def send_confirmation(user):
    loader = Loader('templates/mail')
    text = loader.load('confirm.txt').generate(user=user, config=config.web)
    html = loader.load('confirm.html').generate(user=user, config=config.web)
    
    if not user.unsubscribed:
        send(user.email, 'Confirmation instructions', text=text, html=html)

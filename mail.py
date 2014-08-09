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
    if user.unsubscribed:
        return
    
    loader = Loader('templates/mail')
    text = loader.load('confirm.txt').generate(user=user, config=config.web)
    html = loader.load('confirm.html').generate(user=user, config=config.web)
    
    send(user.email, 'Confirmation instructions', text=text, html=html)


def send_alert(user_id, alert, alert_value):
    user = db.get_email_attributes(user_id)
    if user.unsubscribed:
        return
    
    alert.email_description = alert.email_description.replace('REPLACE_TRIGGER', str(alert.option_1_value))
    alert.email_description = alert.email_description.replace('REPLACE_ACTUAL', str(alert_value))
    
    if int(alert.interval) > 1440:
        alert.interval = "%d day(s)" % (int(alert.interval)/1440) # minutes to days
    else:
        alert.interval = "%d hour(s)" % (int(alert.interval)/60) # minutes to hours
    
    loader = Loader('templates/mail')
    text = loader.load('alert.txt').generate(user=user, alert=alert, config=config.web)
    html = loader.load('alert.html').generate(user=user, alert=alert, config=config.web)
    
    send(user.email, 'Character alert: ' + alert.name , text=text, html=html)

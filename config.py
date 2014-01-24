import yaml

class Config(object):
    def __init__(self, config):
        for k, v in config[self.key].items():
            del(self.attrs[k])
            setattr(self, k, v)

class WebConfig(Config):
    key = 'web'
    attrs = dict([
        ('port', 8888),
        ('host', 'localhost'),
        ('cookie_secret', 'super sekret'),
    ])

class DBConfig(Config):
    key = 'db'
    attrs = dict([
        ('host', 'localhost'),
        ('port', 5432),
        ('user', 'eveskill'),
        ('password', 'eveskill'),
        ('database', 'eveskill'),
    ])

try:
    conf = yaml.load(open('config.yaml', 'r'))
except FileNotFoundError:
    conf = dict()

web = WebConfig(conf)
db = DBConfig(conf)

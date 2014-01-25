import tornado.ioloop
import tornado.escape
import tornado.web
import os

import db
import config

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("skillbook_user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)


class MainHandler(BaseHandler):
    def get(self):
        try:
            error = self.get_argument("error")
        except:
            error = ""
        self.render('index.html', error=error)


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        user_id = db.check_login(username, password)
        if user_id is not None:
            json = tornado.escape.json_encode({'userid': user_id})
            self.set_secure_cookie('skillbook_user', str(user_id), expires_days=90)
            self.redirect('/home')
        else:
            error = u'?activity=login&error=' + tornado.escape.url_escape('Incorrect username or password')
            self.redirect('/' + error)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('skillbook_user')
        self.redirect('/')


class RegistrationHandler(BaseHandler):
    def get(self):
        self.redirect('/')
    def post(self):
        username = self.get_argument('username').lower()
        password = self.get_argument('password')
        password_again = self.get_argument('password_rep')
        if password != password_again:
            error = u'?activity=register&error=' + tornado.escape.url_escape("Passwords don't match")
            self.redirect('/' + error)
        if not db.username_available(username):
            error = u'?activity=register&error=' + tornado.escape.url_escape("This username has been taken")
            self.redirect('/' + error)

        user_id = db.create_account(username, password)
        if user_id is not None:
            json = tornado.escape.json_encode({'userid': user_id})
            self.set_secure_cookie('skillbook_user', str(user_id), expires_days=90)
            self.redirect('/home')
        else:
            self.redirect('/')


class HomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('home.html')


if __name__ == "__main__":
    application = tornado.web.Application(
        handlers = [
            (r'/', MainHandler),
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            (r'/register', RegistrationHandler),
            (r'/home', HomeHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        cookie_secret=config.web.cookie_secret,
        xsrf_cookies=True,
        login_url='/',
        debug=True
    )

    print("Listening on :" + str(config.web.port))
    application.listen(config.web.port)
    tornado.ioloop.IOLoop.instance().start()

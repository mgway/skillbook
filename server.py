import tornado.ioloop
import tornado.escape
import tornado.web
import os

import db

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("skillbook_user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)


class MainHandler(BaseHandler):
    def get(self):
        self.write("Hello, Skillbook")


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
            self.redirect('/')
        else:
            self.redirect('/login')


if __name__ == "__main__":
    application = tornado.web.Application(
        handlers = [
            (r'/', MainHandler),
            (r'/login', LoginHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        cookie_secret='supersecretzomg',
        xsrf_cookies=True,
        debug=True
    )

    print("Listening on :8888")
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

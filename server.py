import tornado.ioloop
import tornado.escape
import tornado.web
import os

import db
import api
import config
import eveapi

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
        else:
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
        self.render('userhome.html')


class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        userid = self.get_current_user()
        keys = db.get_keys_for_user(userid)
        prefs = db.get_preferences(userid)
        try:
            error = self.get_argument("error")
            context = self.get_argument("context")
        except:
            error = ""
            context = ""
        self.render('settings.html', keys=keys, prefs=prefs,
                error=error, context=context)


class SettingsKeyHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        userid = self.get_current_user()
        keyid = self.get_argument('keyid')
        vcode = self.get_argument('vcode')
        if keyid.strip() == "" or vcode.strip() == "":
            error = u'?context=key&error=' + tornado.escape.url_escape('Please enter a valid Key ID and vCode')
            self.redirect('/settings' + error)
        else:
            try:
                api.add_key(userid, keyid, vcode)
                self.redirect('/settings')
            except (eveapi.APIException, eveapi.HttpException) as e:
                error = u'?context=key&error=' + tornado.escape.url_escape(e.message)
                self.redirect('/settings' + error)


class SettingsPrefsHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        userid = self.get_current_user()
        mail = self.get_argument('email', default="")
        letter = self.get_argument('newsletter', default=False)
        if mail.strip() == "":
            self.redirect('/settings')
        else:
            db.change_preferences(userid, mail, letter)
            self.redirect('/settings')


class SettingsPasswordHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        userid = self.get_current_user()
        password = self.get_argument('current_password')
        new_pw = self.get_argument('password')
        new_pw_dup = self.get_argument('password_dup')

        if new_pw != new_pw_dup:
            error = u'?context=password&error=' + tornado.escape.url_escape('Passwords don\'t match')
            self.redirect('/settings' + error)
        else:
            try:
                db.change_password(userid, password, new_pw)
                self.redirect('/settings')
            except db.UserError as e:
                error = u'?context=password&error=' + tornado.escape.url_escape(e.message)
                self.redirect('/settings' + error)


if __name__ == "__main__":
    application = tornado.web.Application(
        handlers = [
            (r'/', MainHandler),
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            (r'/register', RegistrationHandler),
            (r'/home', HomeHandler),
            (r'/settings', SettingsHandler),
            (r'/settings/keys', SettingsKeyHandler),
            (r'/settings/prefs', SettingsPrefsHandler),
            (r'/settings/password', SettingsPasswordHandler),
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

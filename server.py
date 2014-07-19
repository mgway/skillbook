#!/usr/bin/env python3

import tornado.ioloop
import tornado.escape
import tornado.web
import os
import simplejson 
import redis

import db
import api
import config
import eveapi


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("skillbook_user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)
    def set_current_user(self, user_id):
        json = tornado.escape.json_encode({'userid': user_id})
        self.set_secure_cookie('skillbook_user', str(user_id), expires_days=90)


class MainHandler(BaseHandler):
    def get(self):
        error = self.get_argument("error", "")
        self.render('index.html', error=error)


class AboutHandler(BaseHandler):
    def get(self):
        self.render('info.html')


class HelpHandler(BaseHandler):
    def get(self):
        self.render('help.html')


class LoginHandler(BaseHandler):
    attrs = {'login_error': '', 'register_error': ''}
    def get(self):
        self.render('auth.html', **self.attrs)
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        user_id = db.check_login(username, password)
        if user_id is not None:
            self.set_current_user(user_id)
            self.redirect('/skills')
        else:
            self.attrs['login_error'] = 'Incorrect username or password'
            self.render('auth.html', **self.attrs)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('skillbook_user')
        self.redirect('/')


class RegistrationHandler(BaseHandler):
    attrs = {'login_error': '', 'register_error': ''}
    def get(self):
        self.render('auth.html', **self.attrs)
    def post(self):
        username = self.get_argument('username').lower()
        password = self.get_argument('password')
        password_again = self.get_argument('password_rep')
        
        if password != password_again:
            self.attrs['register_error'] = 'Passwords don\'t match'
            self.render('auth.html', **self.attrs)
        elif not db.username_available(username):
            self.attrs['register_error'] = 'This username has been taken'
            self.render('auth.html', **self.attrs)
        else:
            user_id = db.create_account(username, password)
            if user_id is not None:
                self.set_current_user(user_id)
                self.redirect('/settings')
            else:
                self.redirect('/')


class SkillsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('skills.html')


class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        userid = self.get_current_user()
        keys = db.get_keys(userid)
        prefs = db.get_preferences(userid)
        error = self.get_argument("error", "")
        context = self.get_argument("context", "")
        self.render('settings.html', keys=keys, prefs=prefs,
                error=error, context=context)


class SettingsKeyHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        userid = self.get_current_user()
        keyid = self.get_argument('keyid')
        vcode = self.get_argument('vcode', default='')
        remove = self.get_argument('remove', False)
        
        if remove == 'yes':
            api.remove_key(userid, keyid)
            self.set_status(200)
            return self.finish()

        if keyid.strip() == "" or vcode.strip() == "":
            error = u'?context=key&error=' + tornado.escape.url_escape('Please enter a valid Key ID and vCode')
            self.redirect('/settings' + error)
        else:
            try:
                api.add_key(userid, keyid, vcode)
                self.redirect('/settings')
            except (eveapi.APIException, eveapi.HttpException, api.SkillbookException, db.UserError) as e:
                error = u'?context=key&error=' + tornado.escape.url_escape(e.message)
                self.redirect('/settings' + error)
            except Exception as e:
                error = u'?context=key&error=' + tornado.escape.url_escape('An unknown error has occurred')
                print(e)
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


class AjaxHandler(BaseHandler):
    def write_message(self, message, pre=True):
        def json_handler(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            else:
                raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))
        
        self.set_header('Content-Type', 'application/json')
        if pre:
            self.finish(message)
        else:
            self.finish(simplejson.dumps(message, use_decimal=True, default=json_handler))


class DynamicAjaxHandler(AjaxHandler):
    def get(self, command, arg):
        userid = self.get_current_user()

        try:
            if command == 'characters':
                characters = api.get_characters(userid)
                self.write_message(characters)
            elif command == 'sheet':
                sheet = api.get_character_sheet(userid, arg)
                self.write_message(sheet)
            elif command == 'skills':
                skills = api.get_character_skills(userid, arg)
                self.write_message(skills)
            elif command == 'queue':
                skills = api.get_character_queue(userid, arg)
                self.write_message(skills)
            else:
                self.set_status(404)
                self.write_message({'error': 'Unknown resource: ' + str(command)}, pre=False)

        except api.SkillbookException as e:
            self.set_status(403, e.message)
            self.write_message({'error': e.message}, pre=False)


class StaticAjaxHandler(AjaxHandler):
    def get(self, command):
        args = self.get_argument('args', '')

        if command == 'skills':
            self.write_message(api.get_skills())
        else:
            print('unhandled command: ' + str(command))


if __name__ == "__main__":
    application = tornado.web.Application(
        handlers = [
            (r'/', MainHandler),
            (r'/info', AboutHandler),
            (r'/help', HelpHandler),
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            (r'/register', RegistrationHandler),
            (r'/skills.*', SkillsHandler),
            (r'/api/static/(.+)', StaticAjaxHandler),
            (r'/api/(?P<command>[^\/]+)/?(?P<arg>[\d]+)?', DynamicAjaxHandler),
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
        debug=config.web.debug
    )

    print("Listening on :" + str(config.web.port))
    application.listen(config.web.port)
    tornado.ioloop.IOLoop.instance().start()

#!/usr/bin/env python3

import tornado.ioloop
import tornado.escape
import tornado.web
import os
import simplejson 

import db
import api
import config
import eveapi
import mail


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie('skillbook_user')
        if not user_json: return None
        return tornado.escape.json_decode(user_json)
    def set_current_user(self, user_id):
        json = tornado.escape.json_encode({'userid': user_id})
        self.set_secure_cookie('skillbook_user', str(user_id), expires_days=90)


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


class MainHandler(BaseHandler):
    def get(self):
        self.render('index.html')


class AboutHandler(BaseHandler):
    def get(self):
        self.render('info.html')


class HelpHandler(BaseHandler):
    def get(self):
        self.render('help.html')
        

class SkillsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('skills.html')


class PlansHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('plans.html')


class LoginHandler(BaseHandler):
    messages = {'login_error': '', 'register_error': ''}
    def get(self):
        self.render('auth.html', **self.messages)
    def post(self):
        messages = self.messages.copy()
        username = self.get_argument('username')
        password = self.get_argument('password')
        
        user_id = db.check_login(username, password)
        if user_id is not None:
            self.set_current_user(user_id)
            self.redirect('/skills')
        else:
            messages['login_error'] = 'Incorrect username or password'
            self.render('auth.html', **messages)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('skillbook_user')
        self.redirect('/')


class RegistrationHandler(BaseHandler):
    messages = {'login_error': '', 'register_error': ''}
    def get(self):
        self.render('auth.html', **self.messages)
    def post(self):
        messages = self.messages.copy()
        username = self.get_argument('username').lower()
        password = self.get_argument('password')
        password_again = self.get_argument('password_rep')
        
        if password != password_again:
            messages['register_error'] = 'Passwords don\'t match'
            self.render('auth.html', **messages)
        elif not db.username_available(username):
            messages['register_error'] = 'This username has been taken'
            self.render('auth.html', **messages)
        else:
            user_id = db.create_account(username, password)
            if user_id is not None:
                self.set_current_user(user_id)
                self.redirect('/settings')
            else:
                self.redirect('/')


class SettingsHandler(BaseHandler):
    messages = {'mail_error': '', 'mail': '', 'password_error': '', 'password': ''}
    
    @tornado.web.authenticated
    def get(self):
        user_id = self.get_current_user()
        prefs = db.get_preferences(user_id)
        self.render('settings.html', prefs=prefs, **self.messages)
        
    @tornado.web.authenticated
    def post(self):
        user_id = self.get_current_user()
        messages = self.messages.copy()
        
        if self.get_argument('email-form', default=None):
            mail = self.get_argument('email', default='')
            letter = self.get_argument('newsletter', default=False)
            resubscribe = self.get_argument('resubscribe', default=False) == 'on'
            
            db.change_preferences(user_id, mail, letter, resubscribe)
            messages['mail'] = 'Mail preferences updated'

        elif self.get_argument('password-form', default=None):
            password = self.get_argument('current_password')
            new_pw = self.get_argument('password')
            new_pw_dup = self.get_argument('password_dup')
            if new_pw != new_pw_dup:
                messages['password_error'] = 'Passwords don\'t match'
            else:
                try:
                    db.change_password(user_id, password, new_pw)
                    messages['password'] = 'Password successfully changed'
                except db.UserError as e:
                    messages['password_error'] = e.message
        
        prefs = db.get_preferences(user_id)
        self.render('settings.html', prefs=prefs, **messages)


class MailHandler(BaseHandler):
    messages = {'title': '', 'message': ''}
    
    def get(self, action):
        messages = self.messages.copy()
        user_id = self.get_argument('u', default=None)
        token = self.get_argument('t', default=None)
        if action == 'confirm':
            messages['title'] = 'Email Confirmation'
            if db.confirm_email(user_id, token):
                messages['message'] = 'Address successfully confirmed. You may now receive elect \
                to receive notifications about your character\'s status.'
            else:
                messages['message'] = 'Invalid token, address not confirmed'
        elif action == 'unsubscribe':
            messages['title'] = 'Unsubscribe'
            if db.unsubscribe_email(user_id, token):
                messages['message'] = 'Unsubscribe successful. You may re-enable notification email \
                at any time from the settings page'
            else:
                messages['message'] = 'Invalid token, address not unsubscribed'
        else:
            return self.set_status(400)
        
        self.render('mail.html', **messages)
        
    @tornado.web.authenticated
    def post(self, action):
        user_id = self.get_current_user()
        
        if action == 'confirm':
            user = db.get_email_attributes(user_id)
            if not user.valid_email:
                mail.send_confirmation(user)
                return self.set_status(200)
            else:
                return self.set_status(304)
        else:
            return self.set_status(400)

# API Methods
class KeyApiHandler(AjaxHandler):
    @tornado.web.authenticated
    def get(self, key_id = None):
        user_id = self.get_current_user()
        if key_id != None:
            self.set_status(405)
        else:
            self.write_message(api.get_keys(user_id), pre=False)
        
    @tornado.web.authenticated
    def post(self, key_id = None):
        user_id = self.get_current_user()
        
        if key_id != None:
            return self.set_status(405)
            
        try:
            body = simplejson.loads(self.request.body)
            key_id = body['keyid']
            vcode = body['vcode']
        except (simplejson.JSONDecodeError, KeyError):
            self.set_status(400)
            return self.write_message({'error': 'Enter a valid Key ID and vCode'}, pre=False)
        
        try:
            api.add_key(user_id, key_id, vcode)
            self.set_status(201)
            self.write_message(api.get_keys(user_id), pre=False)
        except (eveapi.APIException, eveapi.HttpException, api.SkillbookException, db.UserError) as e:
            self.set_status(400)
            self.write_message({'error': e.message}, pre=False)
        except Exception as e:
            self.set_status(500)
            self.write_message({'error': 'An unknown error has occurred'}, pre=False)
        
    @tornado.web.authenticated  
    def delete(self, key_id = None):
        user_id = self.get_current_user()
        if key_id == None:
            self.set_status(400)
            self.write_message({'error': 'You must specify a Key ID to remove'}, pre=False)
        else:
            api.remove_key(user_id, key_id)
            self.set_status(204)


class CharacterApiHandler(AjaxHandler):
    @tornado.web.authenticated
    def get(self, character_id = None, subtype = None):
        user_id = self.get_current_user()
        
        try:
            if not character_id:
                characters = api.get_characters(user_id)
                self.write_message(characters)
            elif subtype == 'skills':
                skills = api.get_character_skills(user_id, character_id)
                self.write_message(skills)
            elif subtype == 'queue':
                skills = api.get_character_queue(user_id, character_id)
                self.write_message(skills)
            elif character_id and subtype == None:
                sheet = api.get_character_sheet(user_id, character_id)
                self.write_message(sheet)
            else:
                self.set_status(404)
                self.write_message({'error': 'Resource not found'}, pre=False)
            
        except api.SkillbookException as e:
            self.set_status(403)
            self.write_message({'error': e.message}, pre=False)


class PlanApiHandler(AjaxHandler):
    @tornado.web.authenticated
    def get(self, plan_id = None, entry_id = None):
        user_id = self.get_current_user()
        
        if not plan_id:
            self.write_message(api.get_plans(user_id))
        elif plan_id and entry_id == None:
            self.write_message(api.get_plan(user_id, plan_id))
        else:
            self.set_status(404)
            self.write_message({'error': 'Resource not found'}, pre=False)
        
    @tornado.web.authenticated
    def post(self, plan_id = None, entry_id = None):
        user_id = self.get_current_user()
        
        try:
            body = simplejson.loads(self.request.body)
        except simplejson.JSONDecodeError:
            self.set_status(400)
            return self.write_message({'error': 'Character ID and plan name are required'}, pre=False)
        
        if not plan_id:
            try:
                character_id = body['character_id']
                name = body['name']
                description = body['description']
            except KeyError:
                self.set_status(400)
                return self.write_message({'error': 'Character ID and plan name are required'}, pre=False)
                
            plans = api.add_plan(user_id, character_id, name, description)
            self.write_message(plans)
        elif plan_id:
            try:
                plan_id = body['plan_id']
                type_id = body['name']
                level = body['description']
                priority = body['priority']
                sort = body['sort']
                meta = body.get('sort', None)
            except KeyError:
                self.set_status(400)
                return self.write_message({'error': 'Required attribute was missing'}, pre=False)
                
            api.add_plan_entry(plan_id, type_id, level, priority, sort, meta=None)
    
class StaticApiHandler(AjaxHandler):
    @tornado.web.authenticated
    def get(self, command):
        args = self.get_argument('args', '')
        
        if command == 'skills':
            self.write_message(api.get_all_skills())
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
            (r'/plans.*', PlansHandler),
            (r'/mail/(?P<action>[\w]+)/?', MailHandler),
            (r'/api/static/(.+)', StaticApiHandler),
            (r'/api/plan/(?P<plan_id>[\d]+)?/?(?P<entry_id>[\d]+)?/?', PlanApiHandler),
            (r'/api/character/(?P<character_id>[\d]+)?/?(?P<subtype>[\w]+)?/?', CharacterApiHandler),
            (r'/api/key/(?P<key_id>[\d]+)?/?', KeyApiHandler),
            (r'/settings', SettingsHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        cookie_secret=config.web.cookie_secret,
        xsrf_cookies=True,
        login_url='/login',
        debug=config.web.debug
    )

    print("Listening on :" + str(config.web.port))
    application.listen(config.web.port)
    tornado.ioloop.IOLoop.instance().start()

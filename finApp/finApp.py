import os
import urllib
import datetime
import uuid
import logging

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import images

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def userProfile_key(email):
    return ndb.Key('UserProfile', email)
    
class UserProfile(ndb.Model):
    email = ndb.StringProperty(indexed=True, required=True)
    name = ndb.StringProperty()
    designation = ndb.StringProperty()
    salary = ndb.IntegerProperty()
    currency = ndb.StringProperty()
   
class AddUpdateProfile(webapp2.RequestHandler):
    def post(self):
        #This will be used to add/update profile in a datastore. Will be called when the user clicks on submit button on the Profile Page
        template = JINJA_ENVIRONMENT.get_template('profile.html')
        error = None
        name = self.request.get('name')
        designation = self.request.get('designation')
        salary = self.request.get('salary')
        currency = self.request.get('currency')
        logging.info("Name = "+name)
        logging.info("Designation = "+designation)
        logging.info("Salary = "+salary)
        logging.info("Currecny = "+currency)
        
        profile = UserProfile(parent=userProfile_key(users.get_current_user().email()))
        profile.name = name
        profile.designation = designation
        profile.salary = int(salary)
        profile.currency = currency
        profile.email = str(users.get_current_user().email())
        
        profile.put()
        
        #Go back to main page. TODO : Change this to update 
        self.redirect('/profile')
    
class Profile(webapp2.RequestHandler):

    def get(self):
        logging.info("Inside Profile Page")
        user = users.get_current_user()
        if user:
            logging.info("Found a user inside MainPage")
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'SIGN OUT'
            template_values = {
            'user': user.nickname(),
            'url': url,
            }
            template = JINJA_ENVIRONMENT.get_template('profile.html')
            self.response.write(template.render(template_values))
        else:
            logging.info("User not found. Loading Landing page")
            template_values = {
                'url' : users.create_login_url(self.request.uri)
            }
            template = JINJA_ENVIRONMENT.get_template('landing.html')
            self.response.write(template.render(template_values))
            
            
class MainPage(webapp2.RequestHandler):

    def get(self):
        logging.info("Inside MainPage")
        user = users.get_current_user()
        if user:
            logging.info("Found a user inside MainPage")
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'SIGN OUT'
            template_values = {
            'user': user.nickname(),
            'url': url,
            'userPage' : "no",
            'url_linktext': url_linktext,
            }
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
        else:
            logging.info("User not found. Loading Landing page")
            template_values = {
                'url' : users.create_login_url(self.request.uri)
            }
            template = JINJA_ENVIRONMENT.get_template('landing.html')
            self.response.write(template.render(template_values))
            
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/profile', Profile),
    ('/addProfile', AddUpdateProfile)
], debug=True)
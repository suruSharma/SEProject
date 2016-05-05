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
    
def getProfileInformation(userId):
    profileInfo = UserProfile.query(UserProfile.userId == userId).fetch()
    return profileInfo  
    
def profile_key(userId):
    return ndb.Key('Profile', userId)   
    
class UserProfile(ndb.Model):
    userId = ndb.IntegerProperty(indexed=True, required=True)
    email = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    designation = ndb.StringProperty()
    salary = ndb.IntegerProperty()
    currency = ndb.StringProperty()
    nickName = ndb.StringProperty()
    
def encode(s):
    return abs(hash(s)) % (10 ** 8)

class UpdateProfile(webapp2.RequestHandler):
    def get(self):
        logging.info("Inside get of Updateprofile")
    def post(self):
        logging.info("Inside update profile")
        template = JINJA_ENVIRONMENT.get_template('profile.html')
        error = None
        user = users.get_current_user()
        
        name = self.request.get('name')
        designation = self.request.get('designation')
        salary = self.request.get('salary')
        currency = self.request.get('currency')
        userId = self.request.get('userId')
        nickName  =self.request.get('nickName')
        
        logging.info("Name = "+name)
        logging.info("Designation = "+designation)
        logging.info("Salary = "+salary)
        logging.info("Currency = "+currency)
        logging.info("UserId = "+userId)
        
        profile = getProfileInformation(int(userId))
        profile[0].userId = int(userId)
        profile[0].nickName = nickName
        profile[0].name = name
        profile[0].designation = designation
        profile[0].salary = int(salary)
        profile[0].currency = currency
        profile[0].email = str(users.get_current_user().email())
        profile[0].put()
        
        #Go back to main page. TODO : Change this to update 
        self.redirect('/')
    
class SaveProfile(webapp2.RequestHandler):
    def post(self):
        #This will be used to add/update profile in a datastore. Will be called when the user clicks on submit button on the Profile Page
        template = JINJA_ENVIRONMENT.get_template('profile.html')
        error = None
        user = users.get_current_user()
        
        name = self.request.get('name')
        designation = self.request.get('designation')
        salary = self.request.get('salary')
        currency = self.request.get('currency')
        userId = self.request.get('userId')
        nickName = self.request.get('nickName')
        
        logging.info("Name = "+name)
        logging.info("Designation = "+designation)
        logging.info("Salary = "+salary)
        logging.info("Currency = "+currency)
        logging.info("UserId = "+userId)
        
        profile = UserProfile(parent=profile_key(int(userId)))
        profile.userId = int(userId)
        profile.nickName = nickName
        profile.name = name
        profile.designation = designation
        profile.salary = int(salary)
        profile.currency = currency
        profile.email = str(users.get_current_user().email())
        profile.put()
        
        #Go back to main page. TODO : Change this to update 
        self.redirect('/')
    
class LoadProfile(webapp2.RequestHandler):
    def get(self):
        logging.info("Inside Profile Page")
        user = users.get_current_user()
        
        if user:
            userCode = encode(user.email())
            profileInfo = getProfileInformation(userCode)
            logging.info("Found a user inside Profile Page")
            url = users.create_logout_url(self.request.uri)
            if profileInfo is None or not profileInfo:
                #The user is not present in the system yet
                logging.info("Email = "+user.email())
                logging.info("Profile Info not found")
                template_values = {
                'user': user.nickname(),
                'url': url,
                'email' : user.email(),
                'userId' : userCode,
                'button' : 'SAVE',
                'action' : 'saveProfile'
                }
            else:
                logging.info("Profile Info found")
                template_values = {
                'user': user.nickname(),
                'url': url,
                'name' : profileInfo[0].name,
                'designation' : profileInfo[0].designation,
                'salary' : profileInfo[0].salary,
                'currency' : profileInfo[0].currency,
                'email' : profileInfo[0].email,
                'userId' : userCode,
                'button' : 'UPDATE',
                'action' : 'updateProfile',
                'nickName' : profileInfo[0].nickName
                }
                
            template_values = template_values
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
    ('/loadProfile', LoadProfile),
    ('/saveProfile', SaveProfile),
    ('/updateProfile', UpdateProfile)
], debug=True)
import os
import urllib
import datetime
import uuid
import logging
import time

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

def household_key(householdId):
    return ndb.Key('Household', householdId)

class Household(ndb.Model):
    householdId = ndb.StringProperty(indexed=True, required=True)
    householdName = ndb.StringProperty()
    
class HouseholdMembers(ndb.Model):
    householdId = ndb.StringProperty(indexed=True, required=True)
    members = ndb.StringProperty()
    
class UserProfile(ndb.Model):
    userId = ndb.IntegerProperty(indexed=True, required=True)
    email = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    designation = ndb.StringProperty()
    salary = ndb.IntegerProperty()
    currency = ndb.StringProperty()
    nickName = ndb.StringProperty()
    company = ndb.StringProperty()
    households = ndb.StringProperty(repeated=True)
    
def encode(s):
    return abs(hash(s)) % (10 ** 8)

class AddHousehold(webapp2.RequestHandler):
    def get(self):
        logging.info("Inside get of Add Household")
    def post(self):
        template = JINJA_ENVIRONMENT.get_template('household.html')
        householdName = self.request.get('householdName')
        householdId = addHousehold(householdName)
        memberCount = self.request.get('count')
        for i in range(0, int(memberCount)):
            memberName = self.request.get('name'+str(i))
            memberUsername = self.request.get('email'+str(i))
            isEarning = self.request.get('earning'+str(i))
            if(isEarning is None or not isEarning):
                isEarning = "no"
            else:
                isEarning = "yes"
            
            
                
        
def addHousehold(householdName):
    householdId = str(uuid.uuid4())
    household = Household(parent=household_key(householdId))
    household.householdId = householdId
    household.householdName = householdName
    
    household.put()
    
    return householdId
        
class UpdateProfile(webapp2.RequestHandler):
    def get(self):
        logging.info("Inside get of Updateprofile")
    def post(self):
        template = JINJA_ENVIRONMENT.get_template('profile.html')
        error = None
        user = users.get_current_user()
        
        name = self.request.get('name')
        designation = self.request.get('designation')
        salary = self.request.get('salary')
        currency = self.request.get('currency')
        userId = self.request.get('userId')
        nickName  =self.request.get('nickName')
        company = self.request.get('company')
        
        profile = getProfileInformation(int(userId))
        profile[0].userId = int(userId)
        profile[0].nickName = nickName
        profile[0].name = name
        profile[0].designation = designation
        profile[0].salary = int(salary)
        profile[0].currency = currency
        profile[0].email = str(users.get_current_user().email())
        profile[0].company = company
        profile[0].put()
        
        #Go back to main page. TODO : Change this to update 
        time.sleep(3)
        self.redirect('/loadProfile')
    
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
        company = self.request.get('company')
        
        profile = UserProfile(parent=profile_key(int(userId)))
        profile.userId = int(userId)
        profile.nickName = nickName
        profile.name = name
        profile.designation = designation
        profile.salary = int(salary)
        profile.currency = currency
        profile.email = str(users.get_current_user().email())
        profile.company = company
        profile.put()
        
        #Go back to main page. TODO : Change this to update 
        time.sleep(3)
        self.redirect('/loadProfile')
    
class LoadProfile(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        if user:
            userCode = encode(user.email())
            profileInfo = getProfileInformation(userCode)
            url = users.create_logout_url(self.request.uri)
            if profileInfo is None or not profileInfo:
                #The user is not present in the system yet
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
                'nickName' : profileInfo[0].nickName,
                'company' : profileInfo[0].company
                }
                
            template_values = template_values
            template = JINJA_ENVIRONMENT.get_template('profile.html')
            self.response.write(template.render(template_values))
        else:
            template_values = {
                'url' : users.create_login_url(self.request.uri)
            }
            template = JINJA_ENVIRONMENT.get_template('landing.html')
            self.response.write(template.render(template_values))
            
class CreateHousehold(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        if user:
            userCode = encode(user.email())
            profileInfo = getProfileInformation(userCode)
            url = users.create_logout_url(self.request.uri)
            if profileInfo is None or not profileInfo:
                #The user is not present in the system yet
                template_values = {
                'user': user.nickname(),
                'url': url,
                'email' : user.email(),
                'userId' : userCode,
                'button' : 'SAVE',
                'action' : 'saveProfile'
                }
            else:
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
                'nickName' : profileInfo[0].nickName,
                'company' : profileInfo[0].company
                }
                
            template_values = template_values
            template = JINJA_ENVIRONMENT.get_template('household.html')
            self.response.write(template.render(template_values))
        else:
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
    ('/updateProfile', UpdateProfile),
    ('/createHousehold', CreateHousehold),
    ('/addHousehold', AddHousehold)
], debug=True)
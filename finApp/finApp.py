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
DEFAULT_KEY = "default_key"   
def getProfileInformation(userId):
    return UserProfile.query(UserProfile.userId == userId).fetch()
    
def profile_key(userId):
    return ndb.Key('Profile', userId)

def household_key(householdId):
    return ndb.Key('Household', householdId)
    
def householdMembers_key():
    return ndb.Key('HouseholdMembers', DEFAULT_KEY)
    
def getHouseholdMemberCombo(householdId, profileId):
    return HouseholdMembers.query(HouseholdMembers.householdId == householdId and HouseholdMembers.member == profileId).fetch()
    
def getHousehold(householdId):
    return Household.query(Household.householdId == householdId).fetch()

def encode(s):
    return abs(hash(s)) % (10 ** 8)
    
def addHouseholdMembers(profileIdList, householdId):
    for profile in profileIdList:
        household = getHousehold(householdId)
        if(household is None or not household):
            householdMemberCombo = HouseholdMembers(parent=householdMembers_key())
            householdMemberCombo.householdId = householdId
            householdMemberCombo.member = profile
            householdMemberCombo.put()
        else:
            #Change this to update existing households
            logging.info("Found the combo :     " + str(householdId) + "->" + str(profile))
            logging.info(householdMemberCombo)
        
def addProfileToDS(name, emailId, isEarning, householdName, userEmail):
    userCode = encode(emailId)
    profile = getProfileInformation(int(userCode))
    if(profile is None or not profile):
        profile = UserProfile(parent=profile_key(int(userCode)))
        profile.userId = int(userCode)
        profile.name = name
        profile.email = emailId
        profile.isEarning = True if isEarning == "yes" else False
        profile.put()
    sendMailToMember(name, emailId, householdName, userEmail)
    return userCode

def sendMailToMember(name, emailId, householdName, userEmail):
    mail.send_mail(sender=userEmail,
                    to=emailId,
                    subject="You have been added to household : "+householdName,
                    body = """Hi """+name+"""
                        You have been added to """+householdName+""" by """+userEmail+""". Please click on http://toalmoal.appspot.com/loadProfile to update your profile""")  
                       
def addHousehold(householdName):
    householdId = str(uuid.uuid4())
    household = getHousehold(householdId)
    if(household is None or not household):
        household = Household(parent=household_key(householdId))
        household.householdId = householdId
        household.householdName = householdName
        household.put()
    
    return householdId

def getHouseholdsListByUserId(userId):
    households = HouseholdMembers.query(HouseholdMembers.member == userId).fetch()
    return households

def getHouseholdMembersByHouseholdId(householdId):
    hhMembers = HouseholdMembers.query(HouseholdMembers.householdId == householdId).fetch()
    return hhMembers

def getHousehold(hId):
    household = Household.query(Household.householdId == hId).fetch()
    return household
    
def getAllMembersOfHousehold(hId):
    hhMembers = getHouseholdMembersByHouseholdId(hId)
    members = []
    for hhm in hhMembers:
        memberProfile = getProfileInformation(hhm.member)[0]
        members.append(memberProfile)
    return members
    
def getListOfMemberNames(members):
    names = []
    for m in members:
        names.append(m.email if m.name is None or not m.name else m.name.split()[0])
    return names
    
#Param houeholds = lis of households a person belongs to    
def getHouseholdInformation(households):
    householdTableInfo = []
    for hh in households:
        hId = hh.householdId
        hhInfo = getHousehold(hId)
        members = getAllMembersOfHousehold(hhInfo[0].householdId)
        names = getListOfMemberNames(members)
        hh = {
            'hname' : hhInfo[0].householdName,
            'hId' : hhInfo[0].householdId,
            'members' : ', '.join(names)
        }
        householdTableInfo.append(hh)
        
    return householdTableInfo

def createMemberRows(members):
    memberRows = []
    i = 1
    for m in members:
        memObj = {
            'name' : m.name,
            'email' : m.email,
            'isEarning' : "checked" if m.isEarning == True else "",
            'id' : i
        }
        i = i+1
        memberRows.append(memObj)
        
    return memberRows

def deleteHouseholdRecords(hhid):
    hh = getHousehold(str(hhid))
    #delete the Household entry
    hh[0].key.delete()
    
    #delete the HouseholdMembers entry
    members = getHouseholdMembersByHouseholdId(str(hhid))
    for m in members:
        m.key.delete()
        
class Household(ndb.Model):
    householdId = ndb.StringProperty(indexed=True, required=True)
    householdName = ndb.StringProperty()
    
class HouseholdMembers(ndb.Model):
    householdId = ndb.StringProperty(indexed=True, required=True)
    member = ndb.IntegerProperty()
    
class UserProfile(ndb.Model):
    userId = ndb.IntegerProperty(indexed=True, required=True)
    email = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    designation = ndb.StringProperty()
    salary = ndb.IntegerProperty()
    currency = ndb.StringProperty()
    debt = ndb.IntegerProperty()
    company = ndb.StringProperty()
    households = ndb.StringProperty(repeated=True)
    isEarning = ndb.BooleanProperty()
    
class AddHousehold(webapp2.RequestHandler):
    def post(self):
        template = JINJA_ENVIRONMENT.get_template('household.html')
        householdName = self.request.get('householdName')
        user = users.get_current_user().email()
        householdId = addHousehold(householdName)
        count = self.request.get('memCount')
        profileIdList = []
        count = 2 if int(count) == 1 else int(count)
        for i in range(1, count):
            memberName = self.request.get('name'+str(i))
            memberUsername = self.request.get('email'+str(i))
            isEarning = self.request.get('earning'+str(i))
            if(isEarning is None or not isEarning):
                isEarning = "no"
            else:
                isEarning = "yes"
            
            profileId = addProfileToDS(memberName, memberUsername, isEarning,householdName, user)
            profileIdList.append(profileId)
            
        addProfileToDS("", user, "no", householdName, user)#This is to add user to profile table, if he doesn't exist
        profileIdList.append(int(encode(user)))
        addHouseholdMembers(profileIdList, householdId)
        
        time.sleep(2)
        self.redirect('/loadProfile')
              
class UpdateProfile(webapp2.RequestHandler):
    def post(self):
        template = JINJA_ENVIRONMENT.get_template('profile.html')
        error = None
        user = users.get_current_user()
        
        name = self.request.get('name')
        designation = self.request.get('designation')
        salary = int(self.request.get('salary'))
        currency = self.request.get('currency')
        userId = self.request.get('userId')
        debt  = int(self.request.get('debt'))
        company = self.request.get('company')
        
        profile = getProfileInformation(int(userId))
        profile[0].userId = int(userId)
        profile[0].debt = debt
        profile[0].name = name
        profile[0].designation = designation
        profile[0].salary = salary
        profile[0].currency = currency
        profile[0].email = str(users.get_current_user().email())
        profile[0].company = company
        profile[0].isEarning = True if salary > 0 else False
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
        salary = int(self.request.get('salary'))
        currency = self.request.get('currency')
        userId = self.request.get('userId')
        debt = self.request.get('debt')
        company = self.request.get('company')
        
        profile = UserProfile(parent=profile_key(int(userId)))
        profile.userId = int(userId)
        profile.debt = int(debt)
        profile.name = name
        profile.designation = designation
        profile.salary = salary
        profile.currency = currency
        profile.email = str(users.get_current_user().email())
        profile.company = company
        profile.isEarning = True if salary > 0 else False
        profile.put()
        
        #Go back to main page. TODO : Change this to update 
        time.sleep(3)
        self.redirect('/loadProfile')
    
class LoadProfile(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        if user:
            userCode = encode(user.email())
            households = getHouseholdsListByUserId(int(userCode))#This returns a list of  households a person belongs to
            householdTableInfo = getHouseholdInformation(households)#This returns a list of data to populate the household table
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
                'action' : 'saveProfile',
                'hhTable' : householdTableInfo
                }
            else:
                template_values = {
                'user': user.nickname(),
                'url': url,
                'name' : '' if profileInfo[0].name == None else profileInfo[0].name,
                'designation' : '' if profileInfo[0].designation == None else profileInfo[0].designation,
                'salary' : '' if profileInfo[0].salary == None else profileInfo[0].salary,
                'currency' : profileInfo[0].currency,
                'email' : profileInfo[0].email,
                'userId' : profileInfo[0].userId,
                'button' : 'UPDATE',
                'action' : 'updateProfile',
                'debt' : '' if profileInfo[0].debt == None else profileInfo[0].debt,
                'company' : '' if profileInfo[0].company == None else profileInfo[0].company,
                'hhTable' : householdTableInfo
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

class UpdateHousehold(webapp2.RequestHandler):
    def get(self):
        logging.info('update household')
    def post(self):
        template = JINJA_ENVIRONMENT.get_template('household.html')
        householdName = self.request.get('householdName')
        user = users.get_current_user().email()
        hhid = self.request.get('hhid')
        deleteHouseholdRecords(hhid)
        count = self.request.get('memCount')
        profileIdList = []
        count = 2 if int(count) == 1 else int(count)
        for i in range(1, count):
            memberName = self.request.get('name'+str(i))
            memberUsername = self.request.get('email'+str(i))
            isEarning = self.request.get('earning'+str(i))
            if(isEarning is None or not isEarning):
                isEarning = "no"
            else:
                isEarning = "yes"
            
            #profileId = addProfileToDS(memberName, memberUsername, isEarning,householdName, user)
            profileIdList.append(profileId)
            
        #addProfileToDS("", user, "no", householdName, user)#This is to add user to profile table, if he doesn't exist
        #profileIdList.append(int(encode(user)))
        addHouseholdMembers(profileIdList, householdId)
        
        time.sleep(2)
        self.redirect('/loadProfile')
        
class CreateHousehold(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        if user:
            userCode = encode(user.email())
            url = users.create_logout_url(self.request.uri)
            hhId = self.request.get('hid')
            if(hhId is None or not hhId):
                template_values = {
                    'user': user.nickname(),
                    'url': url,
                    'action' : 'addHousehold',
                    'button' : 'SAVE'
                    }
            else:
                hh = getHousehold(hhId)
                logging.info(hh)
                hhMembers = getAllMembersOfHousehold(hhId)
                memberRows = createMemberRows(hhMembers)
                template_values = {
                    'user': user.nickname(),
                    'url': url,
                    'hhname' : hh[0].householdName,
                    'hhid' : hh[0].householdId,
                    'members' : memberRows,
                    'count' : int(len(memberRows))+1,
                    'action' : 'updateHousehold',
                    'button' : 'UPDATE'
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
        user = users.get_current_user()
        if user:
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
    ('/household', CreateHousehold),
    ('/addHousehold', AddHousehold),
    ('/updateHousehold', UpdateHousehold)
], debug=True)
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

def account_key(userId):
    return ndb.Key('BankAccounts', userId)

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

def getAllBankAccountsForUser(userId):
    return BankAccounts.query(BankAccounts.userId == userId).fetch()
    
def getBankAccountById(accountId):
    return BankAccounts.query(BankAccounts.accountId == accountId).fetch()
    
def getCcAccountById(ccId):
    return CCAccounts.query(CCAccounts.accountId == ccId).fetch()
    
def getAllCCAccountsForUser(userId):
    return CCAccounts.query(CCAccounts.userId == userId).fetch()
    
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

class BankAccounts(ndb.Model):
    accountId = ndb.IntegerProperty(indexed=True, required=True)
    userId = ndb.IntegerProperty(indexed=True, required=True)
    accountName = ndb.StringProperty(required=True)
    balance = ndb.IntegerProperty()

class CCAccounts(ndb.Model):
    accountId = ndb.IntegerProperty(indexed=True, required=True)
    userId = ndb.IntegerProperty(indexed=True, required=True)
    ccName = ndb.StringProperty(required=True)
    debt = ndb.IntegerProperty()
    limit = ndb.IntegerProperty()
                
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

def deleteOldBankData(userId):
    bankAccount = getAllBankAccountsForUser(int(userId))
    for ba in bankAccount:
        ba.key.delete()

def deleteOldProfileData(userId):
    profile = getProfileInformation(int(userId))
    for p in profile:
        p.key.delete()
        
def deleteOldCcData(userId):
    ccAccount = getAllCCAccountsForUser(int(userId))
    for cc in ccAccount:
        cc.key.delete()
        
class SaveProfile(webapp2.RequestHandler):
    def post(self):
        template = JINJA_ENVIRONMENT.get_template('profile.html')
        error = None
        
        name = self.request.get('name')
        email = self.request.get('email')
        userId = encode(email)
        deleteOldProfileData(int(userId))
        profile = UserProfile(parent=profile_key(int(userId)))
        profile.userId = int(userId)
        profile.name = name
        profile.email = email
        
        #Have to add bank accounts in another table
        bankCount = self.request.get('bankCount')
        bankRecords = self.request.get('bankRecords')
        deleteOldBankData(int(userId))
        if bankRecords == "yes":
            for i in range(0, int(bankCount)):
                bankName = self.request.get('acc'+str(i))
                balance = self.request.get('bal'+str(i))
                accountId = self.request.get('accountId'+str(i))
                
                if bankName:
                    #TODO: Check if the bank name already exists
                    if not balance:
                        balance = "0"
                    if not accountId:
                       bankId = encode(str(uuid.uuid4()))
                    else:
                        bankId = accountId
                        
                    account = BankAccounts(parent=account_key(int(userId)))
                    account.accountId = int(bankId)
                    account.userId = int(userId)
                    account.accountName = bankName
                    account.balance = int(balance)
                    
                    account.put()
                else:
                    logging.info("No bank name ")
                
        #Have to add cc accounts in another table
        ccCount = self.request.get('ccCount')
        ccRecords = self.request.get('ccRecords')
        deleteOldCcData(int(userId))
        if ccRecords == "yes":
            for i in range(0, int(ccCount)):
                ccName = self.request.get('cc'+str(i))
                debt = self.request.get('debt'+str(i))
                limit = self.request.get('limit'+str(i))
                ccAccountId = self.request.get('accountId'+str(i))
                
                if ccName:
                    #TODO: Check if the cc name already exists
                    if not debt:
                        debt = "0"
                    if not limit:
                        limit = "0"
                    if not ccAccountId:
                        ccId = encode(str(uuid.uuid4()))
                    else:
                        ccId = ccAccountId
                        
                        
                    ccAccount = CCAccounts(parent=account_key(int(userId)))
                    ccAccount.accountId = int(ccId)
                    ccAccount.userId = int(userId)
                    ccAccount.ccName = ccName
                    ccAccount.debt = int(debt)
                    ccAccount.limit = int(limit)
                    
                    ccAccount.put()
                else:
                    logging.info("No cc name ") 

                
        profile.put()
        
        time.sleep(3)
        self.redirect('/profile')

def createCcObjectForDisplay(ccAccounts):
    displayObjects = []
    number = 0
    srno = 1
    
    for cc in ccAccounts:
        obj = {
            'number' : number,
            'srno' : srno,
            'accountId' : cc.accountId,
            'ccName' : cc.ccName,
            'debt' : cc.debt,
            'limit' : cc.limit
        }
        displayObjects.append(obj)
        number = number + 1
        srno = srno+1
    
    return displayObjects
    
def createBankObjectForDisplay(bankAccounts):
    displayObjects = []
    number = 0
    srno = 1
    
    for ba in bankAccounts:
        obj = {
            'number' : number,
            'srno' : srno,
            'accountId' : ba.accountId,
            'accountName' : ba.accountName,
            'balance' : ba.balance
        }
        displayObjects.append(obj)
        number = number + 1
        srno = srno+1
    
    return displayObjects
    
class LoadProfile(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        if user:
           url = users.create_logout_url(self.request.uri)
           #Fetch bank account records 
           bankAccounts = getAllBankAccountsForUser(int(encode(user.email())))
           ccAccounts = getAllCCAccountsForUser(int(encode(user.email())))
           profile = getProfileInformation(int(encode(user.email())))
           template_values = {
            'url' : url,
            'user' : user,
            'email' : user.email(),
            'name' : profile[0].name if profile else '',
            'button' : 'SAVE POFILE',
            'action' : 'saveProfile',
            'bankCount': len(bankAccounts) if bankAccounts else '1',
            'ccCount' : len(ccAccounts) if ccAccounts else '1',
            'bankAccounts' : createBankObjectForDisplay(bankAccounts),
            'ccAccounts' : createCcObjectForDisplay(ccAccounts)
            }

           #Load profile details pending
           template = JINJA_ENVIRONMENT.get_template('profile.html')
           self.response.write(template.render(template_values)) 
            
        else:
           self.redirect(users.create_login_url(self.request.uri))

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

def getSummaryofHouseholds(households):
    #logging.info(households)
    summary = []
    for hh in households:
        members = getAllMembersOfHousehold(hh['hId'])
        netSalary = 0
        netDebt = 0
        for m in members:
            if m.salary is not None:
                netSalary = netSalary + m.salary
            if m.debt is not None:    
                netDebt = netDebt + m.debt
        sum = {
            'hhname' : hh['hname'],
            'netSal' : netSalary,
            'netDebt' : netDebt
        }
        summary.append(sum)
    return summary

class AccountInfo(webapp2.RequestHandler):
    def get(self):
        #Checks for active Google session
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            
            template_values = {
            'url' : url,
            'user' : user
            }

            template = JINJA_ENVIRONMENT.get_template('accounts.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))
            
class MainPage(webapp2.RequestHandler):
    def get(self):
        #Checks for active Google session
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            
            template_values = {
            'userPage' : "no",
            'url' : url,
            'user' : user
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))
            
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/accountInfo', AccountInfo),
    ('/profile', LoadProfile),
    ('/saveProfile', SaveProfile),
    ('/updateProfile', UpdateProfile),
    ('/household', CreateHousehold),
    ('/addHousehold', AddHousehold),
    ('/updateHousehold', UpdateHousehold)
], debug=True)
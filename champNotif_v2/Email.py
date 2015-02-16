__author__ = 'StormCrow'

from flask import g
from champNotif_v2 import app
import sqlite3, os, hashlib, smtplib
from database import get_db,query_db

from info import *

from email.mime.text import MIMEText

class Email:

    __email__ = None
    __emailId__ = None

    #helper method to get a token for a given email
    def _getToken(self, email):
        t = (email,)
        result = query_db('SELECT token FROM verification WHERE email=?',t,one=True)
        return result['token']

    def addEmail(self, email, password, salt, isVerified):
        t = (email, password, salt, isVerified)
        g.db.execute('INSERT INTO USERS VALUES (?,?,?,?)', t)
        g.db.commit()
        #newId = cur.lastrowid

        #return newId

    def addVerification(self, email, token):
        db = get_db()
        t = (token,email)
        db.execute('INSERT INTO VERIFICATION SET token=?, timestamp=datetime("now",localtime"),count=0,email=?',t)
        g.db.commit()


    def emailExists(self, email):
        t = (email,)
        result = query_db('SELECT COUNT(email) FROM USERS WHERE email=(?)',t,one=True)
        count = result[0]
        if count > 0:
            return True

        return False

    def makeEmailActive(self,email):
        g.db = get_db()
        t = (email,)
        g.db.execute('UPDATE USERS SET isVerified=1 WHERE email=?',t)
        g.db.commit()

    def genRandomString(self):
        randomBytes = os.urandom(32)
        hash = hashlib.sha512()
        hash.update(randomBytes)
        return hash.hexdigest()

    def securePw(self, salt, pw):
        hash = hashlib.sha512()
        hash.update(salt + pw)
        return hash.hexdigest()



    def genNewToken(self,email):
        g.db = get_db()
        newToken = self.genRandomString()
        token = self._getToken(email)
        t = (newToken,token)
        g.db.execute('UPDATE verification SET token=?, timestamp=datetime("now","localtime") WHERE token=?',t)
        g.db.commit()
        return newToken

    #returns tuple where first element is bool and 2nd is email if bool is true
    def tokenIsActive(self,token):
        t = (token,)
        result = query_db('SELECT COUNT(*),email FROM verification WHERE token=? and datetime("now","localtime") < datetime(timestamp,"+2 day")',t)
        return result


    def sendVerificationEmail(self, email, token):
        notificationEmail = app.config['NOTIFICATIONEMAIL']
        emailPw = app.config['EMAILPW']
        server = app.config['SERVER']
        server = smtplib.SMTP('smtp.gmail.com',587)
        server.starttls()
        server.login(notificationEmail, emailPw)
        #msg = "Click the link to confirm your e-mail \n\n" + server + "/verify?token="+token
        #subject = "email verification"


        #server.sendmail(notificationEmail,email,msg)

        #msg = MIMEText("Click the link to confirm your e-mail \n\n http://www.freechamp.sonyar.info/verify.py?token="+token)
        msg = MIMEText("Click the link to confirm your e-mail \n\n" + server + "/verifyEmail?token="+token)
        msg['To'] = email
        msg['From'] =notificationEmail
        msg['Subject'] = 'email verification'



        try:
            server.sendmail(notificationEmail, email, msg.as_string())
        finally:
            server.quit()


    def verificationFromToday(self, email):
        t = (email,)
        result = query_db("SELECT count(strftime('%Y-%m-%d',timestamp,'localtime')) from verification WHERE strftime(" + \
                          "'%Y-%m-%d',timestamp,'localtime')=strftime('%Y-%m-%d','now','localtime') and email=?",t,one=True)

        count = result[0]
        return count == 1

    def resetVerificationCount(self, email):
        g.db = get_db()
        t = (email,)
        g.db.execute('UPDATE verification SET count=0 WHERE email=?',t)
        g.db.commit()

    def updateVerificationCount(self, email, count):
        g.db = get_db()
        t = (count,email)
        g.db.execute('UPDATE verification SET count=? WHERE email=?',t)
        g.db.commit()

    def getCount(self, email):
        t = (email,)
        result = query_db('SELECT count FROM verification WHERE email=?',t,one=True)
        return result[0]

    #returns true if send limit has not been exceeded for a given email
    def checkSendLimit(self, email):
        emailLib = Email()
        if emailLib.emailExists(email):
        #does the email have a timestamp of today?
            today = self.verificationFromToday(email)
            if today:
                count = self.getCount(email)
                if count == 0:
                    self.updateVerificationCount(email,1)
                    return True
                elif count == 1:
                    self.updateVerificationCount(email,2)
                    return True
                else:
                    return False
        else:
            return False











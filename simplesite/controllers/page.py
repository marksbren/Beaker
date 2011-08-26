import logging
import simplesite.lib.helpers as h
import string
import datetime
from sqlalchemy.sql import and_, or_, not_
import time

# For MicroController
import serial

# For Twilio
import twilio
API_VERSION = '2008-08-01'
# Twilio AccountSid and AuthToken
ACCOUNT_SID = 'AC179a9a10e2e8560d1c803bb2cf47555e'
ACCOUNT_TOKEN = 'dc806c7d02fe70db0cc98fd13b2b2c60'
# Create a Twilio REST account object using your Twilio account ID and token
account = twilio.Account(ACCOUNT_SID,ACCOUNT_TOKEN)
CALLER_ID = '4152362962'

# For the db stuff
import simplesite.model as model
import simplesite.model.meta as meta

# For Forms
import formencode
from formencode import htmlfill
from pylons.decorators import validate
from pylons.decorators.rest import restrict

# For Authentication
from authkit.authorize.pylons_adaptors import authorize
from authkit.permissions import RemoteUser, ValidAuthKitUser, UserIn

# Default
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from simplesite.lib.base import BaseController, render

log = logging.getLogger(__name__)

#Insert a new line in the event_log
def Insert_Event_Log(User_Id1, Event1, Query1):
	#Add the new pag to the database
	event_log = model.Event_log()
	event_log.user_id = User_Id1
	event_log.event = Event1
	event_log.query = Query1
	event_log.timestamp = datetime.datetime.now()
	meta.Session.add(event_log)
	meta.Session.commit()

#Insert a checkin to the feed
def Add_Checkin(Firstname,Number):
	#Add a new checkin
	checkin_feed = model.Checkin_feed()
	checkin_feed.firstname = Firstname
	checkin_feed.number = Number
	checkin_feed.timestamp = datetime.datetime.now()
	meta.Session.add(checkin_feed)
	meta.Session.commit()
	
#The SMS Send function
def SMS_Send(TO, CALLER_ID, BODY):
	#Initiate a new SMS
	d = {
		'To' : TO,
		'From' : CALLER_ID,
		'Body' : BODY #What should this be?
		}
	account.request('/%s/Accounts/%s/SMS/Messages' % (API_VERSION, ACCOUNT_SID), 'POST', d)

#Open the door!
def send_open_signal():	
	ser = serial.Serial('/dev/ttyACM0',2400)
	time.sleep(1)
	ser.write('O')
	time.sleep(1)
	ser.flushInput()
	time.sleep(1)
	ser.flushOutput()
	time.sleep(5)
	ser.close()


class WhitelistForm(formencode.Schema):
	allow_extra_fields = True
	filter_extra_fields = True
	firstname = formencode.validators.String(not_empty=True)
	lastname = formencode.validators.String(not_empty=True)
	response = formencode.validators.String(not_empty=True)
	number = formencode.validators.String(not_empty=True)
	filename = formencode.validators.String()

class PasscodeForm(formencode.Schema):
	allow_extra_fields = True
	filter_extra_fields = True
	passcode = formencode.validators.String(not_empty=True)

class ViewForm(formencode.Schema):
	allow_extra_fields = True
	filter_extra_fields = True
	response = formencode.validators.String(not_empty=True)

class PageController(BaseController):

	#TODO: restrict to Twilio user-agent using HTTP_USER_AGENT
	#@restrict('POST')
	def twilio(self):
		#Get the information in the text
		BODY = request.params['Body']
		INCOMING = request.params['From']

		page_q = meta.Session.query(model.Whitelist1)
		whitelist = page_q.filter_by(number=INCOMING).first()

		# passcodes only last for 12 hours and must be saved in lowercase
		passcodes_q = meta.Session.query(model.Passcodes)
		expire_time = datetime.datetime.now()-datetime.timedelta(hours=12)
		code_sent = string.lower(BODY)
		psscd = passcodes_q.filter_by(passcode=code_sent).first()

		# if the texter is not on the whitelist
		if whitelist is None:
			# if the body is not the passcode
			if psscd is None:
				SMS_Send('5038300523', CALLER_ID, 'Master Mark, %s would like to enter.' % INCOMING)
				SMS_Send(INCOMING, CALLER_ID, 'Terribly sorry, but I do not see your name in the guestlist and did not get the right passcode. I have contacted Mark.')
				Insert_Event_Log(-1, '/whitelist/block', 'number=%s&raw=%s' % (INCOMING,BODY))
			# sent the passcode (TODO: ask for name)
			else:
				SMS_Send(INCOMING, CALLER_ID, 'Welcome to Basecamp! Now recuperate & get back out there!')
				Insert_Event_Log(-1, '/passcode/entry', 'number=%s&raw=%s' % (INCOMING,BODY))
				send_open_signal()
				Add_Checkin("Guest","5555555555")

		# The texter is recognized
		else:
			# If they checkin within 20 minutes they don't get points
			checkin_q = meta.Session.query(model.Checkin_feed)
			twenty_minutes_ago = datetime.datetime.now()-datetime.timedelta(minutes=20)
			last_checkin = checkin_q.filter_by(number=whitelist.number).order_by(model.Checkin_feed.timestamp.desc()).first()

			if last_checkin.timestamp < twenty_minutes_ago:
				#if the checkin was okay, add it to the feed
				Add_Checkin(whitelist.firstname,whitelist.number)
				if whitelist.count is None:
					whitelist.count = 1
				else:
					whitelist.count = whitelist.count + 1
				meta.Session.update(whitelist)
				meta.Session.commit()
				SMS_Send(INCOMING ,CALLER_ID, whitelist.response)
			else:
				#send the open signal, but reluctantly
				SMS_Send(INCOMING ,CALLER_ID, "Hmmm... you seem to be coming offen... I'll let you in, but you're not getting credit!")
			send_open_signal()	
			Insert_Event_Log(whitelist.id, '/whitelist/entry', 'number=%s' % INCOMING)


	@authorize(ValidAuthKitUser())
	def home(self):
		c.passcode_entries = meta.Session.query(model.Passcodes).all()
		c.event_log_entries = meta.Session.query(model.Event_log).order_by(model.Event_log.timestamp.desc())[0:20]
		return render('/derived/page/home.html')

	@authorize(ValidAuthKitUser())
	def view(self, id):
		if id is None:
			abort(404)
		page_q = model.meta.Session.query(model.Whitelist1)
		c.whitelist= page_q.get(int(id))
		if c.whitelist is None:
			abort(404)
		return render('/derived/page/view.html')
	
	@authorize(ValidAuthKitUser())
	def display(self):
		c.checkins = meta.Session.query(model.Checkin_feed).order_by(model.Checkin_feed.timestamp.desc())[0:7]
		return render('/derived/page/display.html')
	
	@authorize(ValidAuthKitUser())
	def new(self):
		return render('/derived/page/new.html')

	@authorize(ValidAuthKitUser())
	@restrict('POST')
	@validate(schema=WhitelistForm(), form='new')
	def create(self):
		#Add the new pag to the database
		whitelist = model.Whitelist1()
		for k, v in self.form_result.items():
			setattr(whitelist, k, v)
		whitelist.count = 0
		meta.Session.add(whitelist)
		meta.Session.commit()
		# issue HTTP redirect
		response.status_int = 302
		response.headers['location'] = h.url(controller='page',
			action='view', id=whitelist.id)
		return "Moved temporarily"
	
	@authorize(ValidAuthKitUser())
	@restrict('POST')
	@validate(schema=PasscodeForm(), form='new')
	def create_passcode(self):
		#Add the new pag to the database
		passcodes = model.Passcodes()
		for k, v in self.form_result.items():
			setattr(passcodes, k, v)
		meta.Session.add(passcodes)
		meta.Session.commit()
		# issue HTTP redirect
		response.status_int = 302
		response.headers['location'] = h.url(controller='page',
			action='home')
		return "Moved temporarily"

	@authorize(ValidAuthKitUser())
	def edit(self, id=None):
		if id is None:
			abort(404)
		page_q = meta.Session.query(model.Whitelist1)
		whitelist = page_q.filter_by(id=id).first()
		if whitelist is None:
			abort(404)
		values = {
			'firstname' : whitelist.firstname,
			'lastname' : whitelist.lastname,
			'response' : whitelist.response,
			'number' : whitelist.number,
			'filename' : whitelist.filename
		}
		c.name = whitelist.name
		return htmlfill.render(render('/derived/page/edit.html'), values)
	
	@restrict('POST')
	@authorize(ValidAuthKitUser())
	@validate(schema=WhitelistForm(), form='edit')
	def save(self, id=None):
		page_q = meta.Session.query(model.Whitelist1)
		whitelist = page_q.filter_by(id=id).first()
		if whitelist is None:
			abort(404)
		for k,v in self.form_result.items():
			if getattr(whitelist, k) != v:
				setattr(whitelist, k, v)
		meta.Session.commit()
		# issue HTTP redirect
		response.status_int = 302
		response.headers['location'] = h.url(controller='page',
			action='view', id=whitelist.id)
		return "Moved temporarily"

	@authorize(ValidAuthKitUser())
	def list(self):
		c.whitelist_entries = meta.Session.query(model.Whitelist1).all()
		return render('/derived/page/list.html')

	@authorize(ValidAuthKitUser())
	def delete(self, id=None):
		if id is None:
			abort(404)
		page_q = meta.Session.query(model.Whitelist1)
		whitelist = page_q.filter_by(id=id).first()
		if whitelist is None:
			abort(404)
		meta.Session.delete(whitelist)
		meta.Session.commit()
		return render('/derived/page/deleted.html')
	
	@authorize(ValidAuthKitUser())
	def delete_passcode(self, id=None):
		if id is None:
			abort(404)
		passcode = meta.Session.query(model.Passcodes)
		psscd = passcode.filter_by(id=id).first()
		if psscd is None:
			abort(404)
		meta.Session.delete(psscd)
		meta.Session.commit()
		# issue HTTP redirect
		response.status_int = 302
		response.headers['location'] = h.url(controller='page',
			action='home')
		return "Moved temporarily"
	

	@restrict('POST')
	@authorize(ValidAuthKitUser())
	@validate(schema=ViewForm(), form='edit')
	def edit_response(self, id=None):
		if id is None:
			abort(404)
		whitelist_q = meta.Session.query(model.Whitelist1)
		whitelist = whitelist_q.filter_by(id=id).first()
		if whitelist is None:
			abort(404)
		for k, v in self.form_result.items():
			setattr(whitelist, k, v)
		meta.Session.update(whitelist)
		meta.Session.commit()
		# issue HTTP redirect
		response.status_int = 302
		response.headers['location'] = h.url(controller='page',
			action='view', id=whitelist.id)
		return "Moved"

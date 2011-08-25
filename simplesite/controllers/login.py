import logging
import simplesite.lib.helpers as h
from pylons.decorators.rest import restrict

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from simplesite.lib.base import BaseController, render

log = logging.getLogger(__name__)

class LoginController(BaseController):
	
	def login(self):
		if request.environ.get("REMOTE_USER"):
			return "You are authenticated!"
		else:
			response.status = "401 Not Authenticated"
			return "You are not authenicated"
	
	def logout(self):
		return "Successfully signed out!"

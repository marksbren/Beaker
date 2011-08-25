"""Setup the SimpleSite application"""
import logging
from simplesite import model
import pylons.test

from simplesite.config.environment import load_environment
from simplesite.model.meta import Session, Base, engine

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
	"""Place any commands to setup simplesite here"""
	# Don't reload the app if it was loaded under the testing environment
	if not pylons.test.pylonsapp:
		load_environment(conf.global_conf, conf.local_conf)
	
	#Load the models
	from simplesite.model import meta
	meta.metadata.bind = meta.engine

	# Create the tables if they don't already exist
	meta.metadata.create_all(bind=Session.bind)

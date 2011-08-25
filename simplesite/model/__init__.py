"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm

from simplesite.model import meta

import datetime
from sqlalchemy import schema, types
#from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

def init_model(engine):
	"""Call me before using any of the tables or classes in the model"""
	## Reflected tables must be defined and mapped here
	#global reflected_table
	#reflected_table = sa.table("Reflected", meta.metadata, autoload=True,
	#							autoload_with=engine)
	#orm.mapper(Reflected, reflected_table)

	#We are using SQLALchemy 0.5 so transactional=Ture is replaced by
	#autocommit=False
	sm= orm.sessionmaker(autoflush=True, autocommit=False, bind=engine)

	meta.engine = engine
	meta.Session = orm.scoped_session(sm)

# Replace the rest of the file with the model objects we creates in chapter 7

def now():
	return datetime.datetime.now()

whitelist_table1 = schema.Table('whitelist1', meta.metadata,
	schema.Column('id', types.Integer,
		schema.Sequence('whitelist_seq_id', optional=True), primary_key=True),
	schema.Column('firstname', types.Unicode(255), nullable=False),
	schema.Column('lastname', types.Unicode(255), nullable=False),
	schema.Column('created', types.DateTime(), default=now),
	schema.Column('response', types.Unicode(255), nullable=False),
	schema.Column('number', types.Unicode(255), nullable=False),
	schema.Column('count', types.Integer, nullable=False),
	schema.Column('filename', types.Unicode(255), default=u'Untitled Page'))

passcodes_table = schema.Table('passcodes', meta.metadata,
	schema.Column('id', types.Integer,
		schema.Sequence('passcodes_seq_id', optional=True), primary_key=True),
	schema.Column('passcode', types.Unicode(255), nullable=False),
	schema.Column('created', types.DateTime(), default=now))

event_log_table = schema.Table('event_log', meta.metadata,
	schema.Column('id', types.Integer,
		schema.Sequence('event_log_seq_id', optional=True), primary_key=True),
	schema.Column('user_id', types.Integer, nullable=False),
	schema.Column('event', types.Unicode(255), nullable=False),
	schema.Column('query', types.Unicode(255), nullable=False),
	schema.Column('timestamp', types.DateTime(), default=now())
)

checkin_feed_table = schema.Table('checkin_feed', meta.metadata,
	schema.Column('id', types.Integer,
		schema.Sequence('checkin_seq_id', optional=True), primary_key=True),
	schema.Column('firstname', types.Unicode(255), nullable=False),
	schema.Column('number', types.Unicode(255), default="+15555555555"),
	schema.Column('timestamp', types.DateTime(), default=now())
)

class Whitelist1(object):
	pass

class Passcodes(object):
	pass

class Event_log(object):
	pass

class Checkin_feed(object):
	pass

orm.mapper(Event_log, event_log_table)
orm.mapper(Whitelist1, whitelist_table1)
orm.mapper(Passcodes, passcodes_table)
orm.mapper(Checkin_feed, checkin_feed_table)

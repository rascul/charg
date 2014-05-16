from flask import g
from flask.ext.login import UserMixin

class User(UserMixin):
	"""
	User class to hold the user's information
	"""
	
	def __init__(self, **kwargs):
		self.uid = kwargs.get('uid')
		self.email = kwargs.get('email')
	
	def get_id(self):
		return self.uid

def load_user(uid):
	"""
	Load a user from the database given the id
	"""
	user = User()
	
	cur = g.db.cursor()
	cur.execute('select uid, email from users where uid = %s', (uid,))
	
	if cur.rowcount is 1:
		row = cur.fetchone()
		user.uid = row[0]
		user.email = row[1]
	else:
		user = None
	
	return user

def get_user(kwargs):
	"""
	Search the database for a user, if not found then create one
	"""
	
	user = User()
	uid = kwargs.get('uid')
	email = kwargs.get('email')
	
	cur = g.db.cursor()
	cur.execute('select uid, email from users where email = %s', (email,))
	
	if cur.rowcount == 1:
		row = cur.fetchone()
		user.uid = row[0]
		user.email = row[1]
	elif cur.rowcount == 0 and kwargs.get('status') == 'okay':
		user.uid = uid
		user.email = email
		user = create_user(user)
	else:
		user = None
	
	return user

def create_user(user):
	"""
	Insert a user into the database
	"""
	
	cur = g.db.cursor()
	
	try:
		cur.execute('insert into users (email) values (%s)', (user.email,))
		g.db.commit()
	except:
		user = None
	
	return user

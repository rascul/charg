from os import environ

import psycopg2
import psycopg2.extras

from flask import Flask, g, render_template, request, url_for, redirect
from flask.ext.login import LoginManager, current_user, login_required
from flask.ext.browserid import BrowserID
from flask.ext.mail import Mail, Message

from charg import app

from user import User, load_user, get_user
from lib import validate_form, send_mail, interval

login_manager = LoginManager()
login_manager.user_loader(load_user)
login_manager.init_app(app)

browser_id = BrowserID()
browser_id.user_loader(get_user)
browser_id.init_app(app)

mail = Mail(app)

def connect_db():
	return psycopg2.connect(app.config.get("DATABASE"))

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(error):
	db = getattr(g, 'db', None)
	if db is not None:
		g.db.close()

@app.route("/")
def index():
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select sex, charid, hitpoints, moves, level, race, char_class, homeland, stat_str, stat_int, stat_wil, stat_dex, stat_con, date_trunc(%s, age(expires, current_timestamp)) as expires from chars where released is null and (expires > current_timestamp or expires is null) order by created desc', ('seconds',))
	chars = cur.fetchall()
	return render_template("index.html", chars=chars)

@app.route("/add")
@login_required
def add():
	return render_template("add.html")

@app.route("/add", methods=['POST'])
@login_required
def add_char():
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	
	check, values = validate_form(current_user, request)
	if check:
		try:
			# hopefully i remember to update this if values index changes
			if values[17]:
				cur.execute('insert into chars (name, password, creator, moves, hitpoints, level, race, char_class, homeland, stat_str, stat_int, stat_wil, stat_dex, stat_con, notes, rent, sex, expires) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, current_timestamp + interval %s) returning charid', (values))
			else:
				cur.execute('insert into chars (name, password, creator, moves, hitpoints, level, race, char_class, homeland, stat_str, stat_int, stat_wil, stat_dex, stat_con, notes, rent, sex, expires) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning charid', (values))
			charid = cur.fetchone().charid
			g.db.commit()
			return redirect(url_for('admin_view_char', charid=charid))
		except:
			return render_template("fail.html", message="Unable to insert record.")
	else:
		return render_template("fail.html", message=values)

@app.route("/char/<charid>")
def view_char(charid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select sex, hitpoints, moves, level, race, char_class, homeland, stat_str, stat_int, stat_wil, stat_dex, stat_con, notes, rent from chars where charid = %s',
		(charid,))
	if cur.rowcount == 1:
		char = cur.fetchone()
		return render_template("char.html", char=char, charid=charid)
	else:
		return render_template("fail.html", message="That character does not exist.")

@app.route("/admin")
@login_required
def admin():
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select charid, name, hitpoints, moves, sex, race, char_class, homeland, level, stat_str, stat_int, stat_wil, stat_dex, stat_con, date_trunc(%s, age(expires, current_timestamp)) as expires from chars where creator = %s and released is null', ("seconds", current_user.uid,))
	current_chars = cur.fetchall()
	cur.execute('select charid, name, hitpoints, moves, sex, race, char_class, homeland, level, stat_str, stat_int, stat_wil, stat_dex, stat_con from chars where creator = %s and released is not null', (current_user.uid,))
	released_chars = cur.fetchall()
	return render_template("admin.html", current_chars=current_chars, released_chars=released_chars)

@app.route("/admin/char/<charid>")
@login_required
def admin_view_char(charid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	
	cur.execute('select creator from chars where charid = %s', (charid,))
	if cur.rowcount == 1:
		creator = cur.fetchone().creator
		if current_user.uid == creator:
			cur.execute('select name, charid, password, sex, hitpoints, moves, level, race, char_class, homeland, stat_str, stat_int, stat_wil, stat_dex, stat_con, notes, rent, date_trunc(%s, age(expires, current_timestamp)) as expires from chars where charid = %s',
				("seconds", charid,))
			char = cur.fetchone()
			cur.execute('select requestid, name from requests where charid = %s', (charid,))
			requests = cur.fetchall()
			return render_template("admin_char.html", char=char, requests=requests)
		else:
			return render_template("fail.html", message="This is not your character.")
	else:
		return render_template("fail.html", message="That character does not exist.")

@app.route("/admin/edit/<charid>")
@login_required
def admin_edit_char(charid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	
	cur.execute('select creator from chars where charid = %s', (charid,))
	if cur.rowcount == 1:
		creator = cur.fetchone().creator
		if current_user.uid == creator:
			cur.execute('select name, charid, password, sex, hitpoints, moves, level, race, char_class, homeland, stat_str, stat_int, stat_wil, stat_dex, stat_con, notes, rent from chars where charid = %s',
				(charid,))
			char = cur.fetchone()
			return render_template("admin_edit.html", char=char)
		else:
			return render_template("fail.html", message="This is not your character.")
	else:
		return render_template("fail.html", message="That character does not exist.")

@app.route("/admin/edit/<charid>", methods=['POST'])
@login_required
def admin_edit_post(charid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	
	cur.execute('select creator, level from chars where charid = %s', (charid,))
	if cur.rowcount == 1:
		row = cur.fetchone()
		creator = row.creator
		level = row.level		
		if current_user.uid == creator:
			check, values = validate_form(current_user, request, charid)
			if check:
				try:
					# change this if values changes index!
					if level != values[4]:
						expires = interval(values[4])
						if expires == False:
							return render_template("fail.html", message="Invalid level.")
						elif expires == None:
							cur.execute('update chars set expires = null where charid = %s', (charid,))
							g.db.commit()
						else:
							cur.execute('update chars set expires = current_timestamp + interval %s where charid = %s', (expires, charid))
							g.db.commit()
					cur.execute('update chars set name = %s, password = %s, moves = %s, hitpoints = %s, level = %s, race = %s, char_class = %s, homeland = %s, stat_str = %s, stat_int = %s, stat_wil = %s, stat_dex = %s, stat_con = %s, notes = %s, rent = %s, sex = %s where charid = %s', (values))
					g.db.commit()
					
					return redirect(url_for('admin_view_char', charid=charid))
				except:
					return render_template("fail.html", message="Unable to update record.")
			else:
				return render_template("fail.html", message=values)
		else:
			return render_template("fail.html", message="This is not your character.")
	else:
		return render_template("fail.html", message="That character does not exist.")

@app.route("/admin/renew/<charid>")
@login_required
def admin_renew_char(charid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select creator, level from chars where charid = %s', (charid,))
	if cur.rowcount == 1:
		row = cur.fetchone()
		if current_user.uid == row.creator:
			expires = interval(row.level)
			if expires == False:
				return render_template("fail.html", message="Couldn't renew character.")
			elif expires == None:
				cur.execute('update chars set expires = null where charid = %s', (charid,))
				g.db.commit()
			else:
				cur.execute('update chars set expires = current_timestamp + interval %s where charid = %s', (expires, charid))
				g.db.commit()
			#return render_template("success.html")
			return redirect(request.referrer or url_for('admin'))
		else:
			return render_template("fail.html", message="This is not your character.")
	else:
		return render_template("fail.html", message="That character does not exist.")

@app.route("/admin/delete/<charid>")
@login_required
def admin_delete_char(charid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select creator from chars where charid = %s', (charid,))
	if cur.rowcount == 1:
		creator = cur.fetchone().creator
		if current_user.uid == creator:
			cur.execute('delete from chars where charid = %s', (charid,))
			g.db.commit()
			return redirect(url_for('admin'))
		else:
			return render_template("fail.html", message="This is not your character.")
	else:
		return render_template("fail.html", message="That character does not exist.")

@app.route("/request/<charid>", methods=["POST"])
def request_char(charid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	
	# check if charid exists
	cur.execute('select charid from chars where charid = %s', (charid,))
	if cur.rowcount != 1:
		return render_template("fail.html", message="Invalid character.")
	
	request_name = request.form.get("name")
	request_email = request.form.get("email")
	
	# verify we got both name and email, maybe at a later point verify
	# that the email address is valid
	if not request_name:
		return render_template("fail.html", message="You must enter a name.")
	if not request_email:
		return render_template("fail.html", message="You must enter a email address.")
	
	cur.execute('insert into requests (charid, name, email) values (%s, %s, %s) returning requestid', (charid, request_name, request_email))
	requestid = cur.fetchone().requestid
	if requestid:
		g.db.commit()
		
		email = ""
		
		cur.execute('select users.email from users, chars where chars.charid = %s and chars.creator = users.uid', (charid,))
		email = cur.fetchone().email
		
		if email:
			body = app.config.get("REQUEST_MESSAGE") % charid
			
			if send_mail(mail, app.config.get("MAIL_SENDER_ADDRESS"), email, app.config.get("REQUEST_SUBJECT"), body):
				return render_template("success.html")
			else:
				return render_template("fail.html", message="Could not send email.")			
		else:
			return render_template("fail.html", message="Could not get email address from database.")
	else:
		return render_template("fail.html", message="Could not insert request into database.")


@app.route("/requests")
@login_required
def requests():
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select requests.requestid, requests.name as request_name, chars.charid, chars.name as char_name from requests, chars, users where requests.charid = chars.charid and chars.creator = users.uid and users.uid = %s', (current_user.uid,))
	requests = cur.fetchall()
	return render_template("requests.html", requests=requests)

@app.route("/requests/delete/<requestid>")
@login_required
def request_delete(requestid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select chars.creator from chars, requests where requests.charid = chars.charid and requests.requestid = %s', (requestid,))
	if cur.rowcount == 1:
		uid = cur.fetchone().creator
		if current_user.uid == uid:
			cur.execute('delete from requests where requestid = %s', (requestid,))
			g.db.commit()
			return redirect(url_for("requests"))
		else:
			return render_template("fail.html", message="This is not your character.")
	else:
		return render_template("fail.html", message="That character does not exist.")

@app.route("/requests/release/<requestid>")
@login_required
def request_release(requestid):
	cur = g.db.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
	cur.execute('select * from requests where requestid = %s', (requestid,))
	
	if cur.rowcount == 1:
		request = cur.fetchone()
		cur.execute('select * from chars where charid = %s', (request.charid,))
		
		if cur.rowcount == 1:
			char = cur.fetchone()
			
			if current_user.uid == char.creator:
				cur.execute('delete from requests where charid = %s', (request.charid,))
				cur.execute('update chars set owner = %s, released = current_timestamp where charid = %s', (request.name, char.charid))
				g.db.commit()
				
				body = app.config.get("RELEASE_MESSAGE") % (
					char.name,
					char.password,
					char.sex,
					char.race,
					char.char_class,
					char.homeland,
					char.level,
					char.hitpoints,
					char.moves,
					char.stat_str,
					char.stat_int,
					char.stat_wil,
					char.stat_dex,
					char.stat_con,
					char.stat_str + char.stat_int + char.stat_wil + char.stat_dex + char.stat_con,
					char.rent,
					char.notes
				)
				
				if send_mail(mail, app.config.get("MAIL_SENDER_ADDRESS"), request.email, app.config.get("RELEASE_SUBJECT"), body):
					return redirect(url_for("requests"))
				else:
					return render_template("fail.html", message="Could not send email.")
			else:
				return render_template("fail.html", message="This is not your character.")
		else:
			return render_template("fail.html", message="That character does not exist.")
	else:
		return render_template("fail.html", message="That request does not exist.")

@app.route("/help")
def help():
	return render_template("help.html", email=app.config.get('MAIL_SENDER_ADDRESS'))

if __name__ == "__main__":
	app.run()


from flask.ext.mail import Message

human_classes = (
	"channeler", 
	"hunter", 
	"rogue", 
	"warrior"
)
seanchan_classes = (
	"hunter", 
	"rogue", 
	"warrior"
)
trolloc_classes = (
	"hunter", 
	"rogue", 
	"warrior"
)
human_homelands = (
	"altara", 
	"amadicia", 
	"andor", 
	"arad doman", 
	"arafel", 
	"borderlands", 
	"cairhien", 
	"ghealdan", 
	"illian", 
	"kandor", 
	"mayene", 
	"murandy", 
	"saldaea", 
	"shienar", 
	"tarabon", 
	"tear", 
	"two rivers"
)
seanchan_homelands = (
	"seandar", 
	"kirendad", 
	"shon kifar", 
	"rampore", 
	"tzura", 
	"noren m'shar"
)
trolloc_homelands = (
	"beaked", 
	"bearish", 
	"boarheaded", 
	"ramshorned", 
	"wolfish"
)

def num(s):
	try:
		if int(s) > 0:
			return int(s)
	except:
		return False

def interval(level):
	if level == 1:
		return "3 days"
	elif 2 <= level <= 4:
		return "7 days"
	elif 5 <= level <= 9:
		return "1 month"
	elif 10 <= level <= 19:
		return "3 months"
	elif 20 <= level <= 29:
		return "6 months"
	elif 30 <= level <= 51:
		return None
	else:
		return False

def validate_form(current_user, request, charid=None):
	name = request.form.get("name")
	if not name:
		return False, "You must enter the name."
	
	password = request.form.get("password")
	if not password:
		return False, "You must enter the password."
	
	mv = num(request.form.get("mv"))
	if not mv:
		return False, "You must enter the movement points."
	
	hp = num(request.form.get("hp"))
	if not hp:
		return False, "You must enter the hitpoints."
	
	level = int(request.form.get("level"))
	expires = interval(level)
	
	if expires == False:
		return False, "You must specify the level."
	
	race = request.form.get("race").lower()
	char_class = ""
	homeland = ""
	if race == "human":
		char_class = request.form.get("human-class").lower()
		homeland = request.form.get("human-homeland").lower()
		if not char_class in human_classes:
			return False, "Invalid class selection."
		if not homeland in human_homelands:
			return False, "Invalid homeland selection."
	elif race == "seanchan":
		char_class = request.form.get("seanchan-class").lower()
		homeland = request.form.get("seanchan-homeland").lower()
		if not char_class in seanchan_classes:
			return False, "Invalid class selection."
		if not homeland in seanchan_homelands:
			return False, "Invalid homeland selection."
	elif race == "trolloc":
		char_class = request.form.get("trolloc-class").lower()
		homeland = request.form.get("trolloc-homeland").lower()
		if not char_class in trolloc_classes:
			return False, "Invalid class selection."
		if not homeland in trolloc_homelands:
			return False, "Invalid homeland selection."
	else:
		return False, "You must choose a valid race."
	
	stat_str = num(request.form.get("str"))
	stat_int = num(request.form.get("int"))
	stat_wil = num(request.form.get("wil"))
	stat_dex = num(request.form.get("dex"))
	stat_con = num(request.form.get("con"))
	
	if not stat_str or stat_str > 21 or stat_str < 5 or (race == "human" and stat_str > 19):
		return False, "Invalid data for strength."
	if not stat_int or stat_int > 19 or stat_int < 3:
		return False, "Invalid data for intelligence."
	if not stat_wil or stat_wil > 19 or stat_wil < 3:
		return False, "Invalid data for wisdom."
	if not stat_dex or stat_dex > 19 or stat_dex < 5:
		return False, "Invalid data for constitution."
	if not stat_con or stat_con > 19 or stat_con < 5:
		return False, "Invalid data for dexterity."
	
	sex = request.form.get("sex")
	if not sex:
		return False, "You must specify the sex."
	elif not sex in ("guy", "gal"):
		return False, "Invalid sex."
	
	values = ()
	if charid:
		# /admin/edit
		values = (
			name,
			password,
			mv,
			hp,
			level,
			race,
			char_class,
			homeland,
			stat_str,
			stat_int,
			stat_wil,
			stat_dex,
			stat_con,
			request.form.get("notes"),
			request.form.get("rented"),
			sex,
			charid
		)
	else:
		# /add
		values = (
			name,
			password,
			current_user.uid,
			mv,
			hp,
			level,
			race,
			char_class,
			homeland,
			stat_str,
			stat_int,
			stat_wil,
			stat_dex,
			stat_con,
			request.form.get("notes"),
			request.form.get("rented"),
			sex,
			expires
		)
	
	return True, values

def send_mail(mail, sender, recipient, subject, body):
	try:
		msg = Message(
			subject,
			sender=sender,
			recipients=[recipient],
			body=body
		)
		mail.send(msg)
		return True
	except:
		return False

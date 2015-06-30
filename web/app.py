import os
import csv
import datetime
import json
from peewee import *
from flask import Flask
from flask import render_template, flash, redirect, url_for, session, request, jsonify
from flask.ext.admin import Admin, BaseView
from flask.ext.admin.contrib.peewee import ModelView
from playhouse.csv_utils import load_csv
from playhouse.shortcuts import model_to_dict
from flask.ext.login import LoginManager, login_user , logout_user , current_user , login_required
from flask_wtf import Form

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456790'

#################
# Data         #
#################

# Load address data from CSV 
#csv_path = './static/combined_addresses.csv'
#csv_obj = csv.DictReader(open(csv_path, 'rU'))
#csv_list = list(csv_obj)
# http://stackoverflow.com/questions/1747817/python-create-a-dictionary-with-list-comprehension
#csv_dict = dict([[o['id'], o] for o in csv_list])

#################
# Database      #
#################

host = os.environ['DB_PORT_5432_TCP_ADDR']
user = 'postgres'
database = 'postgres'

#Set up peewee 
db = PostgresqlDatabase(database, user=user, host=host)


#################
# Models        #
#################


class BaseModel(Model):
	"""Base model that will use the postgresql database"""
	class Meta: 
		database = db


class Contact(BaseModel):
	"""Contacts table and class for KIPPster, Alumni, and Postcard contacts"""
	id = PrimaryKeyField(unique = True)
	first_name = CharField()
	last_name = CharField()
	grade = CharField()
	address = CharField()
	lat = FloatField()
	long = FloatField()
	type = CharField()
	cohort = CharField()
	community_area = CharField()
	recruiting_zone = CharField()

	def __unicode__(self):
		return  '%s, %s: %s' % (self.last_name, self.first_name, self.address)


class User(BaseModel):
	"""User table and class"""
	userid = PrimaryKeyField(unique = True)
	username = CharField(unique = True)
	password = CharField()
	join_date = DateTimeField(default = datetime.datetime.now)
	active = BooleanField(default = True)
	admin = BooleanField(default = False)

	class Meta:
		order_by = ('username',)

	def __unicode__(self):
		return self.username

	def is_active(self):
		"""True, as all users are active."""
		return True

	def get_id(self):
		"""Return the email address to satisfy Flask-Login's requirements."""
		return unicode(self.userid)

	def is_authenticated(self):
		"""Return True if the user is authenticated."""
		return True

	def is_active(self):
		"""Return True if the user is authenticated."""
		return self.active

	def is_anonymous(self):
		"""False, as anonymous users aren't supported."""
		return False

	def is_admin(self):
		return self.admin

class Comment(BaseModel):
	"""Comment for contacts from users"""
	user = ForeignKeyField(User, related_name='comments')
	contact = ForeignKeyField(Contact, related_name='contacts')
	comment = CharField()
	timestamp = DateTimeField(default = datetime.datetime.now)

	class Meta:
		order_by = ('timestamp', 'user',)

	@classmethod
	def show(user):
			return (Comment
					.select()
					.where(Comment.user == user)
					.order_by(Comment.timestamp.desc()))

class RecruitingZone(BaseModel):
	"""Recruiting Zone list"""
	id = PrimaryKeyField(unique = True)
	recruiting_zone = CharField(unique = True)

	def __unicode__(self):
		return self.recruiting_zone 

class UserRZ(BaseModel):
	id = PrimaryKeyField(unique = True)
	recruiting_zone = ForeignKeyField(RecruitingZone)
	user = ForeignKeyField(User)

	class Meta:
		def __unicode__(self):
			return self.recruiting_zone





def create_tables():
	"""Create tables in postgresql db from model and import contact adresses"""
	db.connect()
	
	try:
		db.create_tables([Contact, User, Comment, RecruitingZone, UserRZ])
	except: pass

	# populate contact table
	try:
	    csv_path = '../data/combined_addresses.csv'
	    csv_obj = csv.DictReader(open(csv_path, 'rU'))
	    Contact.insert_many(csv_obj).execute()
	except: pass

	# set up basic admin user
	try:
		admin_user = User.create(
								username = "admin",
								password = "admin",
								active = True,
								admin = True)
	except: pass

	# get dis(ticnt recruiting_zones from Contact and insurt into RecruitngZone table
	try:
		rz_qry = (RecruitingZone
			 	.insert_from(
			 		fields=[RecruitingZone.recruiting_zone],
			 		query = Contact.select(Contact.recruiting_zone).distinct().order_by(Contact.recruiting_zone))
				.execute())
	except: pass

all_contacts = Contact.select()

# Need to add my_contacts for logged in user

############
# App     ##
############
@app.route("/")
@login_required
def index():
    return render_template('index.html', 
           object_list=all_contacts
)


############
# Admin   ##
############

class MyModelView(ModelView):
	"""Extends ModelView to use Flask-Login"""
	def is_accessible(self):
		if not current_user.is_active() or not current_user.is_authenticated():
			return False

		if current_user.is_admin():
			return True

		return False

	def _handle_view(self, name, **kwargs):
		""" Overide built-in _handl_view to redirect users when view not accessible"""
		if not self.is_accessible():
			if current_user.is_authenticated():
			# permission denied
				abort(403)
			else:
				# login
				return redirect(url_for('login', next=request.url))



#def CommentsAdmin(ModelView):
#	inline_models = (Contact)


admin = Admin(app)
admin.add_view(MyModelView(User))
admin.add_view(MyModelView(RecruitingZone))
admin.add_view(MyModelView(UserRZ))
admin.add_view(MyModelView(Contact))
admin.add_view(MyModelView(Comment))


############
# Login   ##
############




login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    return User.get(userid=userid)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = None
    try:
    	registered_user = User.get(User.username == username, User.password == password)
    except:
    	registered_user = None
    
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    
    else:
    	login_user(registered_user)
    
    	flash('Logged in successfully')
    
    	return redirect(request.args.get("next") or url_for('index'))
    
    



############
# Logout  ##
############

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('login')


#################
# Add comments ##
#################

@app.route("/comments/<int:id>/", methods=['GET', 'POST'])
@login_required
def show_comments(id):
	if request.method == 'GET':
		comments = Comment.select(Comment.comment).where(Comment.contact == id)
		#comments_json = json.dumps(str(model_to_dict(comments.comment)))
		return render_template('comments.html',
			comments = comments)
	if request.method == 'POST':
		comment = request.form['new_comment']
		contact = id
		user = current_user.userid
		Comment.insert(user = user,
					   contact = contact,
					   comment = comment
					   ).execute()

		comments = Comment.select(Comment.comment).where(Comment.contact == id)
		
		return render_template('comments.html',
			comments = comments)


@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

####################################
####################################
####################################
if __name__ == '__main__':
	try:
		create_tables()

	except: pass

	app.run(
        host="0.0.0.0",
        port=5000,
        use_reloader=True,
        debug=True,
    )

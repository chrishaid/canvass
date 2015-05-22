import os
import csv
import datetime
from flask import Flask
from flask import render_template
from peewee import *
from playhouse.csv_utils import load_csv

app = Flask(__name__)

#################
# Data         #
#################

# Load address data from CSV 
csv_path = './static/combined_addresses.csv'
csv_obj = csv.DictReader(open(csv_path, 'rU'))
csv_list = list(csv_obj)
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
	rz = CharField()

class User(BaseModel):
	"""User table and class"""
	username = CharField(unique = True)
	password = CharField()
	join_date = DateTimeField(default = datetime.datetime.now)
	active = BooleanField(default = True)
	admin = BooleanField(default = False)

class Comment(BaseModel):
	"""Comment for contacts from users"""
	user = ForeignKeyField(User, related_name='comments')
	contact = ForeignKeyField(Contact, related_name='contacts')
	comment = CharField()


def create_tables():
	"""Create tables in postgresql db from model and import contact adresses"""
	db.connect()
	db.create_tables([Contact, User, Comment])
	Contact.insert_many(csv_obj).execute()



############
# App     ##
############
@app.route("/")
def index():
    return render_template('index.html', 
           object_list=csv_list,
)


#@app.route('/<number>/')
#def detail(number):
#    return render_template('detail.html',
#        object=csv_dict[number],
#    )

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5000,
        use_reloader=True,
        debug=True,
    )

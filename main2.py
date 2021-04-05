import pymysql
import sqlite3
import os
from app import app
from datetime import datetime
from db_config import mysql
from flask import flash, render_template, jsonify, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm	
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from wtforms.fields.html5 import DateTimeField
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_classful import FlaskView, route


dir = os.getcwd()
PROJECT_ROOT = dir

app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + PROJECT_ROOT + '/database.db'

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@127.0.0.1:3306/calendar_system'
Bootstrap(app)
db = SQLAlchemy(app)
#
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class LoginForm(FlaskForm):
	username = StringField('username', validators=[InputRequired(message='Username cannot be empty'), Length(min=4, max=15)])
	password = PasswordField('password', validators=[InputRequired(message='Password cannot be empty'), Length(min=8, max=80)])
	remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
	email = StringField('email', validators=[InputRequired(message='Email cannot be empty'),Email(message='This is not the correct email format'), Length(max=50)])
	username = StringField('username', validators=[InputRequired(message='Username cannot be empty'), Length(min=4, max=15)])
	password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
	submit = SubmitField('Submit')

class EventForm(FlaskForm):
	event_title = StringField('Schedule name', validators=[InputRequired(message='The schedule name cannot be empty')])
	type = SelectField('Please select a category', validators=[InputRequired()],
					   choices=[('event-info', 'Info Blue'), ('event-important', 'Important-red'), ('event-error', 'Normal-gray')],
					   id='typearea')
	start = DateTimeField('Start time（format：yyyy/mm/dd hh:mm）', validators=[InputRequired(message='The start date cannot be empty')], format='%Y/%m/%d %H:%M',id='datetime-start')
	end = DateTimeField('End Time（format：yyyy/mm/dd hh:mm）', validators=[InputRequired(message='The end date cannot be empty')], format='%Y/%m/%d %H:%M',id='datetime-end')
	descirbe = StringField('Detailed remarks')
	submit = SubmitField('submit')

class SearchForm(FlaskForm):
	keyword = StringField('Keyword search schedule', validators=[InputRequired()])
	submit = SubmitField('search for')

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(15), unique=True) 
	email = db.Column(db.String(15), unique=True)
	password = db.Column(db.String(80))

class Event(db.Model):
	id = db.Column(db.Integer, primary_key=True)  # unique id
	title = db.Column(db.String)
	url = db.Column(db.String)
	type = db.Column(db.String) # class??
	start_time = db.Column(db.TIMESTAMP)  # datetime
	end_time = db.Column(db.TIMESTAMP)
	author_name = db.Column(db.String, db.ForeignKey("user.username"))

	@route('/add/<int:event_id>', methods = ['GET', 'POST'])
	def add(new_event):
			db.session.add(new_event) 
			db.session.commit()
			#return redirect(url_for('edit'))

	@app.route('/delete/<int:event_id>', methods = ['GET', 'POST'])
	def delete(event_id):
		conn = sqlite3.connect("database.db")
		cursor = conn.cursor()
		sql_delete = 'DELETE FROM event WHERE id={}'.format(event_id)
		cursor.execute(sql_delete)
		conn.commit()
		conn.close()
		return redirect(url_for('Event_Utils:edit'))

	@app.route('/edit/<int:event_id>', methods = ['GET', 'POST'])
	def descirbe(event_id):
		print("Incoming at this time Event ID % i" % event_id)
		one_event = Event.query.filter_by(id=event_id).first()
		print("Find the Event successfully:" + one_event.title)
		return render_template('one_event.html', event=one_event)

	@app.route('/check/<string:event_name>', methods = ['GET', 'POST'])
	def check(event_name):
		# event name is a string
		tmp_e = db.session.query(Event).filter_by(title=event_name).first()
		check_list_event = db.session.query(Event).filter(Event.title.ilike(event_name)).all()
		print(check_list_event)
		#return jsonify({'Check_list_event' : check_list_event})

class Event_Utils(FlaskView):
	route_base = '/'
	@route('/edit', methods=['GET', 'POST'])
	def edit(event_id=None):
		
		form = EventForm()
		search_form = SearchForm()
		result = []
		all_event_list = Event.query.filter_by(author_name=current_user.username).order_by(Event.start_time).all()
		print(all_event_list)
		# for ev in all_event_list:
		# 	print(ev.title)
		# 	print(ev.type)
		# 	print(ev.start_time)


		if form.validate_on_submit():
			print("Verified successfully")
			new_event = Event(title=form.event_title.data,
						url='http://127.0.0.1:5000/edit',
							type=form.type.data,
							start_time=form.start.data,
							end_time=form.end.data,
							author_name=current_user.username)
			print(new_event.title)
			print(new_event.type)
			print(new_event.start_time)
			print(new_event.author_name)
			try:
				Event.add(new_event)
				new_id = new_event.id
				tmp_event = Event.query.filter_by(id=new_id).first()
				tmp_event.url = 'http://127.0.0.1:5000/edit/' + str(new_id)
				db.session.commit()
				return redirect(url_for('Event_Utils:edit'))
			except Exception as e:
				print(e)
				print("There were some problems when joining this event!")
				return 'There were some problems when joining this event!'
		elif search_form.validate_on_submit():
			keyword = search_form.keyword.data
			sql_search = '%' + keyword + '%'
			result = Event.query.filter_by(author_name=current_user.username).filter(Event.title.ilike(sql_search)).order_by(Event.start_time).all()

			flash('The search is complete.', 'info')
			print("The search form is legal! ! Searched" + sql_search + "Output search results below")
			print(result)
			for ev in result:
				print("The query results are shown below")
				print(ev.id)
				print(ev.title)
				print(ev.type)
				print(ev.start_time)
			return render_template('search_result.html', keyword=keyword, search=result, res_len=len(result))

		print("After entering the edit function, it will return list_and_edit html, the search result is:")
		return render_template('list_and_edit.html', form=form, search_form=search_form,
							user=current_user, event_list=all_event_list, len=len(all_event_list),
							search=result,res_len=len(result))



@app.route('/')
def index():
	#return render_template('calendar_events.html')
	return render_template('index.html')


@app.route('/dashboard',methods=['GET','POST']) # profile
@login_required
def dashboard():
	return render_template('calendar_events.html', message='What I saw after logging in', name=current_user.username)

@app.route('/calendar-events')
def calendar_events():
	conn = None
	cursor = None
	try:
		conn = sqlite3.connect("database.db")
		cursor = conn.cursor()
		sql_select = "SELECT id, title, url, type, (strftime('%s', start_time)-28800)*1000 as start, (strftime('%s', end_time)-28800)*1000 as end FROM event where author_name='" + current_user.username + "'";
		rows = cursor.execute(sql_select).fetchall()
		print(rows)

		rows_dict = []
		dict_key = ('id','title','url','class','start','end')
		for line in rows:
			rows_dict.append(dict(zip(dict_key, line)))

		resp = jsonify({'success' : 1, 'result' : rows_dict})
		resp.status_code = 200
		return resp
	except Exception as e:
		print('OH my god! Exception found!')
		print(e)
	finally:
		print("There is a finally in calendar_event that I don’t know why, conn is Nonetype, and the database has not been deployed yet")
		cursor.close()
		conn.close()

class User_Utils(FlaskView):
	@app.route('/login', methods=['GET','POST'])
	def login():
		form = LoginForm()
		if form.validate_on_submit():
			# query database
			user = User.query.filter_by(username=form.username.data).first() # username should be unique
			if user:
				if check_password_hash(user.password, form.password.data):
					# if password correct, redirect to their dashboard
					login_user(user, remember=form.remember.data)
					return redirect(url_for('dashboard'))

			flash('Username does not exist or password is incorrect')
		return render_template('login.html', form=form)

	@app.route('/signup', methods=['GET','POST'])
	def signup():
		form = RegisterForm()
		if form.validate_on_submit():
			hashed_password = generate_password_hash(form.password.data, method='sha256')
			new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
			try:
				db.session.add(new_user)
				db.session.commit()
				flash('registration success')
			except Exception as e:
				#db.session.rollback()
				flash('The user already exists') # and pop put a href to login
				#return redirect(url_for('login'))

		return render_template('signup.html', form=form)


	@app.route('/logout')
	@login_required
	def logout():
		logout_user()
		return redirect(url_for('index'))



Event_Utils.register(app, route_base='/')


if __name__ == "__main__":
	app.run(debug=True)

from flask import Flask, request, make_response, render_template, url_for, Response, redirect, send_from_directory
import csv
import datetime
import mysql.connector
import os
import requests
from validate_email import validate_email
import pickle

app = Flask(__name__)

host = 'localhost'
db = 'busqdb'
user = 'busq'
pwd = 'be a morning person'

def remove_space(string):
    length = len(string)
    while (string[length-1] == ' '):
        length-=1
    return string[0:length]
    
#login the user  
def user_login(userid):
	#pickle.dump(userid, open("log", "wb"))
	r = make_response(redirect('main'))
	outdate=datetime.datetime.today() + datetime.timedelta(days=360)
	r.set_cookie('Name', userid, expires=outdate)
	return r

#update username
def appdb_update_username(username, userid, host, db, user, pwd):
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)

	query = "UPDATE user_table SET username=\"" +username+ "\" WHERE userid = \"" +userid+ "\""
	cursor.execute(query)
	conn.commit()

	cursor.close()
	conn.close()
	
	
#update user email	
def appdb_update_useremail(newemail, userid, host, db, user, pwd):
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)
	print 'new email is', newemail
	query = "UPDATE user_table SET  email=\"" +newemail+ "\" WHERE userid = \"" +userid+ "\""
	cursor.execute(query)
	conn.commit()

	cursor.close()
	conn.close()	
	
	
#update user password	
def appdb_update_userpassword(newpassword, userid, host, db, user, pwd):
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)

	query = "UPDATE user_table SET  password=" +newpassword+ " WHERE userid = \"" +userid+ "\""
	cursor.execute(query)
	conn.commit()

	cursor.close()
	conn.close()
		
#change user details
@app.route('/update')  
def user_details_update():
	return render_template('update.html')
	
#change username
@app.route("/update/username", methods=['GET','POST'])  
def update_username():
	name=request.cookies.get('Name')
	valid = ''
	    
	if request.method=='POST':              
		username = request.form['username'] 

    ############### check if firstname and lastname are valid ################
		if(len(str(username))>=255 or str.isalnum(str(username)) == False):
			print "not a valid username"
			valid = 'invalid username'


		if (valid == ''):
			appdb_update_username(str(username), name, host, db, user, pwd)
			r = user_login(name)
			return r
	return make_response(render_template('update_username.html', valid = valid)) 


#change password
@app.route("/update/password", methods=['GET','POST'])  
def update_password():
	name=request.cookies.get('Name')
	valid = ''

	if request.method=='POST':              
		originalpassword = request.form['originalpassword'] 
		newpassword = request.form['newpassword']
		confirmnewpassword = request.form['confirmnewpassword']
        
		if(len(str(newpassword)) < 6 or str.isalnum(str(newpassword)) == False):
			print "not a valid password"
			valid =  'invalid password'
        
		conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
		cursor = conn.cursor(buffered=True)
		query = "SELECT password FROM user_table WHERE userid = \"" +name+ "\""
		cursor.execute(query)
		password = cursor.fetchone()[0]
		cursor.close()
		conn.close()
        
		if (str(password) != str(originalpassword)):
			valid = 'Password is wrong'

		if (len(str(newpassword))>=255 or str(newpassword)!=str(confirmnewpassword)):
			valid = 'Not the same password'
        
		if (valid == ''):
			appdb_update_userpassword(newpassword, name, host, db, user, pwd)
			r = user_login(name)
			return r  
	return make_response(render_template('update_password.html', valid = valid)) 

#change email address
@app.route("/update/email", methods=['GET','POST'])  
def update_email():
	userid = request.cookies.get('Name')
	valid = ''
	if request.method=='POST':              
		newemail = request.form['newemail'] 
		if(len(str(newemail))>=255 or validate_email(str(newemail)) == False):
			print "not a valid email"
			valid = 'invalid email address'
		if (valid == ''):
			appdb_update_useremail(str(newemail), userid, host, db, user, pwd)
			r = user_login(userid)
			return r

	return make_response(render_template('update_email.html', valid = valid)) 
                
#if this userid already signed up
def has_userid_signedup(userid, host, db, user, pwd):
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)
	query = "SELECT has_signed_up FROM user_table WHERE userid = \"" + userid + "\""
	cursor.execute(query)

	retval = cursor.fetchone()[0]

	cursor.close()
	conn.close()
	return retval
    
    

#santinise user details input
def valid_signup(cookie, username, password, email, confirmpassword, host, db, user, pwd):
	
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)
	query = ("SELECT has_signed_up FROM user_table WHERE userid = \"" + cookie + "\"")
	cursor.execute(query)
	for(has_signed_up) in cursor:
		has_signed_up = str(has_signed_up)
	cursor.close()
	conn.close()
	if(has_signed_up == '1'):
		print "An account already existing in this device"
		return 'An account already existing in this device'
	
	
	if(len(str(email))>=255 or validate_email(str(email)) == False):
		print "not a valid email"
		return 'invalid email address'
	
	if(does_email_exist(str(email), host, db, user, pwd) != 0):
		return 'Email already exists. Please login.'
	
	if(len(str(password)) < 6 or len(str(password)) >= 255):
		print "not a valid password"
		return 'Password must be longer than 6 charaters!'
	if(str.isalnum(str(password)) == False):
		print "not a valid password"
		return 'Password must be combination of only numbers and letters.'
	
	if(len(str(username))>=255 or str.isalnum(str(username)) == False):
		print "not a valid first name"
		return 'invalid username'
	
	
	if (str(password) != str(confirmpassword) or len(str(password)) >= 255):
		return 'Not the same password'
		

	return True
	
#Signup: check if singuo email already exists
def does_email_exist(email, host, db, user, pwd):
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor(buffered=True)
    
    query = "SELECT email FROM user_table WHERE email = \"" + email + "\""
    cursor.execute(query)
    
    rowcount = cursor.rowcount

    cursor.close()
    conn.close()
    print rowcount

    return rowcount   
    



#santinise user login details
def valid_login(email,password):
	if(len(str(email))>=255 or validate_email(str(email)) == False):
		print "not a valid email"
		return 'invalid email address'
	
	if(len(str(password)) != 6 or str.isalnum(str(password)) == False):
		print "not a valid password"
		return 'invalid password'
	return True
	

#verify users' login details
def appdb_verify_logindetails(email, password, current_cookie, host, db, user, pwd):
	username = None
	cookie = None
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)
	query = ("SELECT userid FROM user_table WHERE email = \"" + email + "\" and password = '" + password + "'")
	cursor.execute(query)
	for(userid) in cursor:
		cookie = userid[0]
	rowcount = cursor.rowcount
	#print "cookie is", cookie
	print "login matched rowcount ", rowcount
	
	if(current_cookie == None):
		has_signed_up = 1
	else:
		query1 = ("SELECT has_signed_up FROM user_table WHERE userid = \"" + current_cookie + "\"")
		cursor.execute(query1)
		print query1
		#for(has_signed_up) in cursor:
		#has_signed_up = has_signed_up[0]
		has_signed_up = cursor.fetchone()[0]
	print "has_signed_up is ", has_signed_up
	
	if rowcount == 1:
		#check if one userdetail matches two user ids
		if (cookie != current_cookie and has_signed_up == 0):
			#query = "SELECT stat_lastscantime FROM user_table WHERE userid = \"" +current_cookie+ "\""
			#cursor.execute(query)   
			#for(stat_lastscantime) in cursor:
				#numscans = str(stat_numscans)
				#lastscan = str(stat_lastscantime)
			#print "type lastscan ", lastscan
		
			#print "numscnas is ", numscans

            #merge userid details with newuserid
			#query = "UPDATE user_table SET stat_lastscantime = \"" +lastscan+ "\" ,stat_reward=stat_numscans*10 WHERE userid = \"" +cookie+ "\""
			#cursor.execute(query)
			#conn.commit()
			#delete the new cookie
			query3 = ("DELETE from user_table WHERE userid = \"" + current_cookie + "\" ")
			cursor.execute(query3)
			query = ("ALTER TABLE user_table AUTO_INCREMENT = 1")
			cursor.execute(query)
			#set the old cookie in user device
			
		
		#fetch firstname
		query4 = ("SELECT username FROM user_table WHERE email = \"" + email + "\"")
		cursor.execute(query4)
		for(username) in cursor:
			username = str(username[0])

        

	conn.commit()	
	cursor.close()
	conn.close()
	print "curren cookie is", current_cookie
	return (username, cookie)
	




#save processing data to main DB
def send_to_maindb(SENSOR_UUID, userid, timestamp, host, db, user, pwd):
    conn = mysql.connector.connect(host = host,
                                           database= db,
                                           user = user,
                                           password = pwd)
    cursor = conn.cursor()

    query = ("SELECT token FROM tokenstore WHERE sensor_uuid = '" + SENSOR_UUID + "'")

    cursor.execute(query)

    retval = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    SECRET_TOKEN = retval
    HOST = 'http://aquarii:5000'
    URI = '/api/v1/sensors/' + SENSOR_UUID + '/readings'

    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data = {  

        'data':{
            'userid': userid
        },
        'timestamp': timestamp,
        'server_timestamp': current_time, 
        'token': SECRET_TOKEN
        
    }

    r = requests.post(HOST + URI, json=data)
    print("DEBUGINFO: main DB submission.  URL:" + r.url + " returncode: " + str(r) )






#getting wait_time and last updated time from Rachel
def query_wait_time(uuid, host, db, user, pwd):
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor()
    
    query = ("SELECT timestamp, wait_time FROM wait_time_table "
             "WHERE sensor_uuid = \"" + uuid + "\"")
    
    cursor.execute(query)
    t = 0
    UpdatedTime = 0
    
    for(timestamp, wait_time) in cursor:
       t = wait_time
       UpdatedTime = timestamp
    #print("your estimated waiting time for poll %d, qr %d is %d", PollId, QrId, EstimatedTime)
    cursor.close()
    conn.close()
    return (t, UpdatedTime)


#check if this cookie already existed in the AppDB
def does_user_exist(name, host, db, user, pwd):
    #name = '(' + 'u' + "'" + name + "'" + ',)'
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor(buffered=True)
    
    query = "SELECT userid FROM user_table WHERE userid = \"" + name + "\""
    cursor.execute(query)

    rowcount = cursor.rowcount

   
    cursor.close()
    conn.close()

    return rowcount
    

#check if this uuid already existed in AppDB
def does_uuid_exist(uuid, host, db, user, pwd):
    #name = '(' + 'u' + "'" + name + "'" + ',)'
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor(buffered=True)
    
    query = "SELECT sensor_uuid FROM wait_time_table WHERE sensor_uuid = \"" + uuid + "\""
    cursor.execute(query)
    
    rowcount = cursor.rowcount

    cursor.close()
    conn.close()

    return rowcount
  
   
    



#send user details to app db
def appdb_update_signupdetails(username, email, password, name, host, db, user, pwd):#, email, password, name
    #name = '(' + 'u' + "'" + name + "'" + ',)'
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor()

    #query = ("UPDATE user_table SET (username, password, email) = ('"+ username + "','" + password + "','" + email + "')"
        #"WHERE user_table_userid = ('"+ name +"')")
    query = ("UPDATE user_table SET username = '"+ username + "', password = '"+ password + "', email = '"+ email + "', has_signed_up = '1' "
         "WHERE userid = \"" + name + "\"")

    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

#send scanning details to App Db (increment count)
def appdb_updateuser(name, time_stamp, host, db, user, pwd):
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor()

    ###############
    query1 = ("SELECT stat_numscans FROM user_table "
             "WHERE userid = \"" + name + "\"")
    
    cursor.execute(query1)

    for(stat_numscans) in cursor:
       count = int(stat_numscans[0])
       count += 1
       print ("scanned times ", count)
       number = count 
       count = str(count)
       
    ###############
    points = str((number-1)*10)
    query = ("UPDATE user_table SET stat_lastscantime = '"+ time_stamp + "', stat_numscans = '"+ count + "', stat_reward = '"+ points + "'  "
         "WHERE userid = \"" + name + "\"")

    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()
    return number 



#send cookie to App db
def appdb_adduser(user_cookie, host, db, user, pwd):
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor()

    query = "INSERT INTO user_table (userid, stat_numscans) VALUES ('"+ user_cookie +"', '0')"

    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()


#generate a random string
def randomString(n):
    return (''.join(map(lambda xx:(hex(ord(xx))[2:]),os.urandom(n))))[0:16]



@app.route('/finish')
def finish():
   return "Thank you, You have signed up!";
   
@app.route('/main')
def main():
	#get userid from db
	f = open("log", "rb")
	uuid=pickle.load(f)
	userid = request.cookies.get('Name')
	print "DEBUGINFO: in main, cookie is ", userid
    #fetch info
	wait_time = pickle.load(f)
	TimeStamp = pickle.load(f)
	f.close()
    
	conn = mysql.connector.connect(host='localhost',database='busqdb',user='busq',password='be a morning person')
	cursor = conn.cursor(buffered=True)

	query = "SELECT username, email, stat_numscans, stat_lastscantime, stat_reward FROM user_table WHERE userid = \"" + userid + "\""
	cursor.execute(query)

	for (username, email, stat_numscans, stat_lastscantime, stat_reward) in cursor:
		username = username
		email = email
		numscans = stat_numscans
		lastscantime = stat_lastscantime
		reward = stat_reward

	retval = (username, email, numscans, lastscantime, reward)
	print "retval is ", retval


	cursor.close()
	conn.close()
	return render_template('main.html', TimeStamp = TimeStamp, wait_time = wait_time, username = username, N = numscans, reward = reward, email = email, time = lastscantime, uuid = uuid)



@app.route('/static/<path:path>')
def staticresources(path):
	return send_from_directory('static', path);


#login page for users
@app.route("/login", methods=['GET','POST'])  
def manual_login():
	name=request.cookies.get('Name')
	valid_login_status = None
	valid = ''
	if request.method=='POST':           
		password = request.form['password']
		email = request.form['email']
		valid = valid_login(email,password)
		if valid == True: 
			(username, cookie) = appdb_verify_logindetails(email, password, name, host, db, user, pwd)
			if (username != None):
				print "DEBUGINFO: username ", username, " is dumped into pickle"
				print "Cookie is", cookie
				r = user_login(cookie)
				return r
			else:
				valid = 'Incorrect user details. Please try again or signup!'
        
        
    
         

	return render_template('login.html', valid_login_status = valid)
    
    

#logout page
@app.route("/logout")  
def logout():
	r = make_response(render_template('logout.html'));
	r.set_cookie('Name', expires=0)
	return r



#signup page to get user details
@app.route("/signup", methods=['GET','POST'])  
def signup():
    name=request.cookies.get('Name')
    valid = ''
    if request.method=='POST':   #what if it's not post           
        username = request.form['username'] 
        password = request.form['password']
        email = request.form['email']
        confirmpassword = request.form['confirmpassword']
        valid = valid_signup(name, remove_space(username), password, email, confirmpassword, host, db, user, pwd)
        if valid == True : 
			appdb_update_signupdetails(remove_space(username), email, password, name, host, db, user, pwd)
			r = user_login(name)
			return r 
             
		
        
        
    
   
    return render_template('signup.html', valid_signup_status = valid)


@app.route('/bstop')
def bstop(): 
	
    ### Collect information
	uuid=str(request.query_string)
	f = open("log", "wb")
	pickle.dump(uuid,f)
	name=request.cookies.get('Name')
	print ("DEBUGINFO:  initial userid: " + str(name))
	print ("DEBUGINFO:  QRcode uuid: " + uuid)


    ### Check if provided information is correct and safe
	if len(uuid) != 32:
		print("DEBUGINFO: UUID is not the correct length");
		return make_response(render_template('wrong.html', enter = uuid));
	if str.isalnum(uuid) == False:
		print("DEBUGINFO: UUID has invalid characters");
		return make_response(render_template('wrong.html', enter = uuid));
	if does_uuid_exist(uuid, host, db, user, pwd) == False:
		print ("DEBUGINGINOF: UUID is not in the db");
		return make_response(render_template('wrong.html', enter = uuid));
    
	(wait_time, UpdatedTime)=query_wait_time(uuid, host, db, user, pwd)
	pickle.dump(wait_time,f)
	pickle.dump(UpdatedTime,f)
	f.close()
    
	now = datetime.datetime.now()
	otherStyleTime = now.strftime("%Y-%m-%d %H:%M:%S")
	time_stamp = str(otherStyleTime)
    
	if(name == None or len(name) != 16 or str.isalnum(str(name)) == False or does_user_exist(name, host, db, user, pwd) == False):
       #Set cookies for the new user
       #randomly generate a string with user ID inside and set it as a cookie
		Random = randomString(16)
		name = Random
       #send the new cookie to AppDB
		appdb_adduser(name, host, db, user, pwd)
		
       
  
    
	times = appdb_updateuser(name, time_stamp, host, db, user, pwd)
	print("DEBUGINGINFO: scanned times: ", times)
	
	### Submit data to main DB
	send_to_maindb(uuid, name, time_stamp, host, db, user, pwd)
	
	print("DEBUGINFO: final userid: " + name)
    
    ### Generate the HTML page and set the cookie
	if(has_userid_signedup(name, host, db, user, pwd) == 1):
		print "/main"	
		r = user_login(name)
		return r

  
	else:
    ############
		welcome_info = "Welcome " + name[0:6]
		reward_info = "You have earned " + str(times*10) + " cents!"
    ############
		r = make_response(render_template('website.html', welcome_info = welcome_info, reward_info=reward_info, N = times, user_name = name, time = time_stamp, wait_time = wait_time, TimeStamp = UpdatedTime, uuid=uuid));
		outdate=datetime.datetime.today() + datetime.timedelta(days=360)
		r.set_cookie('Name',name,expires=outdate)
		print "/bstop"
		return r
    
	
	
   

if __name__ == "__main__":
    app.run(host="0.0.0.0")

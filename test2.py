from flask import Flask, request, make_response, render_template, url_for, Response, redirect, send_from_directory
import csv
import datetime
import mysql.connector
import os
import requests
from validate_email import validate_email
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

#santinise user details input
def valid_signup(cookie, username_first,username_last, password, email, confirmpassword, host, db, user, pwd):
	
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)
	query = ("SELECT has_signed_up FROM user_table WHERE userid = \"" + cookie + "\"")
	cursor.execute(query)
	for(has_signed_up) in cursor:
		has_signed_up = str(has_signed_up)
	cursor.close()
    conn.close()
    if (has_signed_up == '1'):
		print "An account already existing in this device"
		return 'An account already existing in this device'
	
	
	if(len(str(email))>=255 or validate_email(str(email)) == False):
		print "not a valid email"
		return 'invalid email address'
	
	if(does_email_exist(str(email), host, db, user, pwd) != 0):
		return 'Email already exists. Please login.'
	
	if(len(str(password)) != 6 or str.isalnum(str(password)) == False):
		print "not a valid password"
		return 'invalid password'
	
	if(len(str(username_first))>=255 or str.isalnum(str(username_first)) == False):
		print "not a valid first name"
		return 'invalid first name'
	
	if(len(str(username_last))>=255 or str.isalnum(str(username_last)) == False):
		print "not a valid last name"
		return 'invalid last name'
	
	if (len(str(confirmpassword)) != 6 or str(password) != str(confirmpassword)):
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
	user_firstname = None
	conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
	cursor = conn.cursor(buffered=True)
	query = ("SELECT userid FROM user_table WHERE email = \"" + email + "\" and password = '" + password + "'")
	cursor.execute(query)
	for(userid, has_signed_up) in cursor:
		cookie = userid[0]
	rowcount = cursor.rowcount
	print cookie
	
	query1 = ("SELECT has_signed_up FROM user_table WHERE userid = \"" + current_cookie + "\"")
	cursor.execute(query1)
	for(has_signed_up) in cursor:
		has_signed_up = str(has_signed_up)
	
	if rowcount == 1:
		#check if one userdetail matches two user ids
		if (cookie != current_cookie and has_signed_up == '0'):
			#Update scan_count
			query2 = ("UPDATE user_table SET stat_numscans = stat_numscans + 1 WHERE userid = \"" + cookie + "\"")##+1 not ok
			cursor.execute(query2)
			#delete the new cookie
			query3 = ("DELETE from user_table WHERE userid = \"" + current_cookie + "\" ")
			cursor.execute(query3)
			#set the old cookie in user device
		else if (cookie != current_cookie and has_signed_up == '1'):
			#this user tried to login in others' device
			cookie = None
			return (user_firstname, cookie)
			
			
		
		#fetch firstname
		query4 = ("SELECT firstname FROM user_table "
             "WHERE email = \"" + email + "\"")
		cursor.execute(query4)
		for(firstname) in cursor:
			user_firstname = str(firstname)
		query5 = ("UPDATE user_table SET login_status = '1' "
         "WHERE email = \"" + email + "\"")
		cursor.execute(query5)
		
        

	conn.commit()	
	cursor.close()
	conn.close()
	print type(user_firstname)
	return (user_firstname, cookie)
	




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
def appdb_update_signupdetails(username_first, username_last, email, password, name, host, db, user, pwd):#, email, password, name
    #name = '(' + 'u' + "'" + name + "'" + ',)'
    conn = mysql.connector.connect(host = host, database = db,user = user,password = pwd)
    cursor = conn.cursor()

    #query = ("UPDATE user_table SET (username, password, email) = ('"+ username + "','" + password + "','" + email + "')"
        #"WHERE user_table_userid = ('"+ name +"')")
    query = ("UPDATE user_table SET firstname = '"+ username_first + "', lastname = '"+ username_last + "', password = '"+ password + "', email = '"+ email + "', has_signed_up = '1' "
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
    points = str(number*10)
    query = ("UPDATE user_table SET stat_lastscantime = '"+ time_stamp + "', stat_numscans = '"+ count + "', stat_reward_placeholder = '"+ points + "'  "
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
	return render_template('main.html')



@app.route('/static/<path:path>')
def staticresources(path):
	return send_from_directory('static', path);


#login page for users
@app.route("/login", methods=['GET','POST'])  
def login():
    name=request.cookies.get('Name')
    valid_login_status = None
    valid = ''
    if request.method=='POST':           
        password = request.form['password']
        email = request.form['email']
        valid = valid_login(email,password)
        if valid == True: 
			(firstname, cookie) = appdb_verify_logindetails(email, password, name, host, db, user, pwd)
			if (firstname != None):
				r = make_response(redirect('main'))
				outdate=datetime.datetime.today() + datetime.timedelta(days=30)
				r.set_cookie('Name', cookie, expires=outdate)
				return r

			else if (firstname == None and cookie == None):
				valid = 'Please use your own device to login.'	
             
			else:
				valid = 'Incorrect user details. Please try again or signup!'
        
        
    
         

    return render_template('login.html', valid_login_status = valid)





#signup page to get user details
@app.route("/signup", methods=['GET','POST'])  
def signup():
    name=request.cookies.get('Name')
    valid = ''
    if request.method=='POST':   #what if it's not post           
        username_first = request.form['firstname'] 
        username_last = request.form['lastname']
        password = request.form['password']
        email = request.form['email']
        confirmpassword = request.form['confirmpassword']
        valid = valid_signup(name, remove_space(username_first), remove_space(username_last), password, email, confirmpassword, host, db, user, pwd)
        if valid == True : 
			appdb_update_signupdetails(username_first, username_last, email, password, name, host, db, user, pwd)#sign in status?
			#count - 1
			return redirect(url_for('finish')) 
             
		
        
        
    
         

    return render_template('signup.html', valid_signup_status = valid)


@app.route('/bstop')
def bstop(): 
	
    ### Collect information
    uuid=str(request.query_string)
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
    
    now = datetime.datetime.now()
    otherStyleTime = now.strftime("%Y-%m-%d %H:%M:%S")
    time_stamp = str(otherStyleTime)
    

    if (name == None or len(name) != 16 or str.isalnum(str(name)) == False or does_user_exist(name, host, db, user, pwd) == False):
       #Set cookies for the new user
       #randomly generate a string with user ID inside and set it as a cookie
       Random = randomString(16)
       name = Random
       #send the new cookie to AppDB
       appdb_adduser(name, host, db, user, pwd)
       
	
  
       
    
    times = appdb_updateuser(name, time_stamp, host, db, user, pwd)
    print("DEBUGINGINFO: scanned times: ", times)
    
    

    ### Generate the HTML page and the cookie
    
    ############
  
    welcome_info = "Welcome " + name[0:6]
    reward_info = "You have earned " + str(times*10) + " cents!"
    ############
    r = make_response(render_template('website.html', welcome_info = welcome_info, reward_info=reward_info, N = times, user_name = name, time = time_stamp, wait_time = wait_time, TimeStamp = UpdatedTime, uuid=uuid));
    outdate=datetime.datetime.today() + datetime.timedelta(days=30)
    r.set_cookie('Name',name,expires=outdate)

    ### Submit data to main DB
    send_to_maindb(uuid, name, time_stamp, host, db, user, pwd)
    
    print("DEBUGINFO: final userid: " + name)
    return r
   

if __name__ == "__main__":
    app.run(host="0.0.0.0")

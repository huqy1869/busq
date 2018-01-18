from flask import Flask, request, Response, make_response
from flask import render_template
from flask import redirect, url_for

app=Flask(__name__)
N=1

@app.route('/ionic.css')
def ionic():
    return app.send_static_file('ionic.css')

@app.route("/bus")
def bus():
    user="32jfi8fil90ju9ki";
    global N;
    if N==1:

        welcome_info="Welcome "+user[0:6]
        reward_info="So far, your rewards are " +str(N*10) + " cents!"
        resp=make_response(render_template('website.html',welcome_info=welcome_info, reward_info=reward_info,N=N))
        N=N+1
        return resp

    else:
        welcome_info="Welcome back " +user[0:6]
        reward_info="So far, your rewards are "+str(N*10)+ " cents!"
        resp=make_response(render_template('website.html',welcome_info=welcome_info, reward_info=reward_info,N=N))
        N=N+1
        return resp

@app.route("/login", methods=['GET','POST'])
def login():
    error=None
    if request.method=='POST':
        if request.form['Username']==None or request.form['Password']==None:
            error='Invalid Input. Please try again.'
    return render_template('login.html',error=error)



if __name__=="__main__":
    app.run(host="0.0.0.0")

"""
blarg.py

Created on Mon Jul 28 08:48:59 2014

Author: Sam Connolly, modified from flask tutorial

Microblogging site

## For larger applications, it would be better to use a seperate .ini or
.py file to load values ##

#########
to start database:
    
import os
os.chdir('K:\\flask\\blarg')
from blarg import init_db,add_account_manual
init_db()
add_account_manual('sam','dog','true')

or 
import os
os.chdir('/export/xray11/sdc1g08/HDData/flask/blarg')
from blarg import init_db,add_account_manual
init_db()
add_account_manual('sam','dog','true')
"""

import os
import sqlite3
import time
import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
                    render_template, flash
from flask.ext.mobility import Mobility
from flask.ext.mobility.decorators import mobile_template
# create application
app = Flask(__name__)  # name given in brackets, but providing __name__
                            # is good for single apps, as the name will change
Mobility(app)
app.config.from_object(__name__)

# Load default config:
#  set username, password, database, key etc
# MAKE SURE DEBUG IS OFF WHEN LIVE OR USERS CAN EXECUTE CODE ON THE SERVER!
app.config.update(dict(
    DATABASE=os.path.join(app.root_path,'blarg.db'),
    DEBUG=True,    ### change this to flase before release!
    )) 

# override config from an environment variable,
#    to give var pointing to config file
app.config.from_envvar('BLARG_SETTINGS', silent=True)


#======== Database functions ===================================================

# database reading function
def connect_db():
    '''Connects to the specified database.'''
    
    rv = sqlite3.connect(app.config['DATABASE']) # connect to config database
    rv.row_factory = sqlite3.Row                  # get rows object
    
    return rv

# database connection creation function
def get_db():
    '''Opens a new database connection if there is none yet for the current 
        application context.'''
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

# close database connection function
@app.teardown_appcontext
def close_db(error):
    '''Closes the database again at the end of the request.'''
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql',mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

#=================================================================================
#--------------- General User Commands -------------------------------------------
#=================================================================================

#============ Home/ index page ===================================================
@app.route('/')
@mobile_template('{mobile/}home.html')      # this can be used for mobile friendliness!
def home(template):
    if 'username' in session:
        return render_template(template)
    else:
        session['logged_in'] = False
        return render_template(template)
       
#============ Blag Entry Commands ================================================


# show entries - list newest first (highest id first)
@app.route('/post/<int:n>')
@mobile_template('{mobile/}show_entries.html')
def show_entries(n,template):
    db = get_db()
    cur = db.execute('select title, time, text, etime, score, username, forum from entries order by id desc')
    entries = cur.fetchall()
    # show the post with the given id, the id is an integer
    return render_template(template,n=n, entries=entries)

# add new entry
@app.route('/add/<int:n>',methods=['POST'])
def add_entry(n):
    if not session.get('logged_in'):    # check if user is logged on
        abort(401)
    etime = time.time()
    timestamp = datetime.datetime.fromtimestamp(etime)\
                .strftime('%Y-%m-%d %H:%M:%S') # timestamp in good format
    db = get_db()
    db.execute('insert into staged (title,text,etime,time,score,username,forum) values (?,?,?,?,?,?,?)',
                [request.form['title'],request.form['text'],etime,timestamp,0,session['username'],n])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries',n=n))    # return to entries page

#======= score board =============================================================

@app.route('/scoreboard')
@mobile_template('{mobile/}scoreboard.html')
def scoreboard(template):
    db = get_db()
    cur = db.execute('select username,score from accounts order by id desc')
    accs = cur.fetchall()
    cur = db.execute('select username, score,forum from entries order by id desc')
    posts = cur.fetchall()
    
    scores = []  
    sscores = []
    mscores = []
    
    for acc in accs:
        username = acc['username']
        score = 0
        sscore = 0
        mscore = 0
        
        # add up scores for this account
        for post in posts:                  
            if post['username'] == username:
                score += int(post['score'])
                
                if int(post['forum']) < 6:
                    sscore += int(post['score'])
                else:
                    mscore += int(post['score'])
        
        # make sure scores are in order
        if len(scores) > 0:
            # overall
            done = False
            
            for i in range(len(scores)):
                if score < int(scores[i][1]) and done == False:
                    scores.insert(i,[username,str(score)])
                    done = True
                    
            if done == False:
                scores.append([username,str(score)])
               
            # science
            done = False
            
            for i in range(len(sscores)):
                if sscore < int(sscores[i][1]) and done == False:
                    sscores.insert(i,[username,str(sscore)])
                    done = True
                    
            if done == False:
                sscores.append([username,str(sscore)])
              
            # media
            done = False
            
            for i in range(len(mscores)):
                if mscore < int(mscores[i][1]) and done == False:
                    mscores.insert(i,[username,str(mscore)])
                    done = True
                    
            if done == False:
                mscores.append([username,str(mscore)])
        else:
            scores.append([username,str(score)]) 
            sscores.append([username,str(sscore)]) 
            mscores.append([username,str(mscore)]) 
   
    return render_template(template,scores=scores[::-1],sscores=sscores[::-1],mscores=mscores[::-1])    
    
#========== login/out commands ===================================================

@app.route('/login', methods=['GET','POST'])
@mobile_template('{mobile/}login.html')
def login(template):   
    error = None
    if request.method == 'POST':
        db = get_db()
        acc = db.execute('select username,password,admin from accounts order by id desc')
        accounts = acc.fetchall()

        for a in accounts:
            if request.form['username'] == a['username'] \
                and request.form['password'] == a['password']:
                        session['username'] = request.form['username']
                        
                        if a['admin'] == 'true':
                            session['admin'] = True
                            flash('You were logged in as admin')
                        else:
                            session['admin'] = False
                            flash('You were logged in')
                        session['logged_in'] = True
                        session['username'] = request.form['username']
                        
                        return redirect(url_for('home'))# return to entries if success
        else:
            error = 'Invalid username and password combination'
    return render_template(template,error=error)  # else return error
        
    
@app.route('/logout')
def logout():
    session.pop('logged_in',None)
    session['admin'] = False
    flash('You were logged out')
    return redirect(url_for('home'))

#---------------------------------------------------------------------------------
#=============== Admin user commands =============================================
#---------------------------------------------------------------------------------


#=================== accounts ====================================================

# display existing accounts
@app.route('/accounts')
def show_accounts(): 
    if not (session.get('logged_in') and session['admin'] == True):    # check if user is logged on
        abort(401)
    db = get_db()
    cur = db.execute('select username,password,admin from accounts order by id desc')
    accounts = cur.fetchall()
    return render_template('show_accounts.html', entries=accounts)

# add new account
@app.route('/add_account',methods=['POST'])
def add_account():
    if not (session.get('logged_in') and session['admin'] == True):    # check if user is logged on
        abort(401)

    if request.form['username'] != '' and request.form['password'] != '':
        db = get_db()
        if 'admin' in request.form.keys():
            admin = 'true'
        else:
            admin = 'false'
        db.execute('insert into accounts (username,password,admin,score) values (?,?,?,?)',
                    [request.form['username'],request.form['password'],admin,0])
        db.commit()
        flash('New account was successfully added')
        return redirect(url_for('show_accounts'))    # return to entries page
        
    else:
        flash('Non-blank username and password required')
        return redirect(url_for('show_accounts'))

# delete account
@app.route('/delete_account',methods=['POST'])
def delete_account():
    if not (session.get('logged_in') and session['admin'] == True):    # check if user is logged on
        abort(401)
    if 'confirm' in request.form.keys():
    
        db = get_db()
        cur = db.execute('select username from accounts order by id desc')
        accounts = cur.fetchall()

        for account in accounts:
            if request.form['delete'] == account['username']:
                    selected = account
            
        db.execute('delete from accounts where username == (?)',[selected['username']])
        db.commit()
        flash('Account was successfully deleted')
        return redirect(url_for('show_accounts'))    # return to entries page


    else:
        flash('Confirm deletion before clicking to delete.')
        return redirect(url_for('show_accounts'))
      
# manually add account        
def add_account_manual(username,password,admin):
    with app.app_context():
        db = get_db()
        db.execute('insert into accounts (username,password,admin, score) values (?,?,?,?)',
                    [username,password,admin,0])
        db.commit() 

#=================== post staging and deletion ===================================

# display staged posts        
@app.route('/stage_entries')
def stage_entries():
    db = get_db()
    cur = db.execute('select title, time, text, etime,score,username,forum from staged order by id desc')
    entries = cur.fetchall()
    return render_template('stage_entries.html', entries=entries) 

# display deleted posts        
@app.route('/deleted')
def deleted_entries():
    db = get_db()
    cur = db.execute('select title, time, text, etime,score,username, forum from deleted order by id desc')
    entries = cur.fetchall()
    return render_template('deleted_entries.html', entries=entries) 

# submit or delete staged posts
@app.route('/submit',methods=['POST'])
def submit_staged():
    db = get_db()
    cur = db.execute('select title,text,time,etime, score,username, forum from staged order by id desc')
    staged = cur.fetchall()
    
    for entry in staged:
        keys = request.form.keys()
        
        if 'submit' in keys:
            
            score = request.form['score']
            
            if score == '':
                score = 0
            
            if request.form['submit'] == entry['etime']:
                    selected = entry
                    db.execute('insert into entries (title,text,time,etime,score,username,forum) values (?,?,?,?,?,?,?)',
                    [selected['title'],selected['text'],selected['time'],selected['etime'],score,selected['username'],selected['forum']])
                    flash('Staged entry was successfully posted')

        elif 'delete' in keys:                
            if request.form['delete'] == entry['etime']:
                selected = entry
                db.execute('insert into deleted (title,text,time,etime,score,username,forum) values (?,?,?,?,?,?,?)',
                [selected['title'],selected['text'],selected['time'],selected['etime'],selected['score'],selected['username'],selected['forum']])
                flash('Staged entry was successfully deleted')    
  
    db.execute('delete from staged where etime == (?)',[selected['etime']])
    db.commit()
    return redirect(url_for('stage_entries'))    # return to entries page

# delete submitted posts
@app.route('/delete/<int:n>',methods=['POST']) 
def delete_entry(n):   
    db = get_db()
    cur = db.execute('select title,text,time,etime,score,username,forum from entries order by id desc')
    entries = cur.fetchall()
  
    for entry in entries:
        if request.form['delete'] == entry['etime']:
                selected = entry
        
    db.execute('insert into deleted (title,text,time,etime,score,username,forum) values (?,?,?,?,?,?,?)',
                [selected['title'],selected['text'],selected['time'],selected['etime'],selected['score'],selected['username'],selected['forum']])
    db.execute('delete from entries where etime == (?)',[selected['etime']])
    db.commit()
    flash('Entry was successfully deleted')      
    return redirect(url_for('show_entries',n=n))    # return to entries page
 
# restore deleted posts
@app.route('/forum_restore',methods=['POST']) 
def restore_post():   
    db = get_db()
    cur = db.execute('select title,text,time,etime,score,username,forum from deleted order by id desc')
    entries = cur.fetchall()
  
    for entry in entries:
        if request.form['post'] == entry['etime']:
                selected = entry
        
    db.execute('insert into entries (title,text,time,etime,score,username,forum) values (?,?,?,?,?,?,?)',
                [selected['title'],selected['text'],selected['time'],selected['etime'],selected['score'],selected['username'],selected['forum']])
    db.execute('delete from deleted where etime == (?)',[selected['etime']])
    db.commit()
    flash('Entry was successfully restored to forum')      
    return redirect(url_for('deleted_entries'))    # return to entries page
       
@app.route('/staged_restore',methods=['POST'])   
def restore_staged():  
    db = get_db()
    cur = db.execute('select title,text,time,etime,score,username,forum from deleted order by id desc')
    entries = cur.fetchall()
  
    for entry in entries:
        if request.form['stage'] == entry['etime']:
                selected = entry
        
    db.execute('insert into staged (title,text,time,etime,score,username,forum) values (?,?,?,?,?,?,?)',
                [selected['title'],selected['text'],selected['time'],selected['etime'],selected['score'],selected['username'],selected['forum']])
    db.execute('delete from deleted where etime == (?)',[selected['etime']])
    db.commit()
    flash('Entry was successfully restored to staging')      
    return redirect(url_for('deleted_entries'))    # return to entries page
    
#========== Dev/testing ==========================================================


#=================================================================================
#            Run app
#=================================================================================

# set the secret key. Keep it safe. Keep it secret.
app.secret_key = '_~q\xf4c\x88\x1b\x0fPi\x88\x9dj?Ofj\x8f\xee\xa4\xcb\x9a\xe9U'

# run the application if run as standalone app
if __name__ == '__main__':
    app.run(host='0.0.0.0')
    
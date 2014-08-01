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
                    
# create application
app = Flask(__name__)  # name given in brackets, but providing __name__
                            # is good for single apps, as the name will change
app.config.from_object(__name__)

# Load default config:
#  set username, password, database, key etc
# MAKE SURE DEBUG IS OFF WHEN LIVE OR USERS CAN EXECUTE CODE ON THE SERVER!
app.config.update(dict(
    DATABASE=os.path.join(app.root_path,'blarg.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    ADMIN=True)) ## change this before release!

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
        
#============ Blag Entry Commands ==============================================
# show entries - list newest first (highest id first)
@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, time, text, etime, score, username from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries,\
                        admin=app.config['ADMIN'],username=app.config['USERNAME'])

# add new entry
@app.route('/add',methods=['POST'])
def add_entry():
    if not session.get('logged_in'):    # check if user is logged on
        abort(401)
    etime = time.time()
    timestamp = datetime.datetime.fromtimestamp(etime)\
                .strftime('%Y-%m-%d %H:%M:%S') # timestamp in good format
    db = get_db()
    db.execute('insert into staged (title,text,etime,time,score,username) values (?,?,?,?,?,?)',
                [request.form['title'],request.form['text'],etime,timestamp,0,app.config['USERNAME']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))    # return to entries page

# score board
@app.route('/scoreboard')
def scoreboard():
    db = get_db()
    cur = db.execute('select username,score from accounts order by id desc')
    accs = cur.fetchall()
    cur = db.execute('select username, score from entries order by id desc')
    posts = cur.fetchall()
    
    scores = []    
    
    for acc in accs:
        username = acc['username']
        score = 0
        
        # add up scores for this account
        for post in posts:                  
            if post['username'] == username:
                score += int(post['score'])
        
        # make sure scores are in order
        if len(scores) > 1:
            done = False
            
            for i in range(len(scores)):
                if score < int(scores[i][1]) and done == False:
                    scores.insert(i,[username,str(score)])
                    done = True
                    
            if done == False:
                scores.append([username,str(score)])
        else:
            scores.append([username,str(score)]) 
       
    return render_template('scoreboard.html',scores=scores[::-1],username=app.config['USERNAME'])    
    
#========== login/out commands =================================================
@app.route('/login', methods=['GET','POST'])
def login():   
    error = None
    if request.method == 'POST':
        db = get_db()
        acc = db.execute('select username,password,admin from accounts order by id desc')
        accounts = acc.fetchall()

        for a in accounts:
            if request.form['username'] == a['username'] \
                and request.form['password'] == a['password']:
                        app.config['USERNAME'] = request.form['username']
                        app.config['PASSWORD'] = request.form['password']
                        
                        if a['admin'] == 'true':
                            app.config['ADMIN'] = True
                            flash('You were logged in as admin')
                        else:
                            app.config['ADMIN'] = False
                            flash('You were logged in')
                        session['logged_in'] = True
                        
                        return redirect(url_for('show_entries'))# return to entries if success
        else:
            error = 'Invalid username and password combination'
    return render_template('login.html',error=error,\
                admin=app.config['ADMIN'],username=app.config['USERNAME'])  # else return error
        
    
@app.route('/logout')
def logout():
    session.pop('logged_in',None)
    app.config['ADMIN'] = False
    flash('You were logged out')
    return redirect(url_for('show_entries'))

#=============== Admin user commands ===========================================
# display existing accounts
@app.route('/accounts')
def show_accounts(): 
    if not (session.get('logged_in') and app.config['ADMIN'] == True):    # check if user is logged on
        abort(401)
    db = get_db()
    cur = db.execute('select username,password,admin from accounts order by id desc')
    accounts = cur.fetchall()
    return render_template('show_accounts.html', entries=accounts,\
                    admin=app.config['ADMIN'],username=app.config['USERNAME'])

# add new account
@app.route('/add_account',methods=['POST'])
def add_account():
    if not (session.get('logged_in') and app.config['ADMIN'] == True):    # check if user is logged on
        abort(401)
    db = get_db()
    db.execute('insert into accounts (username,password,admin,score) values (?,?,?,?)',
                [request.form['username'],request.form['password'],request.form['admin'],0])
    db.commit()
    flash('New accounts was successfully added')
    return redirect(url_for('show_accounts'))    # return to entries page

# manually add account        
def add_account_manual(username,password,admin):
    with app.app_context():
        db = get_db()
        db.execute('insert into accounts (username,password,admin, score) values (?,?,?,?)',
                    [username,password,admin,0])
        db.commit() 

# display staged posts        
@app.route('/stage_entries')
def stage_entries():
    db = get_db()
    cur = db.execute('select title, time, text, etime,score,username from staged order by id desc')
    entries = cur.fetchall()
    return render_template('stage_entries.html', entries=entries,\
                        admin=app.config['ADMIN'],username=app.config['USERNAME']) 

# submit or delete staged posts
@app.route('/submit',methods=['POST'])
def submit_staged():
    db = get_db()
    cur = db.execute('select title,text,time,etime, score,username from staged order by id desc')
    staged = cur.fetchall()
    
    for entry in staged:
        keys = request.form.keys()
        
        if 'submit' in keys:
            
            score = request.form['score']
            
            if score == '':
                score = 0
            
            if request.form['submit'] == entry['etime']:
                    selected = entry
                    db.execute('insert into entries (title,text,time,etime,score,username) values (?,?,?,?,?,?)',
                    [selected['title'],selected['text'],selected['time'],selected['etime'],score,selected['username']])
                    flash('Staged entry was successfully posted')

        elif 'delete' in keys:                
            if request.form['delete'] == entry['etime']:
                selected = entry
                db.execute('insert into deleted (title,text,time,etime,score,username) values (?,?,?,?,?,?)',
                [selected['title'],selected['text'],selected['time'],selected['etime'],selected['score'],selected['username']])
                flash('Staged entry was successfully deleted')    
  
    db.execute('delete from staged where etime == (?)',[selected['etime']])
    db.commit()
    return redirect(url_for('stage_entries'))    # return to entries page

# delete submitted posts
@app.route('/delete',methods=['POST']) 
def delete_entry():   
    db = get_db()
    cur = db.execute('select title,text,time,etime,score,username from entries order by id desc')
    entries = cur.fetchall()
  
    for entry in entries:
        if request.form['delete'] == entry['etime']:
                selected = entry
        
    db.execute('insert into deleted (title,text,time,etime,score,username) values (?,?,?,?,?,?)',
                [selected['title'],selected['text'],selected['time'],selected['etime'],selected['score'],selected['username']])
    db.execute('delete from entries where etime == (?)',[selected['etime']])
    db.commit()
    flash('Entry was successfully deleted')      
    return redirect(url_for('show_entries'))    # return to entries page
    
    
#===============================================================================

# run the application if run as standalone app
if __name__ == '__main__':
    app.run()
    
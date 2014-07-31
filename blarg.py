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
    ADMIN=False))

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
    cur = db.execute('select title, time, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries,\
                        admin=app.config['ADMIN'],username=app.config['USERNAME'])

# add new entry
@app.route('/add',methods=['POST'])
def add_entry():
    if not session.get('logged_in'):    # check if user is logged on
        abort(401)
    timestamp = datetime.datetime.fromtimestamp(time.time())\
                .strftime('%Y-%m-%d %H:%M:%S') # timestamp in good format
    db = get_db()
    db.execute('insert into staged (title,text,time) values (?,?,?)',
                [request.form['title'],request.form['text'],timestamp])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))    # return to entries page

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

@app.route('/accounts')
def show_accounts(): 
    if not (session.get('logged_in') and app.config['ADMIN'] == True):    # check if user is logged on
        abort(401)
    db = get_db()
    cur = db.execute('select username,password,admin from accounts order by id desc')
    accounts = cur.fetchall()
    return render_template('show_accounts.html', entries=accounts,\
                    admin=app.config['ADMIN'],username=app.config['USERNAME'])

# add new entry
@app.route('/add_account',methods=['POST'])
def add_account():
    if not (session.get('logged_in') and app.config['ADMIN'] == True):    # check if user is logged on
        abort(401)
    db = get_db()
    db.execute('insert into accounts (username,password,admin) values (?,?,?)',
                [request.form['username'],request.form['password'],request.form['admin']])
    db.commit()
    flash('New accounts was successfully added')
    return redirect(url_for('show_accounts'))    # return to entries page

# delete entry
@app.route('/delete')
def delete_entry():
    if not (session.get('logged_in') and app.config['ADMIN'] == True):     # check if user is logged on
        abort(401)
    db = get_db()
    db.execute('delete from entries where time=(?)',request.form['time'])
    db.commit()
    flash('Entry was successfully deleted')
    return redirect(url_for('show_entries'))    # return to entries page

        
def add_account_manual(username,password,admin):
    with app.app_context():
        db = get_db()
        db.execute('insert into accounts (username,password,admin) values (?,?,?)',
                    [username,password,admin])
        db.commit() 
 
@app.route('/stage_entries')
def stage_entries():
    db = get_db()
    cur = db.execute('select title, time, text from staged order by id desc')
    entries = cur.fetchall()
    return render_template('stage_entries.html', entries=entries,\
                        admin=app.config['ADMIN'],username=app.config['USERNAME']) 
                        
@app.route('/submit')
def submit_staged():
    db = get_db()
    cur = db.execute('select title, time, text from staged order by id desc')
    entries = cur.fetchall()
    db.execute('insert into staged (title,text,time) values (?,?,?)',
                [request.form['title'],request.form['text'],timestamp])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))    # return to entries page
          

#===============================================================================

# run the application if run as standalone app
if __name__ == '__main__':
    app.run()
    
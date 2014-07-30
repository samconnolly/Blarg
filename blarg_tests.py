"""
blarg_tests.py

Created on Tue Jul 29 10:25:31 2014

Author: Sam Connolly

tests to ensure that blarg is working!
"""

import os
import blarg
import unittest
import tempfile

class BlargTestCase(unittest.TestCase):
    
    def setUp(self):
        self.db_fd, blarg.app.config['DATABASE'] = tempfile.mkstemp()
        blarg.app.config['TESTING'] = True
        self.app = blarg.app.test_client()
        blarg.init_db()
        
    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(blarg.app.config['DATABASE'])

    #--------- log in/out scripts ---------------------------------------------- 
    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
            ), follow_redirects=True)
            
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)
     
    #--------- Tests ----------------------------------------------------------- 
    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'No entries here so far' in rv.data 

    def test_login_logout(self):
        rv = self.login('admin', 'default')
        assert 'You were logged in' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login('adminx', 'default')
        assert 'Invalid username' in rv.data
        rv = self.login('admin', 'defaultx')
        assert 'Invalid password' in rv.data
        
    def test_messages(self):                # Test that html is allowed in text
        self.login('admin', 'default')      # but not title
        rv = self.app.post('/add', data=dict(
        title='<Hello>',                            
        text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        assert '&lt;Hello&gt;' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data        


        
if __name__ == '__main__':
    unittest.main()
        


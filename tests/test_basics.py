import unittest
from flask import current_app
from app import create_app, db

class BasicsTestCase(unittest.TestCase):
    #setUp and tearDown methods are called at the beginning and end of each test case class run
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        #Gives tests access to current_app
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
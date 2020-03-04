import unittest
from app.models import User

class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        test_user = User(password = 'dog')
        self.assertTrue(test_user.password_hash is not None)
    
    #Check that password is not readable from db
    def test_no_password_getter(self):
        test_user = User(password='dog')
        with self.assertRaises(AttributeError):
            test_user.password
    
    def test_password_verification(self):
        test_user = User(password='dog')
        self.assertTrue(test_user.verify_password('dog'))
        self.assertFalse(test_user.verify_password('cat'))

    def test_password_salts_are_random(self):
        test_user_1 = User(password='dog')
        test_user_2 = User(password='dog')
        self.assertTrue(test_user_1.password_hash != test_user_2.password_hash)
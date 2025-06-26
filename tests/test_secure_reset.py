import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, users_db
from werkzeug.security import check_password_hash

class TestSecurePasswordReset(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and reset users database"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Reset users database to known state
        users_db.clear()
        from werkzeug.security import generate_password_hash
        users_db['testuser'] = {
            'id': 'test-user-id',
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': generate_password_hash('original_password')
        }
    
    def test_password_reset_requires_current_password(self):
        """Test that password reset now requires current password verification"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'test-user-id'
            sess['username'] = 'testuser'
        
        # Try to reset password without providing current password
        response = self.app.post('/reset-password', data={
            'current_password': '',  # Empty current password
            'new_password': 'new_password',
            'confirm_password': 'new_password'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Current password is incorrect!', response.data)
        
        # Verify password was NOT changed
        user = users_db['testuser']
        self.assertTrue(check_password_hash(user['password_hash'], 'original_password'))
        self.assertFalse(check_password_hash(user['password_hash'], 'new_password'))
        
        print("✅ SECURITY FIX CONFIRMED: Password reset requires current password!")
    
    def test_password_reset_with_wrong_current_password(self):
        """Test that password reset fails with wrong current password"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'test-user-id'
            sess['username'] = 'testuser'
        
        # Try to reset password with wrong current password
        response = self.app.post('/reset-password', data={
            'current_password': 'wrong_password',
            'new_password': 'new_password',
            'confirm_password': 'new_password'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Current password is incorrect!', response.data)
        
        # Verify password was NOT changed
        user = users_db['testuser']
        self.assertTrue(check_password_hash(user['password_hash'], 'original_password'))
        
        print("✅ Security check: Wrong current password is rejected!")
    
    def test_successful_password_reset_with_correct_current_password(self):
        """Test that password reset succeeds with correct current password"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'test-user-id'
            sess['username'] = 'testuser'
        
        # Reset password with correct current password
        response = self.app.post('/reset-password', data={
            'current_password': 'original_password',
            'new_password': 'new_secure_password',
            'confirm_password': 'new_secure_password'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password updated successfully!', response.data)
        
        # Verify password was changed
        user = users_db['testuser']
        self.assertFalse(check_password_hash(user['password_hash'], 'original_password'))
        self.assertTrue(check_password_hash(user['password_hash'], 'new_secure_password'))
        
        print("✅ Password successfully changed with proper verification!")
    
    def test_prevent_password_reuse(self):
        """Test that reusing the same password is prevented"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'test-user-id'
            sess['username'] = 'testuser'
        
        # Try to reset password to the same password
        response = self.app.post('/reset-password', data={
            'current_password': 'original_password',
            'new_password': 'original_password',  # Same as current
            'confirm_password': 'original_password'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New password must be different from current password!', response.data)
        
        print("✅ Password reuse prevention working!")
    
    def test_password_confirmation_still_required(self):
        """Test that password confirmation is still validated"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'test-user-id'
            sess['username'] = 'testuser'
        
        # Try with mismatched passwords
        response = self.app.post('/reset-password', data={
            'current_password': 'original_password',
            'new_password': 'new_password',
            'confirm_password': 'different_password'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New passwords do not match!', response.data)
        
        # Verify password was NOT changed
        user = users_db['testuser']
        self.assertTrue(check_password_hash(user['password_hash'], 'original_password'))
    
    def test_password_length_validation_still_works(self):
        """Test that password length validation still works"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'test-user-id'
            sess['username'] = 'testuser'
        
        # Try with short password
        response = self.app.post('/reset-password', data={
            'current_password': 'original_password',
            'new_password': '123',
            'confirm_password': '123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password must be at least 6 characters long!', response.data)
        
        # Verify password was NOT changed
        user = users_db['testuser']
        self.assertTrue(check_password_hash(user['password_hash'], 'original_password'))
    
    def test_login_still_required(self):
        """Test that login is still required for password reset"""
        response = self.app.get('/reset-password')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        response = self.app.post('/reset-password', data={
            'current_password': 'original_password',
            'new_password': 'new_password',
            'confirm_password': 'new_password'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login

if __name__ == '__main__':
    unittest.main()
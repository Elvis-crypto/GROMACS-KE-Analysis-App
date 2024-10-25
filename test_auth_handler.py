import unittest
import bcrypt
import sqlite3
import os
from auth_handler import initialize_user_db, register_user, login_user, logout_user
import streamlit as st
from unittest.mock import patch

DB_FILE = ':memory:'

@patch('streamlit.session_state', {})
class TestAuthHandler(unittest.TestCase):
    
    def setUp(self):
        # Set up the in-memory database for each test
        self.conn = sqlite3.connect(DB_FILE)
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password TEXT NOT NULL)''')
        self.conn.commit()
        # Reset the session state before each test
        st.session_state = {}

    def tearDown(self):
        # Close the connection after each test
        self.conn.close()

    

    def test_register_user_success(self):
        success, message = register_user('test_user', 'test_password')
        self.assertTrue(success)
        self.assertEqual(message, "User registered successfully.")

    def test_register_user_existing_username(self):
        register_user('test_user', 'test_password')
        success, message = register_user('test_user', 'new_password')
        self.assertFalse(success)
        self.assertEqual(message, "Username already exists.")

    def test_login_user_success(self):
        register_user('test_user', 'test_password')
        success, message = login_user('test_user', 'test_password')
        self.assertTrue(success)
        self.assertEqual(message, "Login successful.")
        self.assertIn('logged_in', st.session_state)
        self.assertIn('username', st.session_state)
        self.assertEqual(st.session_state['username'], 'test_user')

    def test_login_user_wrong_password(self):
        register_user('test_user', 'test_password')
        success, message = login_user('test_user', 'wrong_password')
        self.assertFalse(success)
        self.assertEqual(message, "Incorrect password.")

    def test_login_user_nonexistent(self):
        success, message = login_user('nonexistent_user', 'password')
        self.assertFalse(success)
        self.assertEqual(message, "Username does not exist.")

    def test_logout_user(self):
        register_user('test_user', 'test_password')
        login_user('test_user', 'test_password')
        logout_user()
        self.assertNotIn('logged_in', st.session_state)
        self.assertNotIn('username', st.session_state)

if __name__ == '__main__':
    unittest.main()

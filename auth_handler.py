import bcrypt
import sqlite3
import os
import streamlit as st

# Define the file to store user data
DB_FILE = 'user_data.db'

# Initialize the SQLite database
def initialize_user_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()


    

# Register a new user
def register_user(username, password):
    initialize_user_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if the user already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    if cursor.fetchone() is not None:
        conn.close()
        return False, "Username already exists."
    
    # Hash the password and store it
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()
    
    return True, "User registered successfully."

# Verify user credentials for login
def login_user(username, password):
    initialize_user_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if the user exists
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        return False, "Username does not exist."
    
    hashed_password = result[0].encode('utf-8')
    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        return True, "Login successful."
    else:
        return False, "Incorrect password."

# Logout the current user
def logout_user():
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'username' in st.session_state:
        del st.session_state['username']

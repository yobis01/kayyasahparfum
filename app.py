import streamlit as st
import mysql.connector
from mysql.connector import Error
import os

# Fungsi untuk membuat koneksi ke database MySQL
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='sql12.freemysqlhosting.net',  # Ganti dengan host MySQL Anda
            database='sql12721255',  # Ganti dengan nama database Anda
            user='sql12721255',  # Ganti dengan username MySQL Anda
            password='tXZ7VamWty'  # Ganti dengan password MySQL Anda
        )
    except Error as e:
        st.error(f"The error '{e}' occurred")
    return connection

# Fungsi untuk memeriksa login pengguna
def check_login(username, password):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

# Fungsi untuk mendaftarkan pengguna baru
def register_user(username, password, name, level_akses):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, name, level_akses) VALUES (%s, %s, %s, %s)",
                       (username, password, name, level_akses))
        connection.commit()
        return True
    except Error as e:
        st.error(f"The error '{e}' occurred")
        return False
    finally:
        cursor.close()
        connection.close()

# Halaman Login
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        user = check_login(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user['username']
            st.session_state['name'] = user['name']
            st.session_state['level_akses'] = user['level_akses']
            st.success(f"Welcome {user['name']}!")
            if user['level_akses'] == 'admin':
                os.system('streamlit run admin.py')
            elif user['level_akses'] == 'PemilikToko':
                os.system('streamlit run PemilikToko.py')
        else:
            st.error("Invalid username or password")

# Halaman Daftar
def register():
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    name = st.text_input("Name")
    level_akses = st.selectbox("Level Akses", ["admin", "PemilikToko"])
    if st.button("Register"):
        if register_user(username, password, name, level_akses):
            st.success("User registered successfully")

# Halaman Utama
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        st.sidebar.title(f"Welcome, {st.session_state['name']}")
        st.sidebar.write(f"Level Akses: {st.session_state['level_akses']}")
        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
        st.write("You are logged in!")
        # Tambahkan konten halaman utama di sini
    else:
        page = st.sidebar.selectbox("Choose an option", ["Login", "Register"])
        if page == "Login":
            login()
        elif page == "Register":
            register()

if __name__ == "__main__":
    main()

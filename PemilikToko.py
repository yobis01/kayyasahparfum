# app.py

import streamlit as st
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from mlxtend.frequent_patterns import fpgrowth, association_rules
import joblib
from utils import save_history, save_package, load_model, save_model, fill_missing_dates, save_forecasting_history, save_prediction_history
from config import export_transaksi_produk_to_csv,get_db_connection,create_package_table, create_history_table,export_transaksi_produk_to_excel, fetch_all_packages, fetch_all_history, delete_package, delete_history, update_package, create_forecasting_history_table, create_prediction_history_table, fetch_forecasting_history, fetch_prediction_history,insert_transaksi_produk,fetch_all_transaksi_produk,delete_transaksi_produk,update_transaksi_produk
import io
import xlsxwriter
import os
from mysql.connector import Error
from datetime import datetime
from sklearn.metrics import mean_absolute_error
import plotly.express as px
import matplotlib.pyplot as plt
from PIL import Image

def predict_and_evaluate(model_file, forecast_steps, actual_data):
    model = load_model(model_file)
    forecast = model.forecast(steps=forecast_steps)

    # Menghitung MAE
    mae = mean_absolute_error(actual_data, forecast)

    # Menyimpan prediksi ke dalam database
    save_prediction_history(model_file, forecast)

    return forecast, mae
# Function to plot forecasted values
def plot_forecast(actual_data, forecast_dates, forecast_values):
    plt.figure(figsize=(10, 6))
    plt.plot(forecast_dates, actual_data, label='Actual Data', marker='o')
    plt.plot(forecast_dates, forecast_values, label='Forecasted Values', marker='o')
    plt.title('Forecasted Values vs Actual Data')
    plt.xlabel('Date')
    plt.ylabel('Jumlah Stok')
    plt.legend()
    plt.grid(True)
    return plt
# Function to save history to the database
def save_history(file_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO history (file_name) VALUES (%s)"
    cursor.execute(query, (file_name,))
    conn.commit()
    cursor.close()
    conn.close()

# Function to save package to the database
def save_package(package_name, items, discount):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO Package (package_name, items, discount) VALUES (%s, %s, %s)"
    cursor.execute(query, (package_name, items, discount))
    conn.commit()
    cursor.close()
    conn.close()

def load_data():
    packages_df = fetch_all_packages()
    prediction_history_df = fetch_prediction_history()
    return packages_df, prediction_history_df

# Function to fetch all users from the database
def fetch_all_users():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            cursor.close()
            connection.close()
            return users
    except Error as e:
        st.error(f"Error fetching users: {e}")
        return []

# Function to insert a new user into the database
def insert_user(username, password, name, level_akses):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO users (username, password, name, level_akses, timestamp) VALUES (%s, %s, %s, %s, %s)",
                           (username, password, name, level_akses, current_timestamp))
            connection.commit()
            st.success("User added successfully!")
            cursor.close()
            connection.close()
    except Error as e:
        st.error(f"Error inserting user: {e}")

# Function to update an existing user in the database
def update_user(user_id, username, password, name, level_akses):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET username=%s, password=%s, name=%s, level_akses=%s WHERE id=%s",
                           (username, password, name, level_akses, user_id))
            connection.commit()
            st.success("User updated successfully!")
            cursor.close()
            connection.close()
    except Error as e:
        st.error(f"Error updating user: {e}")

# Function to delete a user from the database
def delete_user(user_id):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
            connection.commit()
            st.success("User deleted successfully!")
            cursor.close()
            connection.close()
    except Error as e:
        st.error(f"Error deleting user: {e}")

# Streamlit UI for CRUD operations
def users_crud():
    # Initialize session_state for selected_user_id
    if 'selected_user_id' not in st.session_state:
        st.session_state.selected_user_id = None

    with st.form("User Form"):
        st.header("Manage Users")

        # Display current users
        users_df = pd.DataFrame(fetch_all_users())
        st.dataframe(users_df)

        # Form inputs
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        name = st.text_input("Name")
        level_akses = st.radio("Access Level", ('admin', 'PemilikToko'))

        add_update_button = st.form_submit_button("Add/Update User")

        if add_update_button:
            if username and password and name:
                if st.session_state.selected_user_id is None:
                    insert_user(username, password, name, level_akses)
                else:
                    update_user(st.session_state.selected_user_id, username, password, name, level_akses)
            else:
                st.warning("Please fill in all fields.")

    # Delete functionality
    st.header("Delete Users")
    selected_rows = st.multiselect("Select users to delete", users_df['id'].tolist())

    if st.button("Delete Selected"):
        for user_id in selected_rows:
            delete_user(user_id)

# Initialize session state variables
if 'model_loaded' not in st.session_state:
    st.session_state['model_loaded'] = False
    st.session_state['basket_sets'] = None
    st.session_state['frequent_itemsets'] = None
    st.session_state['rules'] = None
# Load the image
logo_img = Image.open('image/parfum.png')
# Ensure the package and history tables exist
create_package_table()
create_history_table()
st.image(logo_img, width=200)
st.title("Kayyasah Parfum ")

# Create tabs
tab1,tab2,tab3 = st.tabs(["Dashboard","Laporan","Users"])


with tab1:
    st.header("Dashboard")
    st.write("Selamat datang di Dashboard Kayssah Parfum. Bagian ini akan berisi pelatihan model Asosiasi Menggunakan FP-Growth dan Forecasting Menggunakan Arima.")

    # Load data
    packages_df, prediction_history_df = load_data()

    # Display statistics from 'package' table
    st.subheader("Package Data")
    st.dataframe(packages_df)

    # Bar chart for package discounts
    st.subheader("Statistik Diskon Paket")
    package_discounts = packages_df.groupby('package_name')['discount'].mean()
    plt.bar(package_discounts.index, package_discounts.values)
    plt.xlabel('Nama Paket')
    plt.ylabel('Rata-rata Diskon (%)')
    st.pyplot(plt)

    # Display statistics from 'prediction_history' table
    st.subheader("Prediction History")
    st.dataframe(prediction_history_df)

    

    # Line chart for prediction history
    st.subheader("Statistik Prediksi")
    prediction_history_df['timestamp'] = pd.to_datetime(prediction_history_df['timestamp'])
    prediction_history_df.set_index('timestamp', inplace=True)
    st.line_chart(prediction_history_df['value'])


with tab2:
    st.header("Laporan")

    # Fetch and display package data
    st.subheader("Package Data")
    package_df = fetch_all_packages()
    st.dataframe(package_df)

    # Fetch and display history data
    st.subheader("History Data")
    history_df = fetch_all_history()
    st.dataframe(history_df)

    st.subheader("Forecasting History")
    forecasting_history_df = fetch_forecasting_history()
    st.dataframe(forecasting_history_df)

    st.subheader("Prediction History")
    prediction_history_df = fetch_prediction_history()
    st.dataframe(prediction_history_df)

    st.header("Laporan Barang Paling Laku dan Tidak Laku dari Transaksi")

    # Load data from transaksi_produk table
    transaksi_produk_df = fetch_all_transaksi_produk()

    # Display the raw data
    st.subheader("Data Transaksi Produk")
    st.dataframe(transaksi_produk_df)

    # Aggregate data to find the most popular and unpopular items
    if not transaksi_produk_df.empty:
        # Calculate total Jumlah_Stok per item
        item_sales_summary = transaksi_produk_df.groupby('Nama_Produk')['Jumlah_Stok'].sum().reset_index()

        # Sort by Jumlah_Stok to find most popular and unpopular items
        item_sales_summary = item_sales_summary.sort_values(by='Jumlah_Stok', ascending=False)

        # Most popular items
        st.subheader("Barang Paling Laku")
        st.write(item_sales_summary.head())

        # Least popular items
        st.subheader("Barang Tidak Laku")
        st.write(item_sales_summary.tail())

    else:
        st.warning("Data transaksi belum tersedia.")

    # Delete package
    st.subheader("Delete Package")
    package_id_to_delete = st.number_input("Enter Package ID to Delete", min_value=1, step=1)
    if st.button("Delete Package"):
        delete_package(package_id_to_delete)
        st.success(f"Package with ID {package_id_to_delete} has been deleted.")

    # Delete history
    st.subheader("Delete History")
    history_id_to_delete = st.number_input("Enter History ID to Delete", min_value=1, step=1)
    if st.button("Delete History"):
        delete_history(history_id_to_delete)
        st.success(f"History with ID {history_id_to_delete} has been deleted.")

   

    # Export to Excel
    st.subheader("Export Data")
    if st.button("Export Package Data"):
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        package_df.to_excel(writer, sheet_name='Package Data', index=False)
        writer._save()
        output.seek(0)
        st.download_button(label="Download Excel", data=output, file_name='package_data.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    if st.button("Export History Data"):
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        history_df.to_excel(writer, sheet_name='History Data', index=False)
        writer._save()
        output.seek(0)
        st.download_button(label="Download Excel", data=output, file_name='history_data.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

with tab3:
    st.header("Users")
    users_crud()
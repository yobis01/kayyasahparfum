import pandas as pd
import numpy as np
import pickle
import mysql.connector
from mysql.connector import Error
from config import get_db_connection

def save_model(model, file_name):
    with open(file_name, 'wb') as file:
        pickle.dump(model, file)

def load_model(file_name):
    with open(file_name, 'rb') as file:
        return pickle.load(file)

def fill_missing_dates(df, date_col, value_col):
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.drop_duplicates(subset=[date_col]).set_index(date_col)
    all_dates = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df = df.reindex(all_dates, fill_value=0).rename_axis(date_col).reset_index()
    df = df.rename(columns={'index': date_col})
    return df

def save_forecasting_history(file_name, item_name):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            query = "INSERT INTO forecasting_history (file_name, item_name, timestamp) VALUES (%s, %s, NOW())"
            cursor.execute(query, (file_name, item_name))
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error while saving forecasting history: {e}")

def save_prediction_history(model_file, forecast):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            for idx, value in enumerate(forecast):
                query = "INSERT INTO prediction_history (model_file, step, value, timestamp) VALUES (%s, %s, %s, NOW())"
                cursor.execute(query, (model_file, idx+1, value))
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error while saving prediction history: {e}")

def save_history(file_name):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='yoga',
                                             user='root',
                                             password='')
        if connection.is_connected():
            cursor = connection.cursor()
            query = """INSERT INTO history (file_name, timestamp)
                       VALUES (%s, NOW())"""
            cursor.execute(query, (file_name,))
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")

def save_package(package_name, items, discount):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='yoga',
                                             user='root',
                                             password='')
        if connection.is_connected():
            cursor = connection.cursor()
            query = """INSERT INTO package (package_name, items, discount, timestamp)
                       VALUES (%s, %s, %s, NOW())"""
            cursor.execute(query, (package_name, items, discount))
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")


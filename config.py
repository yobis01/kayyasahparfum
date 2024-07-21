# config.py

import mysql.connector
import pandas as pd
from datetime import datetime
from mysql.connector import Error
import io

def execute_delete_query(query, params):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        cursor.close()
        connection.close()

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="yoga"
    )

def create_package_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Package (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        package_name VARCHAR(255) NOT NULL,
                        items TEXT NOT NULL,
                        discount INT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    cursor.close()
    conn.close()

def create_history_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        file_name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    cursor.close()
    conn.close()

def create_forecasting_history_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute( '''
    CREATE TABLE IF NOT EXISTS forecasting_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        model_name VARCHAR(255),
        item_name VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def create_prediction_history_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute( '''
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        model_name VARCHAR(255),
        forecast JSON,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    
def fetch_all_packages():
    conn = get_db_connection()
    query = "SELECT * FROM Package"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def fetch_all_history():
    conn = get_db_connection()
    query = "SELECT * FROM history"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def delete_package(package_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM Package WHERE id = %s"
    cursor.execute(query, (package_id,))
    conn.commit()
    cursor.close()
    conn.close()

def delete_history(history_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM history WHERE id = %s"
    cursor.execute(query, (history_id,))
    conn.commit()
    cursor.close()
    conn.close()

def update_package(package_id, package_name, items, discount):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE Package SET package_name = %s, items = %s, discount = %s WHERE id = %s"
    cursor.execute(query, (package_name, items, discount, package_id))
    conn.commit()
    cursor.close()
    conn.close()

# Fungsi untuk mengambil data transaksi dari database
def fetch_all_transaksi_produk():
    try:
        connection = get_db_connection()
        if connection:
            query = "SELECT * FROM transaksi_produk"
            transaksi_produk_df = pd.read_sql(query, connection)
            connection.close()
            return transaksi_produk_df
    except Error as e:
        print(f"Error fetching data from MySQL: {e}")
        return pd.DataFrame()
          # Mengubah hasil fetchall() menjadi DataFrame
    except Error as e:
        print(f"Error while fetching transaction data: {e}")
    return pd.DataFrame()  

def fetch_query_results(query):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results
    
def fetch_forecasting_history():
    connection = get_db_connection()
    if connection:
        query = "SELECT * FROM forecasting_history"
        forecasting_history_df = pd.read_sql(query, connection)
        connection.close()
        return forecasting_history_df

def fetch_prediction_history():
    connection = get_db_connection()
    if connection:
        query = "SELECT * FROM prediction_history"
        prediction_history_df = pd.read_sql(query, connection)
        connection.close()
        return prediction_history_df



def insert_transaksi_produk(tanggal_transaksi, nomor_pesanan, nama_produk, jumlah_stok):
    try:
        connection = get_db_connection()  # Mendapatkan koneksi ke database
        if connection:
            cursor = connection.cursor()
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Query SQL untuk memasukkan data
            sql_query = """INSERT INTO transaksi_produk (Tanggal_Transaksi, Nomor_Pesanan, Nama_Produk, Jumlah_Stok, timestamp)
                           VALUES (%s, %s, %s, %s, %s)"""
            
            # Eksekusi query dengan nilai parameter
            cursor.execute(sql_query, (tanggal_transaksi, nomor_pesanan, nama_produk, jumlah_stok, current_timestamp))

            # Commit perubahan ke database
            connection.commit()

            # Tampilkan pesan sukses (opsional)
            print("Data transaksi berhasil ditambahkan ke database!")

    except Error as e:
        print(f"Error while inserting transaction data: {e}")

    except AttributeError as e:
        print(f"Error: No connection found. Connection object is None.")

    finally:
        # Pastikan selalu menutup kursor dan koneksi setelah selesai
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()
            print("Koneksi ke database ditutup.")

def delete_transaksi_produk(transaksi_id):
    query = "DELETE FROM transaksi_produk WHERE id = %s"
    execute_delete_query(query, (transaksi_id,))

def update_transaksi_produk(transaksi_id, tanggal_transaksi, nomor_pesanan, nama_produk,jumlah_stok):
    query = """
    UPDATE transaksi_produk
    SET Tanggal_Transaksi = %s, Nomor_Pesanan = %s, Nama_Produk = %s, Jumlah_Stok = %s
    WHERE id = %s
    """
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(query, (tanggal_transaksi, nomor_pesanan, nama_produk, transaksi_id,jumlah_stok))
        connection.commit()
        cursor.close()
        connection.close()

# Fungsi untuk mengambil data transaksi dan menulisnya ke file Excel
def export_transaksi_produk_to_excel(dataframe):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    dataframe.to_excel(writer, sheet_name='Transaksi Produk', index=False)
    writer._save()
    processed_data = output.getvalue()
    return processed_data



    # Jika ada data transaksi, tulis ke file Excel
    if not transaksi_produk_df.empty:
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        transaksi_produk_df.to_excel(writer, sheet_name='Transaksi Produk', index=False)
        writer._save()  # Memastikan untuk menyimpan file Excel
        excel_data = output.getvalue()
        return excel_data

    # Jika ada data transaksi, tulis ke file Excel
    if not transaksi_produk_df.empty:
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        transaksi_produk_df.to_excel(writer, sheet_name='Transaksi Produk', index=False)
        writer.save()
        excel_data = output.getvalue()
        return excel_data

    return None

def export_transaksi_produk_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode('utf-8')

def fill_missing_dates(df, date_col, value_col):
    df.set_index(date_col, inplace=True)
    df = df.asfreq('D', fill_value=0)
    df.reset_index(inplace=True)
    return df


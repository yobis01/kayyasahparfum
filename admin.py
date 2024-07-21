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

def predict_and_evaluate(model_file, steps, actual_data):
    model = load_model(model_file)
    forecast = model.forecast(steps)
    mae = (abs(forecast - actual_data)).mean()
    return forecast, mae

def plot_forecast(train_data, actual_data, forecast_dates, forecast):
    plt.figure(figsize=(14, 7))
    plt.plot(train_data['Tanggal_Transaksi'], train_data['Jumlah_Stok'], label='Data Train')
    plt.plot(forecast_dates, forecast, label='Prediksi')
    plt.plot(forecast_dates, actual_data, label='Data Aktual')
    plt.fill_between(forecast_dates, actual_data, forecast, color='gray', alpha=0.2)
    plt.title('Prediksi Stok Produk')
    plt.xlabel('Tanggal')
    plt.ylabel('Jumlah Stok')
    plt.legend()
    plt.grid()
    return plt

def plot_train_data(data, date_col, value_col):
    plt.figure(figsize=(10, 6))
    plt.plot(data[date_col], data[value_col], label='Jumlah Stok')
    plt.title('Data Train Jumlah Stok Produk')
    plt.xlabel('Tanggal')
    plt.ylabel('Jumlah Stok')
    plt.legend()
    plt.grid()
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
tab1, tab2, tab3, tab4, tab5,tab6,tab7 = st.tabs(["Dashboard","Model Training", "Pemaketan Barang", "Data Transaksi",  "Forecasting","Laporan","Users"])


with tab1:
    st.header("Dashboard")
    st.write("Selamat datang di Dashboard Kayssah Parfum. Bagian ini akan berisi pelatihan model Asosiasi Menggunakan FP-Growth dan Forecasting Menggunakan Arima.")

    # Load data
    packages_df, prediction_history_df = load_data()

    # Display statistics from 'package' table
    st.subheader("Data Paket")
    st.markdown("Tabel ini menampilkan informasi mengenai paket barang, termasuk nama paket, item dalam paket, dan diskon yang diberikan.")
    st.dataframe(packages_df)

    # Bar chart for package discounts
    st.subheader("Statistik Diskon Paket")
    st.markdown("Grafik ini menunjukkan rata-rata diskon untuk setiap paket yang tersedia.")
    package_discounts = packages_df.groupby('package_name')['discount'].mean()

    fig, ax = plt.subplots()
    ax.bar(package_discounts.index, package_discounts.values)
    ax.set_xlabel('Nama Paket')
    ax.set_ylabel('Rata-rata Diskon (%)')
    ax.set_title('Rata-rata Diskon per Paket')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig)

    # Display statistics from 'prediction_history' table
    st.subheader("Riwayat Prediksi")
    st.markdown("Tabel ini menampilkan riwayat prediksi yang telah dilakukan sebelumnya, termasuk nilai prediksi dan timestamp.")
    st.dataframe(prediction_history_df)

    # Line chart for prediction history
    st.subheader("Statistik Prediksi")
    st.markdown("Grafik ini menunjukkan perkembangan nilai prediksi dari waktu ke waktu.")
    prediction_history_df['timestamp'] = pd.to_datetime(prediction_history_df['timestamp'])
    prediction_history_df.set_index('timestamp', inplace=True)

    fig, ax = plt.subplots()
    ax.plot(prediction_history_df.index, prediction_history_df['value'])
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Nilai Prediksi')
    ax.set_title('Perkembangan Nilai Prediksi')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig)

with tab2:
    st.header("Pelatihan Model")
    uploaded_file = st.file_uploader("Pilih file CSV", type="csv")

    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        st.write("### Data Mentah")
        st.write(data.head())

        basket = (data.groupby(['Id_Pemesanan', 'Nama_barang'])['Nama_barang']
                .count().unstack().reset_index().fillna(0).set_index('Id_Pemesanan'))
        basket_sets = basket.applymap(lambda x: 1 if x >= 1 else 0)
        st.write("### Set Keranjang")
        st.markdown("Tabel ini menunjukkan dataset transaksional di mana setiap baris mewakili pesanan yang berbeda dan setiap kolom mewakili produk unik. Nilai 1 menunjukkan bahwa produk tersebut termasuk dalam pesanan, sedangkan nilai 0 menunjukkan bahwa produk tersebut tidak termasuk dalam pesanan.")
        st.write(basket_sets.head())

        min_support = st.slider("Pilih dukungan minimum", 0.01, 0.5, 0.01)
        frequent_itemsets = fpgrowth(basket_sets, min_support=min_support, use_colnames=True)
        frequent_itemsets['support_count'] = frequent_itemsets['support'] * len(basket_sets)

        # Ubah frozenset menjadi list untuk serialisasi JSON
        frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(list)

        st.write("### Itemset Frequent")
        st.markdown("Tabel ini menampilkan itemset yang sering ditemukan dalam dataset, beserta jumlah dukungannya. Dukungan mewakili proporsi transaksi yang mengandung itemset tersebut.")
        st.write(frequent_itemsets)

        min_threshold = st.slider("Pilih ambang batas lift minimum", 1.0, 5.0, 1.0)
        rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_threshold)
        rules = rules.assign(support_count=rules['support'] * len(basket_sets))

        st.write("### Aturan Asosiasi")
        st.markdown("Tabel ini berisi aturan asosiasi yang dihasilkan dari itemset frequent. Setiap aturan dievaluasi berdasarkan metrik seperti dukungan, kepercayaan, dan lift.")
        st.write(rules)

        fig_rules = px.scatter(rules, x='confidence', y='lift', size='support', color='support', 
                            title='Aturan Asosiasi', labels={'confidence':'Kepercayaan', 'lift':'Lift', 'support':'Dukungan'})
        st.plotly_chart(fig_rules)

        confidence_threshold = st.slider("Pilih kepercayaan minimum", 0.0, 1.0, 0.7)
        filtered_rules = rules[rules['confidence'] > confidence_threshold]

        st.write("### Aturan yang Difilter")
        st.markdown("Tabel ini menunjukkan aturan asosiasi yang memenuhi ambang batas kepercayaan yang ditentukan. Kepercayaan yang lebih tinggi menunjukkan aturan yang lebih kuat.")
        st.write(filtered_rules)

        if st.button("Simpan Model"):
            file_name = 'association_rules_model.pkl'
            joblib.dump((basket_sets, frequent_itemsets, rules), file_name)
            save_history(file_name)
            st.success("Model disimpan dan riwayat dicatat!")

with tab3:
    st.header("Pemaketan Barang")

    if st.button("Load Saved Model"):
        model = joblib.load('association_rules_model.pkl')
        st.session_state['basket_sets'], st.session_state['frequent_itemsets'], st.session_state['rules'] = model
        st.session_state['model_loaded'] = True
        st.success("Model berhasil dimuat!")

    if st.session_state.get('model_loaded', False):
        frequent_itemsets = st.session_state['frequent_itemsets']
        rules = st.session_state['rules']

        st.write("### Frequent Itemsets")
        st.markdown("Tabel ini menunjukkan itemset-itemset yang sering muncul bersama dalam data penjualan. "
                    "Kolom `support` menunjukkan frekuensi relatif itemset dalam data.")
        st.write(frequent_itemsets)

        st.write("### Association Rules")
        st.markdown("Tabel ini menunjukkan aturan asosiasi yang ditemukan dari itemset-itemset yang sering muncul. "
                    "Kolom `antecedents` dan `consequents` menunjukkan item-item dalam aturan, sementara "
                    "`support`, `confidence`, dan `lift` memberikan metrik untuk mengevaluasi kekuatan aturan tersebut.")
        st.write(rules)

        # Create packaging logic
        st.write("### Buat Paket dan Diskon")
        st.markdown("Bagian ini memungkinkan Anda membuat paket barang berdasarkan itemset yang sering muncul. "
                    "Anda bisa memberi nama paket, memilih item-item yang akan dimasukkan ke dalam paket, "
                    "dan menentukan diskon untuk paket tersebut.")
        package_name = st.text_input("Nama Paket")
        selected_items = st.multiselect("Pilih Item untuk Paket", frequent_itemsets['itemsets'].apply(lambda x: ', '.join(list(x))))

        discount = st.slider("Pilih Diskon (%)", 0, 100, 10)

        if st.button("Buat Paket"):
            if package_name and selected_items:
                items = ', '.join(selected_items)
                save_package(package_name, items, discount)
                st.success(f"Paket '{package_name}' dibuat dengan item: {selected_items} dan diskon: {discount}%")
            else:
                st.error("Silakan masukkan nama paket dan pilih item.")
    else:
        st.warning("Silakan muat model yang disimpan untuk membuat paket.")
with tab4:
    st.header("Data Transaksi")

    # Menu buttons
    menu = st.radio(
    'Menu',
    ['Data Transaksi', 'Tambah Transaksi', 'Hapus Transaksi', 'Update Transaksi']
    )

    # Main content based on menu selection
    if menu == 'Tambah Transaksi':
        st.header("Tambah Transaksi Produk")
        tambah_tanggal_transaksi = st.date_input("Tanggal Transaksi")
        tambah_nomor_pesanan = st.text_input("Nomor Pesanan")
        tambah_nama_produk = st.text_input("Nama Produk")
        tambah_jumlah_stok = st.number_input("Jumlah Stok", min_value=1)

        # File upload for additional data
        uploaded_file = st.file_uploader("Unggah file CSV untuk tambahan transaksi", type=['csv'])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                for index, row in df.iterrows():
                    insert_transaksi_produk(row['Tanggal_Transaksi'], row['Nomor_Pesanan'], row['Nama_Produk'], row['Jumlah_Stok'])
                st.success("Transaksi dari file CSV berhasil ditambahkan.")
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.button("Tambah"):
            insert_transaksi_produk(tambah_tanggal_transaksi, tambah_nomor_pesanan, tambah_nama_produk, tambah_jumlah_stok)
            st.success("Transaksi berhasil ditambahkan.")

    elif menu == 'Hapus Transaksi':
        st.header("Hapus Transaksi Produk")
        transaksi_produk_df = fetch_all_transaksi_produk()
        transaksi_id_to_delete = st.selectbox("Pilih ID Transaksi untuk dihapus", transaksi_produk_df['id'])

        if st.button("Hapus"):
            delete_transaksi_produk(transaksi_id_to_delete)
            st.success(f"Transaksi dengan ID {transaksi_id_to_delete} telah dihapus.")

    elif menu == 'Update Transaksi':
        st.header("Update Transaksi Produk")
        transaksi_produk_df = fetch_all_transaksi_produk()
        transaksi_id_to_update = st.selectbox("Pilih ID Transaksi untuk diperbarui", transaksi_produk_df['id'])

        updated_tanggal_transaksi = st.date_input("Tanggal Transaksi yang Diperbarui", value=pd.to_datetime(transaksi_produk_df[transaksi_produk_df['id'] == transaksi_id_to_update]['Tanggal_Transaksi'].iloc[0]))
        updated_nomor_pesanan = st.text_input("Nomor Pesanan yang Diperbarui", value=transaksi_produk_df[transaksi_produk_df['id'] == transaksi_id_to_update]['Nomor_Pesanan'].iloc[0])
        updated_nama_produk = st.text_input("Nama Produk yang Diperbarui", value=transaksi_produk_df[transaksi_produk_df['id'] == transaksi_id_to_update]['Nama_Produk'].iloc[0])
        updated_jumlah_stok = st.number_input("Jumlah Stok yang Diperbarui", value=transaksi_produk_df[transaksi_produk_df['id'] == transaksi_id_to_update]['Jumlah_Stok'].iloc[0], min_value=1)

        if st.button("Perbarui"):
            update_transaksi_produk(transaksi_id_to_update, updated_tanggal_transaksi, updated_nomor_pesanan, updated_nama_produk, updated_jumlah_stok)
            st.success(f"Transaksi dengan ID {transaksi_id_to_update} telah diperbarui.")

    else:
        # Display all transaction data
        st.header("Data Transaksi Produk")
        transaksi_produk_df = fetch_all_transaksi_produk()

        # Filter by Nama Produk
        produk_list = transaksi_produk_df['Nama_Produk'].unique()
        selected_produk = st.selectbox("Filter berdasarkan Nama Produk", produk_list)

        filtered_df = transaksi_produk_df[transaksi_produk_df['Nama_Produk'] == selected_produk]
        st.dataframe(filtered_df)

        # Informasi Stok
        st.header("Informasi Stok")
        if not filtered_df.empty:
            stok_info_df = filtered_df.groupby(['Tanggal_Transaksi', 'Nama_Produk']).agg({'Jumlah_Stok': 'sum'}).reset_index()
            st.dataframe(stok_info_df)

            # Download buttons for Excel and CSV
            excel_data = export_transaksi_produk_to_excel(stok_info_df)
            st.download_button(
                label="Download Data Transaksi Excel",
                data=excel_data,
                file_name='transaksi_produk_filtered.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            csv_data = export_transaksi_produk_to_csv(stok_info_df)
            st.download_button(
                label="Download Data Transaksi CSV",
                data=csv_data,
                file_name='transaksi_produk_filtered.csv',
                mime='text/csv'
            )

        elif menu == 'Hapus Transaksi':
            st.header("Hapus Transaksi Produk")
            transaksi_id_to_delete = st.number_input("Masukkan ID Transaksi untuk dihapus", min_value=1, step=1)
            if st.button("Hapus"):
                delete_transaksi_produk(transaksi_id_to_delete)
                st.success(f"Transaksi dengan ID {transaksi_id_to_delete} telah dihapus.")

        elif menu == 'Update Transaksi':
            st.header("Update Transaksi Produk")
            transaksi_id_to_update = st.number_input("Masukkan ID Transaksi untuk diperbarui", min_value=1, step=1)
            updated_tanggal_transaksi = st.date_input("Tanggal Transaksi yang Diperbarui")
            updated_nomor_pesanan = st.text_input("Nomor Pesanan yang Diperbarui")
            updated_nama_produk = st.text_input("Nama Produk yang Diperbarui")
            updated_jumlah_stok = st.number_input("Jumlah Stok yang Diperbarui", min_value=1)

            if st.button("Perbarui"):
                update_transaksi_produk(transaksi_id_to_update, updated_tanggal_transaksi, updated_nomor_pesanan, updated_nama_produk, updated_jumlah_stok)
                st.success(f"Transaksi dengan ID {transaksi_id_to_update} telah diperbarui.")




with tab5:
    st.header("Prediksi")

    uploaded_file = st.file_uploader("Pilih file CSV untuk Prediksi", type="csv")

    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        st.write("### Data Mentah")
        st.write(data.head())

        item_name = st.selectbox("Pilih Nama Produk", data["Nama_Produk"].unique())

        item_data = data[data["Nama_Produk"] == item_name]
        item_data['Tanggal_Transaksi'] = pd.to_datetime(item_data['Tanggal_Transaksi'])
        item_data = fill_missing_dates(item_data, 'Tanggal_Transaksi', 'Jumlah_Stok')

        st.write("### Data Produk dengan Tanggal yang Terisi")
        st.markdown("Tabel ini menunjukkan data produk yang telah diisi tanggal-tanggal yang hilang dengan jumlah stok yang diisi dengan nilai nol jika tidak ada transaksi pada tanggal tersebut.")
        st.write(item_data)

        st.write("### Grafik Data Train")
        st.markdown("Grafik ini menunjukkan jumlah stok produk dari waktu ke waktu berdasarkan data train.")
        plt_train = plot_train_data(item_data, 'Tanggal_Transaksi', 'Jumlah_Stok')
        st.pyplot(plt_train)

        order = (st.number_input("Order (p = Order dari Autoregression)", min_value=0), 
                st.number_input("Order (d = Order dari Differencing)", min_value=0), 
                st.number_input("Order (q = Order dari Moving Average)", min_value=0))

        if st.button("Latih Model"):
            model = ARIMA(item_data['Jumlah_Stok'], order=order)
            model_fit = model.fit()
            file_name = f'arima_model_{item_name}.pkl'
            save_model(model_fit, file_name)
            save_forecasting_history(file_name, item_name)
            st.success(f"Model dilatih dan disimpan sebagai {file_name}!")

    model_files = [f for f in os.listdir() if f.startswith('arima_model_') and f.endswith('.pkl')]
    selected_model_file = st.selectbox("Pilih Model yang Telah Dilatih", model_files)
    forecast_steps = st.number_input("Jumlah Langkah untuk Prediksi", min_value=1, step=1)

    if st.button("Prediksi"):
        model = load_model(selected_model_file)
        forecast_dates = pd.date_range(start=item_data['Tanggal_Transaksi'].max(), periods=forecast_steps + 1)[1:]
        actual_data = item_data['Jumlah_Stok'].values[-forecast_steps:]
        forecast, mae = predict_and_evaluate(selected_model_file, forecast_steps, actual_data)

        st.write("### Nilai Prediksi")
        st.markdown("Tabel ini menampilkan nilai hasil Prediksi jumlah stok produk untuk beberapa langkah ke depan.")
        forecast_df = pd.DataFrame({'Tanggal': forecast_dates, 'Nilai Prediksi': forecast})
        st.write(forecast_df)
        st.success("Prediksi selesai dan riwayat dicatat!")

       
        st.subheader("Metrik Evaluasi")
        st.write(f"Mean Absolute Error (MAE): {mae}")

        st.subheader("Grafik Prediksi vs Data Aktual")
        st.markdown("Grafik ini menunjukkan perbandingan antara nilai Prediksi dan data aktual jumlah stok produk.")
        plt = plot_forecast(item_data, actual_data, forecast_dates, forecast)
        st.pyplot(plt)
        for i, row in forecast_df.iterrows():
            st.write(f"Tanggal {row['Tanggal']}: Jumlah stok diperkirakan adalah {row['Nilai Prediksi']}.")


    st.subheader("Riwayat Prediksi")
    forecasting_history_df = fetch_forecasting_history()
    st.markdown("Tabel ini menunjukkan riwayat Prediksi yang telah dilakukan sebelumnya.")
    st.dataframe(forecasting_history_df)

    st.subheader("Riwayat Prediksi")
    prediction_history_df = fetch_prediction_history()
    st.markdown("Tabel ini menunjukkan riwayat prediksi yang telah dilakukan sebelumnya.")
    st.dataframe(prediction_history_df)

with tab6:
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

   
with tab7:
    st.header("Users")
    users_crud()
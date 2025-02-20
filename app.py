import streamlit as st
import sqlite3
import requests
from datetime import datetime
import pandas as pd
from dotenv import dotenv_values

# Ustawienia dla API pogodowego

env = dotenv_values(".env")
### Secrets using Streamlit Cloud Mechanism
# https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
if 'API_KEY' in st.secrets:
    env['API_KEY'] = st.secrets['API_KEY']
###

WEATHER_API_URL = f'http://api.openweathermap.org/data/2.5/weather?q=Poznan&appid={API_KEY}'
FORECAST_API_URL = f'http://api.openweathermap.org/data/2.5/forecast?q=Poznan&appid={API_KEY}'

# Funkcja do pobierania danych pogodowych
def fetch_weather_data():
    weather_response = requests.get(WEATHER_API_URL)
    forecast_response = requests.get(FORECAST_API_URL)
    return weather_response.json(), forecast_response.json()

# Funkcja do tworzenia bazy danych i tabeli
def create_database():
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temperature REAL,
            description TEXT,
            pressure INTEGER,
            humidity INTEGER,
            wind_speed REAL,
            wind_direction INTEGER,
            cloudiness INTEGER,
            sunrise TEXT,
            sunset TEXT,
            latitude REAL,
            longitude REAL,
            city TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            forecast TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            alert TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Funkcja do zapisywania danych do bazy
def save_data(weather_data, forecast_data):
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    main = weather_data['main']
    wind = weather_data['wind']
    sys = weather_data['sys']
    coord = weather_data['coord']

    temperature_celsius = main['temp'] - 273.15
    pressure = main.get('pressure', None)
    humidity = main.get('humidity', None)
    wind_speed = wind.get('speed', None)
    wind_direction = wind.get('deg', None)
    cloudiness = weather_data.get('clouds', {}).get('all', None)
    sunrise = datetime.fromtimestamp(sys['sunrise']).strftime('%Y-%m-%d %H:%M:%S')
    sunset = datetime.fromtimestamp(sys['sunset']).strftime('%Y-%m-%d %H:%M:%S')
    latitude = coord.get('lat', None)
    longitude = coord.get('lon', None)
    city = weather_data['name']
    description = weather_data['weather'][0]['description']

    c.execute('INSERT INTO weather (timestamp, temperature, description, pressure, humidity, wind_speed, wind_direction, cloudiness, sunrise, sunset, latitude, longitude, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              (timestamp, temperature_celsius, description, pressure, humidity, wind_speed, wind_direction, cloudiness, sunrise, sunset, latitude, longitude, city))

    # Save forecast data
    forecast_text = str(forecast_data)  # For simplicity, saving the entire JSON as string here
    c.execute('INSERT INTO forecasts (timestamp, forecast) VALUES (?, ?)', (timestamp, forecast_text))

    # Potential alert handling
    if 'alerts' in forecast_data:
        for alert in forecast_data['alerts']:
            alert_text = alert.get('description', 'Alert bez opisu')
            c.execute('INSERT INTO alerts (timestamp, alert) VALUES (?, ?)', (timestamp, alert_text))

    conn.commit()
    conn.close()

# Uruchom raz przy starcie aplikacji, aby stworzyć bazę
# create_database()

# Opcje aplikacji w Streamlit
st.title('Aplikacja pogodowa')

# Dodanie przycisku do ręcznego pobierania danych
if st.button('Pobierz i zapisz dane pogodowe'):
    weather_data, forecast_data = fetch_weather_data()
    save_data(weather_data, forecast_data)
    st.success("Dane zostały zapisane pomyślnie!")

# Widok tabeli z rekordami
# def view_data():
#    conn = sqlite3.connect('weather_data.db')
#    c = conn.cursor()
#    c.execute('SELECT * FROM weather ORDER BY timestamp DESC')
#    data = c.fetchall()
#    conn.close()
#    if data:
#        st.write("Wszystkie dane pogodowe:")
#        st.table(data)
#    else:
#        st.write("Brak danych w bazie.")

def view_data():
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()

    # Pobierz nazwy kolumn z tabeli weather
    c.execute('PRAGMA table_info(weather)')
    column_info = c.fetchall()
    column_names = [info[1] for info in column_info]

    # Pobierz dane z tabeli weather
    c.execute('SELECT * FROM weather ORDER BY timestamp DESC')
    data = c.fetchall()
    conn.close()

    if data:
        st.write("Wszystkie dane pogodowe:")
        st.table(pd.DataFrame(data, columns=column_names))
    else:
        st.write("Brak danych w bazie.")

# Widok pojedynczego rekordu z nawigacją
def view_single_record():
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM weather')
    total_records = c.fetchone()[0]

    if 'record_index' not in st.session_state:
        st.session_state.record_index = 0

    if total_records > 0:
        c.execute('SELECT * FROM weather ORDER BY timestamp DESC LIMIT 1 OFFSET ?', (st.session_state.record_index,))
        record = c.fetchone()
        if record:
            st.write(f"Rekord: {st.session_state.record_index + 1}/{total_records}")
            st.write(f"Data i godzina: {record[1]}")
            # st.write(f"Temperatura: {record[2]} °C")
            st.write(f"Temperatura: {record[2]:.2f} °C")
            st.write(f"Opis: {record[3]}")
            st.write(f"Ciśnienie: {record[4]} hPa")
            st.write(f"Wilgotność: {record[5]} %")
            st.write(f"Prędkość wiatru: {record[6]} m/s")
            st.write(f"Kierunek wiatru: {record[7]}°")
            st.write(f"Zachmurzenie: {record[8]} %")
            st.write(f"Wschód słońca: {record[9]}")
            st.write(f"Zachód słońca: {record[10]}")
            st.write(f"Szerokość geograficzna: {record[11]}")
            st.write(f"Długość geograficzna: {record[12]}")
            st.write(f"Miasto: {record[13]}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button('Poprzedni'):
                    if st.session_state.record_index > 0:
                        st.session_state.record_index -= 1
            with col2:
                if st.button('Następny'):
                    if st.session_state.record_index < total_records - 1:
                        st.session_state.record_index += 1

    conn.close()

# Interfejs wyboru widoku
option = st.selectbox("Wybierz widok", ["Tabela", "Pojedynczy rekord"])

if option == "Tabela":
    view_data()
elif option == "Pojedynczy rekord":
    view_single_record()
import datetime
import time
from flask import Flask, render_template, request
from alpha_vantage.timeseries import TimeSeries
import requests
import psycopg2
import yfinance as yf
import datetime
import pandas as pd

def create_database():


    try:
        # Opret forbindelse til default "postgres" database for at oprette en ny database
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="financeFun",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True

        # Opret en cursor til at udføre SQL-kommandoer
        cur = conn.cursor()

        # Opret en ny database med navnet "financeDatabase"
        cur.execute("CREATE DATABASE financeDatabase")

        print("Database 'financeDatabase' oprettet succesfuldt!")

    except psycopg2.errors.DuplicateDatabase:
        print("Database 'financeDatabase' eksisterer allerede.")

    except psycopg2.Error as e:
        print("Fejl under oprettelse af database:", e)

    finally:
        # Luk cursor og forbindelse
        if 'cur' in locals():
            cur.close()
        conn.close()

def create_table():
    try:
        # Opret forbindelse til "financeDatabase"
        conn = psycopg2.connect(
            dbname="financedatabase",
            user="postgres",
            password="financeFun",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True

        # Opret en cursor til at udføre SQL-kommandoer
        cur = conn.cursor()

        # Eksempel: Opret en tabel
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                date DATE,
                pe integer
            )
        """)

        print("Tabel 'users' oprettet succesfuldt!")

    except psycopg2.Error as e:
        print("Fejl under oprettelse af tabel:", e)

    finally:
        # Luk cursor og forbindelse
        if 'cur' in locals():
            cur.close()
        conn.close()

def truncate_table():

        try:
            # Connect to the database
            conn = psycopg2.connect(
                dbname="financedatabase",
                user="postgres",
                password="financeFun",
                host="localhost",
                port="5432"
            )
            conn.autocommit = True

            # Create a cursor
            cur = conn.cursor()

            # Truncate the table
            cur.execute(f"TRUNCATE TABLE {'stock'}")

            print(f"Table '{'stock'}' truncated successfully!")

        except psycopg2.Error as e:
            print(f"Error truncating table: {e}")

        finally:
            # Close cursor and connection
            if 'cur' in locals():
                cur.close()
            conn.close()

def insert_value(pe_values):
    try:
        # Opret forbindelse til "financeDatabase"
        conn = psycopg2.connect(
            dbname="financedatabase",
            user="postgres",
            password="financeFun",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True

        # Opret en cursor til at udføre SQL-kommandoer
        cur = conn.cursor()

        # Eksempel: Indsæt en værdi i tabellen
        for date, pe in pe_values.items():
            cur.execute("INSERT INTO stock (date, PE) VALUES (%s, %s)", (date, int(pe)))

        print("Værdi indsat succesfuldt!")

    except psycopg2.Error as e:
        print("Fejl under indsættelse af værdi:", e)

    finally:
        # Luk cursor og forbindelse
        if 'cur' in locals():
            cur.close()
        conn.close()



def fetch_historical_pe(symbol):
    # Hent dagens dato og datoen for en måned siden
    today = datetime.datetime.now()
    last_month = today - datetime.timedelta(days=30)

    # Hent daglige aktiekurser fra Yahoo Finance
    stock_data = yf.download(symbol, start=last_month.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))

    df=yf.Ticker(symbol).financials
    # Beregn daglige P/E-ratioer
    pe_values = {}
    first_diluted_eps = df.axes.copy()
    rerr = first_diluted_eps[0].to_list()
    for i, label in enumerate(rerr):
        if label == 'Diluted EPS':
            diluted_eps_index = i
            break  # Stop iterating once you find 'Diluted EPS'

    #   Access the value using the index (if found)
    if 'diluted_eps_index' in locals():  # Check if index was found
        diluted_eps_value = df.values[diluted_eps_index][0]  # Access the entire row for 'Diluted EPS'
    # You can then access specific columns within the row (e.g., value for 'Diluted EPS')
    else:
        print("Diluted EPS not found in the index")



    for date, row in stock_data.iterrows():
        pe_values[date.strftime('%Y-%m-%d')] = row['Close'] / diluted_eps_value

    insert_value(pe_values)



app = Flask(__name__)


# Replace 'YOUR_API_KEY' with your actual Alpha Vantage API key
API_KEY = 'YOUR_API_KEY'

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stock', methods=['POST'])
def stock():
    symbol = request.form['symbol']

    today = datetime.datetime.now()

    fetch_historical_pe(symbol)

    # Focus on the most recent data point (assuming daily data)
    # Adjust 'Close' if you need a different closing price metric
    latest_price = yf.download(symbol, start=today.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))['Close'].iloc[-1]

    # Optional: You can create a dictionary if you want more data
    # data_with_price = {"symbol": symbol, "latest_price": latest_price}
    list_with_t = [str(latest_price)]


    return render_template('index.html', data=list_with_t)

@app.route('/refresh', methods=['POST'])
def refresh():
    truncate_table()
    return render_template('index.html', data=None)


if __name__ == '__main__':

    create_database()
    create_table()

    app.run(debug=True)
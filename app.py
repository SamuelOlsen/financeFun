import datetime
import time
from flask import Flask, render_template, request
from alpha_vantage.timeseries import TimeSeries
import requests
import psycopg2
import yfinance as yf
import datetime


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



def fetch_historical_pe(symbol, annual_eps):
    # Hent dagens dato og datoen for en måned siden
    today = datetime.datetime.now()
    last_month = today - datetime.timedelta(days=30)

    # Hent daglige aktiekurser fra Yahoo Finance
    stock_data = yf.download(symbol, start=last_month.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))

    # Beregn daglige P/E-ratioer
    pe_values = {}
    for date, row in stock_data.iterrows():
        pe_values[date.strftime('%Y-%m-%d')] = row['Close'] / annual_eps

    return pe_values





app = Flask(__name__)


# Replace 'YOUR_API_KEY' with your actual Alpha Vantage API key
API_KEY = 'YOUR_API_KEY'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stock', methods=['POST'])
def stock():
    symbol = request.form['symbol']
    # URL til Alpha Vantage API
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"

    # Send anmodningen til API'et
    response = requests.get(url)
    data = response.json()

    # Kontrollér om der er returneret data og udtræk P/E ratio
    if 'PERatio' in data:
        pe_ratio = data['PERatio']
    else:
        return "P/E ratio not found for the given symbol."

    print(pe_ratio)

    """
    symbol = request.form['symbol']
    ts = TimeSeries(key=API_KEY, output_format='json')
    data, meta_data = ts.get_quote_endpoint(symbol)
    """
    return render_template('index.html', data=data)

if __name__ == '__main__':
    create_database()
    create_table()

# Antag en EPS (dette bør justeres baseret på aktuel data)
annual_eps = 5.00

pe_values = fetch_historical_pe('AAPL', annual_eps)

insert_value(pe_values)

app.run(debug=True)
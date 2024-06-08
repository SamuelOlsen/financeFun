import datetime
import time
from flask import Flask, render_template, request
from alpha_vantage.timeseries import TimeSeries
import requests
import psycopg2
import yfinance as yf
import datetime
import pandas as pd
import re

# Declare eps as a global variable
eps = None
late = None

def database_connection():
    try:
    # Opret forbindelse til default "postgres" database for at oprette en ny database
        conn = psycopg2.connect(
            dbname="financedatabase",
            user="postgres",
            password="UIS",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
        return None

def create_database():
    try:
        conn = database_connection()
        if conn is None:
            return

        # Cursor for SQL commands
        cur = conn.cursor()
        # Create new database
        cur.execute("CREATE DATABASE financeDatabase")
        print("Database 'financeDatabase' created succesfully!")

    except psycopg2.errors.DuplicateDatabase:
        print("Database 'financeDatabase' already exists.")
    except psycopg2.Error as e:
        print("Error while creating database: ", e)

    finally:
        # Close cursor and connection
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def create_table():
    try:
        conn = database_connection()
        if conn is None:
            return

        cur = conn.cursor()
        # Example: Create table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                date DATE,
                pe integer
            )
        """)

        print("Table 'users' created succesfully!")

    except psycopg2.Error as e:
        print("Error while creating table: ", e)

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def truncate_table():
        try:
            conn = database_connection()
            if conn is None:
                return
            cur = conn.cursor()
            # Truncate the table
            cur.execute(f"TRUNCATE TABLE {'stock'}")
            print(f"Table '{'stock'}' truncated successfully!")

        except psycopg2.Error as e:
            print(f"Error truncating table: {e}")

        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

def insert_value(pe_values):
    try:
        conn = database_connection()
        if conn is None:
            return
        cur = conn.cursor()

        # Insert value into table
        for date, pe in pe_values.items():
            cur.execute("INSERT INTO stock (date, PE) VALUES (%s, %s)", (date, int(pe)))
        print("Value inserted succesfully")
    
    except psycopg2.Error as e:
        print("Error while inserting value: ", e)

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()



def fetch_historical_pe(symbol):
    global eps  # Declare eps as global to modify it within the function
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
        eps = diluted_eps_value
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
    global late
    symbol = request.form['symbol']

    # Define the regex pattern to match strings with only uppercase letters
    pattern = r"^[A-Z]+$"

    # Compile the regex pattern
    regex = re.compile(pattern)
    if regex.match(symbol) == None:
        Notuppercase = "Buddy, you did not use uppercase letters! You have to, okay?"
        donkey = [symbol, Notuppercase ]
        return render_template('index.html', donkey=donkey)

    # Trying to fetch data on the inserted stock symbol
    try:
        fetch_historical_pe(symbol)
        today = datetime.datetime.now()
        last_month = today - datetime.timedelta(days=2)

        # Downnload daily finance data from Yahoo Finance
        stock_data = yf.download(symbol, start=last_month.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))['Close'].iloc[-1]
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ticker = yf.Ticker(symbol).info
        # Company Info
        company_name = ticker['longName']
        company_industry = ticker['industry']
        company_size = ticker['fullTimeEmployees']
        company_description = ticker['longBusinessSummary']

        # Stock Info
        stock_open = ticker['open']
        stock_close = ticker['previousClose']
        stock_volume = ticker['volume']

        late = stock_data/eps
        list_with_t = [company_name, company_industry, company_size, company_description, stock_data, stock_open, stock_close, stock_volume,  stock_data/eps ]
        return render_template('index.html', data=list_with_t)
     # If couldn't fetch data, the stock symbol doesn't exist (at least in Yahoo Finance).
    except Exception as e:
        error_message = f"Stock symbol '{symbol}' does not exist or there was an error fetching data."
        return render_template('index.html', error_message=error_message)

@app.route('/compare', methods=['POST'])
def compare():


    # Fetch historical P/E values to compare with
    try:
        # Connect to the "financeDatabase"
        conn = psycopg2.connect(
            dbname="financedatabase",
            user="postgres",
            password="UIS",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True

        # Create a cursor to execute SQL commands
        cur = conn.cursor()

        # Fetch P/E values from the "stock" table
        cur.execute("SELECT pe FROM stock")
        pe_values = cur.fetchall()

        # Calculate the average P/E ratio
        total_pe = sum(pe[0] for pe in pe_values)
        avg_pe = total_pe / len(pe_values) if pe_values else None

    except psycopg2.Error as e:
        print("Error fetching P/E values:", e)
        return None

    finally:
        # Close cursor and connection
        if 'cur' in locals():
            cur.close()
        conn.close()


    # Fetch the latest price for accurate comparison


    if late is None:
        comparison_result = "Latest P/E ratio is not available."
    else:
        comparison_result = f"Current P/E ratio ({late}) is {'bigger' if late > avg_pe else 'not bigger'} than the AVG P/E ratio ({avg_pe})."

    return render_template('index.html', comparison_result=comparison_result)

@app.route('/refresh', methods=['POST'])
def refresh():
    truncate_table()
    return render_template('index.html', data=None)


if __name__ == '__main__':

    create_database()
    create_table()

    app.run(debug=True)
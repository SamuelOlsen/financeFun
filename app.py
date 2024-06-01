from flask import Flask, render_template, request
from alpha_vantage.timeseries import TimeSeries

app = Flask(__name__)

# Replace 'YOUR_API_KEY' with your actual Alpha Vantage API key
API_KEY = 'YOUR_API_KEY'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stock', methods=['POST'])
def stock():
    symbol = request.form['symbol']
    ts = TimeSeries(key=API_KEY, output_format='json')
    data, meta_data = ts.get_quote_endpoint(symbol)
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
# FinanceFun

This project has been developed as part of the DIKU course "Databases and Information systems". 

## Overview

FinanceFun is a web app that that uses stock data from Yahoo Finance to let the user search for a stock symbol. It will show information about the company, different stock attributes and let the user check if the P/E is less than the average (30 days). 

## How to compile
Python and PostgreSQL are required. First you should clone the git repository. Make sure to edit it to your Git username:
```
git clone https://github.com/username/financefun
```
Next, you should install of the different modules required to run the project. This can be done with:
```
pip install -r requirements.txt
```

## How to run and interact with the web app
In order to run the web app:
```
python3 app.py
```
This should now have created a financedatabase and you should be able to access it, locally, on: 
```
http://127.0.0.1:5000/
```
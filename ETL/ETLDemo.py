import os
import sys
import petl
import pyodbc
import configparser
import requests
import datetime
import json
import decimal


config = configparser.ConfigParser()

try:
    config.read('ETL.ini')
except Exception as e:
    print('issue reading config: ' + str(e))
    sys.exit()

startDate = config['CONFIG']['STARTdATE']
url = config['CONFIG']['url']
server = config['CONFIG']['server']
database = config['CONFIG']['database']

print(startDate + url + server + database)

try:
    response = requests.get(url+startDate)
except Exception as e:
    print('error with request:' + str(e))
    sys.exit()

#print(response.text)

dates = []
rates = []

if (response.status_code == 200):
    raw = json.loads(response.text)

    for row in raw['observations']:
        dates.append(datetime.datetime.strptime(row['d'], '%Y-%m-%d'))
        rates.append(decimal.Decimal(row['FXUSDCAD']['v']))

    exchangeRates = petl.fromcolumns([dates,rates],header=['date','rate'])

    try:
        expenses = petl.io.xlsx.fromxlsx('Expenses.xlsx',sheet='Github')
    except Exception as e:
        print('issue opening xlsx file: '+ str(e))

    expenses = petl.outerjoin(exchangeRates, expenses, key='date')

    expenses = petl.filldown(expenses, 'rate')

    expenses = petl.select(expenses, lambda record: record.USD != None)


    expenses = petl.addfield(expenses, 'CAD', lambda record: decimal.Decimal(record.USD) * record.rate)

    try:
        conn = pymssql.connect(server = server, database = database)
    except Exception as e:
        print('issue connecting to db: ' + str(e))


    try:
        petl.io.todb(expenses,conn,'Example')
    except Exception as e:
        print('issue writing to db: ' + str(e))

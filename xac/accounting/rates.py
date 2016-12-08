# Copyright (c) 2016, AB Uobis
# All rights reserved.

import os
import fnmatch
import io
from datetime import datetime, date, timezone
import time
import logging
import sys
import csv
import json
import uuid
from xac import app, db, models
from sqlalchemy.sql import func, extract
from sqlalchemy import exc
import subprocess
from dateutil import parser
from urllib import request
import gzip

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def download_rates():
    gzfile = request.urlopen("http://api.bitcoincharts.com/v1/csv/bitstampUSD.csv.gz")
    output = open(os.path.join(APP_ROOT,'data_rates/raw/bitstampUSD.csv.gz'),'wb')
    output.write(gzfile.read())
    output.close()
    gzfile = gzip.open(os.path.join(APP_ROOT,'data_rates/raw/bitstampUSD.csv.gz'), 'rb')
    output = open(os.path.join(APP_ROOT,'data_rates/raw/bitstampUSD.csv'), 'wb')
    output.write( gzfile.read())
    gzfile.close()
    output.close()
    os.remove(os.path.join(APP_ROOT,'data_rates/raw/bitstampUSD.csv.gz'))

def summarize_rates(database):
    searchdir = os.path.join(APP_ROOT,'data_rates/raw/')
    savedir = os.path.join(APP_ROOT,'data_rates/summary')
    matches = []
    p = subprocess.call([
    'psql', database, '-U', 'xac',
    '-c', "DELETE FROM rates",'--set=ON_ERROR_STOP=true'
    ])
    p = subprocess.call([
    'psql', database, '-U', 'xac',
    '-c', "DELETE FROM price_feeds",'--set=ON_ERROR_STOP=true'
    ])
    for root, dirnames, filenames in os.walk('%s' % searchdir):
        for filename in fnmatch.filter(filenames, '*.csv'):
            matches.append(os.path.join(root,filename))
    for csvfile in matches:
        filename = csvfile.split("/")
        filename = filename[-1]
        p = subprocess.call([
        'psql', database, '-U', 'xac',
        '-c', "\COPY price_feeds(timestamp, price, volume) FROM %s HEADER CSV" % csvfile,
        '--set=ON_ERROR_STOP=true'
        ])
        # This rounds the time stamps, you can change it to have fewer price marks and improve performance
        p = subprocess.call([
        'psql', database, '-U', 'xac',
        '-c', "UPDATE price_feeds SET timestamp = cast(timestamp/10 as int)*10",'--set=ON_ERROR_STOP=true'
        ])
        p = subprocess.call([
        'psql', database, '-U', 'xac',
        '-c', "INSERT INTO rates SELECT timestamp,  '%s' AS source, 'USD' as currency, (sum(price*volume) / sum(volume)) AS rate FROM price_feeds WHERE volume > 0 GROUP BY timestamp" % filename,'--set=ON_ERROR_STOP=true'
        ])
        p = subprocess.call([
        'psql', database, '-U', 'xac',
        '-c', "\COPY rates to %s/%s-summary.csv HEADER CSV" % (savedir, filename),
        '--set=ON_ERROR_STOP=true'
        ])
        p = subprocess.call([
        'psql', database, '-U', 'xac',
        '-c', "DELETE FROM price_feeds",'--set=ON_ERROR_STOP=true'
        ])
        p = subprocess.call([
        'psql', database, '-U', 'xac',
        '-c', "DELETE FROM rates",'--set=ON_ERROR_STOP=true'
        ])
    return True

def import_rates(database):
    searchdir = os.path.join(APP_ROOT,'data_rates/summary/')
    matches = []
    for root, dirnames, filenames in os.walk('%s' % searchdir):
        for filename in fnmatch.filter(filenames, '*-summary.csv'):
            matches.append(os.path.join(root,filename))
    for csvfile in matches:
        filename = csvfile.split("/")
        filename = filename[-1]
        p = subprocess.call([
        'psql', database, '-U', 'xac',
        '-c', "\COPY rates(date, source, currency, rate) FROM %s HEADER CSV" % csvfile,
        '--set=ON_ERROR_STOP=false'
        ])
    return True

def getRate(querydate):
    if type(querydate) is not datetime:
        querydate = parser.parse(querydate)
    querydate = int(querydate.strftime("%s"))
    print(querydate)
    closest_price = db.session \
        .query(models.Rates) \
        .order_by(func.abs( querydate -  models.Rates.date)) \
        .first()
    return closest_price.rate

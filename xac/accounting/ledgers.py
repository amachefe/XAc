# Copyright (c) 2016, AB Uobis
# All rights reserved.

import datetime
from collections import OrderedDict
from sqlalchemy.sql import func
from xac import db, models
import xac.accounting.rates as rates
from dateutil import parser

def query_entries(accountName, groupby, currency):
    if groupby == "All":
        ledger_entries = models.LedgerEntries \
            .query \
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .order_by(models.LedgerEntries.date.desc()) \
            .order_by(models.LedgerEntries.tside.desc()) \
            .all()
        account = foot_account(accountName, ledger_entries, 'All')
    elif groupby == "Daily":
        debit_ledger_entries = db.session\
            .query( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date), \
                func.sum(models.LedgerEntries.amount)) \
            .filter_by(ledger=accountName)\
            .filter_by(tside='debit')\
            .filter_by(currency=currency)\
            .group_by( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date)) \
            .all()
        credit_ledger_entries = db.session \
            .query( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date), \
                func.sum(models.LedgerEntries.amount))\
            .filter_by(currency=currency) \
            .filter_by(ledger=accountName) \
            .filter_by(tside='credit') \
            .group_by( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date)) \
            .all()
        ledger_entries = {}
        for entry in debit_ledger_entries:
            day = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))
            if not day in ledger_entries:
                ledger_entries[day] = {}
            ledger_entries[day]['debit'] = int(entry[3])
        for entry in credit_ledger_entries:
            day = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))
            if not day in ledger_entries:
              ledger_entries[day] = {}
            ledger_entries[day]['credit'] = int(entry[3])
        ledger_entries = OrderedDict(sorted(ledger_entries.items()))
        account = foot_account(accountName, ledger_entries, 'Summary')
    elif groupby == "Monthly":
        debit_ledger_entries = db.session \
            .query( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.sum(models.LedgerEntries.amount)) \
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .filter_by(tside='debit') \
            .group_by( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date)) \
            .all()
        credit_ledger_entries = db.session\
            .query( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.sum(models.LedgerEntries.amount)) \
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .filter_by(tside='credit') \
            .group_by( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date)) \
            .all()
        ledger_entries = {}
        for entry in debit_ledger_entries:
            month = datetime.date(int(entry[0]), int(entry[1]), 1)
            if not month in ledger_entries:
                ledger_entries[month] = {}
            ledger_entries[month]['debit'] = int(entry[2])
        for entry in credit_ledger_entries:
            month = datetime.date(int(entry[0]), int(entry[1]), 1)
            if not month in ledger_entries:
                ledger_entries[month] = {}
            ledger_entries[month]['credit'] = int(entry[2])
        ledger_entries = OrderedDict(sorted(ledger_entries.items()))
        account = foot_account(accountName, ledger_entries, 'Summary')
    return [account, ledger_entries]

def foot_account(accountName, entries, interval):
  account = {}
  account['accountName'] = accountName
  account['totalDebit'] = 0
  account['totalCredit'] = 0
  account['debitBalance'] = 0
  account['creditBalance'] = 0
  if interval == 'All':
    for entry in entries:
      if entry.tside == 'debit' and entry.ledger == account['accountName']:
        account['totalDebit'] += entry.amount
      elif entry.tside == 'credit' and entry.ledger == account['accountName']:
        account['totalCredit'] += entry.amount
    if account['totalDebit'] > account['totalCredit']:
      account['debitBalance'] = account['totalDebit'] - account['totalCredit']
    elif account['totalDebit'] < account['totalCredit']:
      account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    return account
  elif interval == 'Summary':
    for entry in entries:
      if 'debit' in entries[entry]:
        account['totalDebit'] += entries[entry]['debit']
      if 'credit' in entries[entry]:
        account['totalCredit'] += entries[entry]['credit']
    if account['totalDebit'] > account['totalCredit']:
      account['debitBalance'] = account['totalDebit'] - account['totalCredit']
    elif account['totalDebit'] < account['totalCredit']:
      account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    return account
    
def get_balance(accountName, querydate):
    if type(querydate) is not datetime.datetime:
        querydate = parser.parse(querydate)
    transactions = query = db.session.query(\
      models.LedgerEntries.amount,\
      models.LedgerEntries.date,\
      models.LedgerEntries.tside).\
      filter(models.LedgerEntries.ledger_name==accountName, models.LedgerEntries.date <= querydate).\
      all()
    balance = 0
    for transaction in transactions:
        if transaction[2] == 'debit':
            balance += transaction[0]
        elif transaction[2] == 'credit':
            balance -= transaction[0]
    if balance > 0:
        debitBalance = balance
        creditBalance = 0
    elif balance < 0:
        debitBalance = 0
        creditBalance = balance
    else:
        debitBalance = 0
        creditBalance = 0
    balance = {'accountName': accountName,\
     'debitBalance' : debitBalance,\
     'creditBalance' : creditBalance}
    return balance

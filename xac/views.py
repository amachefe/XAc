# Copyright (c) 2016, AB Uobis
# All rights reserved.

import os
import io
import uuid
import ast
import csv
import calendar
from collections import OrderedDict
from datetime import datetime,date
from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from xac import app, db, forms, models
import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from xac.accounting.memoranda import process_filestorage
import xac.accounting.ledgers as ledgers
import xac.accounting.rates as rates
import xac.accounting.valuations as valuations

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/Configure')
def configure():
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts')
def chart_of_accounts():
    classificationform = forms.NewClassification()
    accountform = forms.NewAccount()
    subaccountform = forms.NewSubAccount()
    subaccounts = models.Subaccounts.query.all()
    return render_template("configure/chart_of_accounts.html",
        subaccounts=subaccounts,
        classificationform=classificationform,
        accountform=accountform,
        subaccountform=subaccountform)

@app.route('/Configure/ChartOfAccounts/AddClassification', methods=['POST','GET'])
def add_classification():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['classification']
        parent = form['classificationparent']
        parent = models.Elements.query.filter_by(id=parent).one()
        parent = parent.name
        classification = models.Classifications(name=name, parent=parent)
        db.session.add(classification)
        db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/DeleteClassification/<classification>')
def delete_classification(classification):
    classification = models.Classifications \
        .query \
        .filter_by(name=classification) \
        .first()
    db.session.delete(classification)
    db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/AddAccount', methods=['POST','GET'])
def add_account():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['account']
        parent = form['accountparent']
        parent = models.Classifications \
            .query \
            .filter_by(id=parent) \
            .one()
        parent = parent.name
        account = models.Accounts(name=name, parent=parent)
        db.session.add(account)
        db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/DeleteAccount/<account>')
def delete_account(account):
    account = models.Accounts.query.filter_by(name=account).first()
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/AddSubAccount', methods=['POST','GET'])
def add_subaccount():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['subaccount']
        parent = form['subaccountparent']
        parent = models.Accounts.query.filter_by(id=parent).one()
        parent = parent.name
        subaccount = models.Subaccounts(name=name, parent=parent)
        db.session.add(subaccount)
        db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/DeleteSubAccount/<subaccount>')
def delete_subaccount(subaccount):
    subaccount = models.Accounts.query.filter_by(name=subaccount).first()
    db.session.delete(subaccount)
    db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Bookkeeping')
def bookkeeping():
    return redirect(url_for('upload_csv'))

@app.route('/Bookkeeping/Memoranda/Upload', methods=['POST','GET'])
def upload_csv():
    filenames = ''
    if request.method == 'POST':
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            process_filestorage(file)
        return redirect(url_for('upload_csv'))
    memos = models.Memoranda \
        .query \
        .order_by(models.Memoranda.date.desc()) \
        .all()
    return render_template('bookkeeping/upload.html',
        title = 'Upload',
        memos=memos)

@app.route('/Bookkeeping/Memoranda/ExchangeRates')
def exchange_rates():
    
    return render_template("bookkeeping/exchange_rates.html")

@app.route('/Bookkeeping/Memoranda/DownloadRates')
def download_rates():
    rates.download_rates()
    return redirect(url_for('exchange_rates'))
  
@app.route('/Bookkeeping/Memoranda/ExchangeRates/Summarize')
def summarize_rates():
    rates.summarize_rates("xac")
    return redirect(url_for('exchange_rates'))
  
@app.route('/Bookkeeping/Memoranda/ExchangeRates/Import')
def import_rates():
    rates.import_rates("xac")
    return redirect(url_for('exchange_rates'))

@app.route('/Bookkeeping/Memoranda/ExchangeRates/CalculateGains/<method>')
def calc_gains(method):
    valuations.calculate_bitcoin_gains(method)
    return redirect(url_for('exchange_rates'))

@app.route('/Bookkeeping/Memoranda/Memos', methods=['POST','GET'])
def memoranda():
    memos = models.Memoranda \
        .query \
        .order_by(models.Memoranda.date.desc()) \
        .all()
    for memo in memos:
        transactions = models.MemorandaTransactions \
            .query \
            .filter_by(memoranda_id=memo.id) \
            .all()
        memo.count = len(transactions)

    return render_template('bookkeeping/memos.html',
        title = 'Memoranda',
        memos=memos)

@app.route('/Bookkeeping/Memoranda/Memos/Delete/<fileName>')
def delete_memoranda(fileName):
    memo = models.Memoranda \
        .query \
        .filter_by(fileName=fileName) \
        .first()
    transactions = models.MemorandaTransactions \
        .query \
        .filter_by(memoranda_id=memo.id) \
        .all()
    for transaction in transactions:
        journal_entry = models.JournalEntries \
            .query \
            .filter_by(memoranda_transactions_id=transaction.id) \
            .first()
        ledger_entries = models.LedgerEntries \
            .query \
            .filter_by(journal_entry_id = journal_entry.id) \
            .all()
        for entry in ledger_entries:
            db.session.delete(entry)
            db.session.commit()
        db.session.delete(journal_entry)
        db.session.commit()
        db.session.delete(transaction)
        db.session.commit()
    db.session.delete(memo)
    db.session.commit()
    return redirect(url_for('upload_csv'))

@app.route('/Bookkeeping/Memoranda/Memos/<fileName>')
def memo_file(fileName):
    memo = models.Memoranda.query.filter_by(fileName=fileName).first()
    fileText = memo.fileText
    document = io.StringIO(fileText)
    reader = csv.reader(document)
    rows = [pair for pair in reader]
    return render_template('bookkeeping/memo_file.html',
        title = 'Memo',
        rows=rows,
        fileName=fileName)
  
@app.route('/Bookkeeping/Memoranda/Memos/Transactions')
def transactions():
    transactions = models.MemorandaTransactions.query.all()
    for transaction in transactions:
        transaction.details = ast.literal_eval(transaction.details)
        journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
        transaction.journal_entry_id = journal_entry.id
    return render_template('bookkeeping/memo_transactions.html',
        title = 'Memo',
        transactions=transactions)


@app.route('/Bookkeeping/Memoranda/Memos/<fileName>/Transactions')
def memo_transactions(fileName):
    memo = models.Memoranda.query.filter_by(fileName=fileName).first()
    transactions = models.MemorandaTransactions.query.filter_by(memoranda_id=memo.id).all()
    for transaction in transactions:
        transaction.details = ast.literal_eval(transaction.details)
        journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
        transaction.journal_entry_id = journal_entry.id
    return render_template('bookkeeping/memo_transactions.html',
        title = 'Memo',
        transactions=transactions,
        fileName=fileName)

@app.route('/Bookkeeping/GeneralJournal/<currency>')
def general_journal(currency):
    journal_entries = db.session \
        .query(models.JournalEntries) \
        .filter(models.JournalEntries.ledgerentries \
            .any(currency=currency)) \
        .join(models.LedgerEntries) \
        .order_by(models.LedgerEntries.date.desc()) \
        .all()
    for journal_entry in journal_entries:
        journal_entry.ledgerentries = [c for c in journal_entry.ledgerentries if c.currency == currency]
    return render_template('bookkeeping/general_journal.html',
        title = 'General Journal',
        journal_entries=journal_entries,
        currency=currency)

@app.route('/Bookkeeping/GeneralJournal/Entry/<id>')
def journal_entry(id):
    journal_entry = models.JournalEntries.query.filter_by(id = id).first()
    ledger_entries = models.LedgerEntries.query.filter_by(journal_entry_id = id).order_by(models.LedgerEntries.date.desc()).order_by(models.LedgerEntries.tside.desc()).all()
    transaction = models.MemorandaTransactions.query.filter_by(id=journal_entry.memoranda_transactions_id).first()
    memo = models.Memoranda.query.filter_by(id=transaction.memoranda_id).first()
    transaction.details = ast.literal_eval(transaction.details)
    print(ledger_entries)
    return render_template('bookkeeping/journal_entry.html',
        title = 'Journal Entry',
        journal_entry=journal_entry,
        ledger_entries=ledger_entries,
        transaction=transaction,
        memo=memo)

@app.route('/Bookkeeping/GeneralJournal/<id>/Edit', methods=['POST','GET'])
def edit_journal_entry(id):
    journal_entry = models.JournalEntries.query.filter_by(id = id).first()
    ledger_entries = models.LedgerEntries.query.filter_by(journal_entry_id = id).order_by(models.LedgerEntries.date.desc()).order_by(models.LedgerEntries.tside.desc()).all()
    transaction = models.MemorandaTransactions.query.filter_by(id=journal_entry.memoranda_transactions_id).first()
    memo = models.Memoranda.query.filter_by(id=transaction.memoranda_id).first()
    transaction.details = ast.literal_eval(transaction.details)
    return render_template('bookkeeping/journal_entry_edit.html',
        title = 'Journal Entry',
        journal_entry=journal_entry,
        ledger_entries=ledger_entries,
        transaction=transaction,
        memo=memo)

@app.route('/Bookkeeping/GeneralLedger/<currency>')
def general_ledger(currency):
    accountsQuery = db.session\
        .query(models.LedgerEntries.ledger)\
        .group_by(models.LedgerEntries.ledger).all()
    accounts = []
    for accountResult in accountsQuery: 
        accountName = accountResult[0]
        query = ledgers.query_entries(accountName, 'Monthly', currency)
        accounts.append(query)
    return render_template('bookkeeping/general_ledger.html',
        title = 'General Ledger',
        accounts=accounts,
        currency=currency)

@app.route('/Bookkeeping/Ledger/<accountName>/<currency>/<groupby>')
def ledger(accountName, currency, groupby):
    query = ledgers.query_entries(accountName, groupby, currency)
    return render_template('bookkeeping/ledger.html',
        title = 'Ledger',
        currency=currency,
        account=query[0],
        ledger_entries=query[1],
        groupby = groupby,
        accountName=accountName)

@app.route('/Bookkeeping/Ledger/<accountName>/<currency>/<groupby>/<interval>')
def ledger_page(accountName, currency, groupby, interval):
    if groupby == "Daily":
        interval = datetime.strptime(interval, "%m-%d-%Y")
        year = interval.year
        month = interval.month
        day = interval.day
        ledger_entries = models.LedgerEntries \
            .query \
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .filter( \
                func.date_part('year', models.LedgerEntries.date)==year, \
                func.date_part('month', models.LedgerEntries.date)==month, \
                func.date_part('day', models.LedgerEntries.date)==day) \
            .order_by(models.LedgerEntries.date) \
            .order_by(models.LedgerEntries.tside.asc()) \
            .all()
        account = ledgers.foot_account(accountName, ledger_entries, 'All')
    if groupby == "Monthly":
        interval = datetime.strptime(interval, "%m-%Y")
        year = interval.year
        month = interval.month
        ledger_entries = models.LedgerEntries\
            .query\
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .filter( \
                func.date_part('year', models.LedgerEntries.date)==year, \
                func.date_part('month', models.LedgerEntries.date)==month)\
            .order_by(models.LedgerEntries.date) \
            .order_by(models.LedgerEntries.tside.desc()) \
            .all()
        account = ledgers.foot_account(accountName, ledger_entries, 'All')
    return render_template('bookkeeping/ledger.html',
        title = 'Ledger',
        account=account,
        ledger_entries=ledger_entries,
        groupby2 = groupby,
        groupby = 'All',
        accountName=accountName,
        interval=interval,
        currency=currency)

@app.route('/Bookkeeping/TrialBalance/<currency>')
def trial_balance(currency):
    accountsQuery = db.session \
        .query(models.LedgerEntries.ledger) \
        .group_by(models.LedgerEntries.ledger) \
        .filter(models.LedgerEntries.currency==currency) \
        .all()
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date) + '-'+
            func.date_part('month', models.LedgerEntries.date)) \
        .filter(models.LedgerEntries.currency==currency) \
        .group_by(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    period = datetime.now()    
    year = period.year
    month = period.month
    accounts = []
    totalDebits = 0
    totalCredits = 0
    for accountResult in accountsQuery:
        accountName = accountResult[0]
        ledger_entries = models.LedgerEntries \
            .query \
                .filter_by(ledger=accountName)\
                .filter_by(currency=currency) \
                .filter( \
                    func.date_part('year', models.LedgerEntries.date)==year,
                    func.date_part('month', models.LedgerEntries.date)==month) \
                .order_by(models.LedgerEntries.date) \
                .order_by(models.LedgerEntries.tside.desc()) \
                .all()
        query = ledgers.foot_account(accountName, ledger_entries, 'All')
        totalDebits += query['debitBalance']
        totalCredits += query['creditBalance']
        accounts.append(query)
    return render_template('bookkeeping/trial_balance.html',
        currency=currency,
        periods=periods,
        period=period,
        accounts=accounts,
        totalDebits=totalDebits,
        totalCredits=totalCredits)

@app.route('/Bookkeeping/TrialBalance/<currency>/<groupby>/<period>')
def trial_balance_historical(currency, groupby, period):
    accountsQuery = db.session \
        .query(models.LedgerEntries.ledger) \
        .group_by(models.LedgerEntries.ledger) \
        .filter(models.LedgerEntries.currency==currency) \
        .all()
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date) + '-'+
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by(\
            func.date_part('year', models.LedgerEntries.date),\
            func.date_part('month', models.LedgerEntries.date)) \
        .filter(models.LedgerEntries.currency==currency) \
        .all()
    period = datetime.strptime(period, "%Y-%m")
    year = period.year
    month = period.month
    day = calendar.monthrange(year, month)[1]
    period = datetime(year, month, day, 23, 59, 59)
    accounts = []
    totalDebits = 0
    totalCredits = 0
    for accountResult in accountsQuery:
        accountName = accountResult[0]
        ledger_entries = models.LedgerEntries \
            .query \
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .filter( \
                func.date_part('year', models.LedgerEntries.date)==year, \
                func.date_part('month', models.LedgerEntries.date)==month) \
            .order_by(models.LedgerEntries.date) \
            .order_by(models.LedgerEntries.tside.desc()) \
            .all()
        query = ledgers.foot_account(accountName, ledger_entries, 'All')
        totalDebits += query['debitBalance']
        totalCredits += query['creditBalance']
        accounts.append(query)
    return render_template('bookkeeping/trial_balance.html',
        currency=currency,
        periods=periods,
        period=period,
        accounts=accounts,
        totalDebits=totalDebits,
        totalCredits=totalCredits)

@app.route('/FinancialStatements')
def financial_statements():
    return redirect(url_for('income_statement', currency='satoshis'))

@app.route('/FinancialStatements/IncomeStatement/<currency>')
def income_statement(currency):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date),\
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date),\
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    period = datetime.now()
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, period.day, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses']))\
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()
    net_income = 0
    for element in elements:
        element.classifications = [c for c in element.classifications if c.name in ['Revenues', 'Expenses', 'Gains', 'Losses']]
        for classification in element.classifications:
            for account in classification.accounts:
                for subaccount in account.subaccounts:
                    subaccount.total = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if period_beg <= c.date <= period_end ]
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            if ledger_entry.tside == 'credit':
                                subaccount.total += ledger_entry.amount
                                net_income += ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                net_income -= ledger_entry.amount
                                subaccount.total -= ledger_entry.amount
    return render_template('financial_statements/income_statement.html',
            title = 'Income Statement',
            periods = periods,
            currency = currency,
            elements = elements,
            net_income = net_income)
    
@app.route('/FinancialStatements/IncomeStatement/<currency>/<period>')
def income_statement_historical(currency, period):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    period = datetime.strptime(period, "%Y-%m")
    lastday = calendar.monthrange(period.year, period.month)[1]
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, lastday, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses']))\
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()
    net_income = 0
    for element in elements:
        element.classifications = [c for c in element.classifications if c.name in ['Revenues', 'Expenses', 'Gains', 'Losses']]
        for classification in element.classifications:
            for account in classification.accounts:
                for subaccount in account.subaccounts:
                    subaccount.total = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if period_beg <= c.date <= period_end ]
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            if ledger_entry.tside == 'credit':
                                net_income += ledger_entry.amount
                                subaccount.total += ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                net_income -= ledger_entry.amount
                                subaccount.total -= ledger_entry.amount
    return render_template('financial_statements/income_statement.html',
            title = 'Income Statement',
            periods = periods,
            currency = currency,
            elements = elements,
            net_income = net_income)
    
@app.route('/FinancialStatements/BalanceSheet/<currency>')
def balance_sheet(currency):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    period = datetime.now()
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, period.day, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()

    retained_earnings = 0
    
    for element in elements:
        element.balance = 0
        for classification in element.classifications:
            classification.balance = 0
            for account in classification.accounts:
                account.balance = 0
                for subaccount in account.subaccounts:
                    subaccount.balance = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if c.date <= period_end ]
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            
                            if ledger_entry.tside == 'credit':
                                element.balance -= ledger_entry.amount
                                classification.balance -= ledger_entry.amount
                                account.balance -= ledger_entry.amount
                                subaccount.balance -= ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                element.balance += ledger_entry.amount
                                classification.balance += ledger_entry.amount
                                account.balance += ledger_entry.amount
                                subaccount.balance += ledger_entry.amount
        if element.name == 'Equity':
            retained_earnings =  -element.balance
            print(retained_earnings)
    elements = [c for c in elements if c.name in ['Assets', 'Liabilities']]
    return render_template('financial_statements/balance_sheet.html', 
    periods=periods,
    currency=currency,
    elements=elements,
    retained_earnings=retained_earnings,
    period=period_end)
    
@app.route('/FinancialStatements/BalanceSheet/<currency>/<period>')
def balance_sheet_historical(currency, period):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    period = datetime.strptime(period, "%Y-%m")
    lastday = calendar.monthrange(period.year, period.month)[1]
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, lastday, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()

    retained_earnings = 0

    for element in elements:
        element.balance = 0
        for classification in element.classifications:
            classification.balance = 0
            for account in classification.accounts:
                account.balance = 0
                for subaccount in account.subaccounts:
                    subaccount.balance = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if c.date <= period_end ]
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            
                            if ledger_entry.tside == 'credit':
                                element.balance -= ledger_entry.amount
                                classification.balance -= ledger_entry.amount
                                account.balance -= ledger_entry.amount
                                subaccount.balance -= ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                element.balance += ledger_entry.amount
                                classification.balance += ledger_entry.amount
                                account.balance += ledger_entry.amount
                                subaccount.balance += ledger_entry.amount
        if element.name == 'Equity':
            retained_earnings =  -element.balance
            print(retained_earnings)
    elements = [c for c in elements if c.name in ['Assets', 'Liabilities']]
    return render_template('financial_statements/balance_sheet.html', 
    periods=periods,
    currency=currency,
    elements=elements,
    retained_earnings=retained_earnings,
    period=period_end)


    
@app.route('/FinancialStatements/StatementOfCashFlows/<currency>/<period>')
def statement_of_cash_flows(currency, period):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    if period == 'Current':
        period = datetime.now()
        lastday = period.day
    else:
        period = datetime.strptime(period, "%Y-%m")
        lastday = calendar.monthrange(period.year, period.month)[1]
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, lastday, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses']))\
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()
    net_income = 0
    for element in elements:
        element.classifications = [c for c in element.classifications if c.name in ['Revenues', 'Expenses', 'Gains', 'Losses']]
        for classification in element.classifications:
            classification.balance = 0
            for account in classification.accounts:
                account.balance = 0
                for subaccount in account.subaccounts:
                    subaccount.balance = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if period_beg <= c.date <= period_end ]
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            
                            if ledger_entry.tside == 'credit':
                                classification.balance -= ledger_entry.amount
                                account.balance -= ledger_entry.amount
                                subaccount.balance -= ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                classification.balance += ledger_entry.amount
                                account.balance += ledger_entry.amount
                                subaccount.balance += ledger_entry.amount
    return render_template('financial_statements/statement_of_cash_flows.html',
            period = period,
            periods = periods,
            currency = currency,
            elements = elements,
            net_income = net_income)

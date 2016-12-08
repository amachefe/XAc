# Copyright (c) 2016, AB Uobis
# All rights reserved.

from xac import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import BigInteger


# Memoranda are source documents from which accounting information is extracted to form General Journal entries. As a preliminary step, all of the details for each individual transaction are extracted from the source document to a dictionary.


class Memoranda(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime, index=True)
    fileName = db.Column(db.Text, unique=True)
    fileType = db.Column(db.Text)
    fileSize = db.Column(BigInteger)
    fileText = db.Column(db.Text)

class MemorandaTransactions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    txid = db.Column(db.Text)
    details = db.Column(JSON) # Replace (db.Text) with (JSON) for pg
    memoranda_id = db.Column(db.Text, db.ForeignKey('memoranda.id'))

class BitcoinTransactions(db.Model):
    # txid of the bitcoins received
    txid = db.Column(db.Text, primary_key=True)
    # output index of the bitcoins received
    output_index = db.Column(db.Integer, primary_key=True)
    # address the bitcoins were received with
    output_address = db.Column(db.Text)
    amount = db.Column(BigInteger)
    unspent = db.Column(db.Boolean)
    last_updated = db.Column(db.DateTime)
    memoranda_transactions_id = db.Column(db.Text, db.ForeignKey('memoranda_transactions.id'))

class Elements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    classifications = db.relationship('Classifications', backref='element', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name

class Classifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    parent = db.Column(db.Text, db.ForeignKey('elements.name'))
    accounts = db.relationship('Accounts', backref='classification', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name
        
class Accounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    parent = db.Column(db.Text, db.ForeignKey('classifications.name'))
    subaccounts = db.relationship('Subaccounts', backref='account', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name

class Subaccounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    parent = db.Column(db.Text, db.ForeignKey('accounts.name'))
    ledgerentries = db.relationship('LedgerEntries', backref='subaccount', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name

class JournalEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    memoranda_transactions_id = db.Column(db.Text, db.ForeignKey('memoranda_transactions.id'))
    ledgerentries = db.relationship('LedgerEntries', backref='journalentry', lazy='select', cascade="save-update, merge, delete", order_by="desc(LedgerEntries.tside), desc(LedgerEntries.amount)")

class LedgerEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime)
    tside = db.Column(db.Text)
    amount = db.Column(db.Numeric)
    currency = db.Column(db.Text)
    ledger = db.Column(db.Text, db.ForeignKey('subaccounts.name'))
    journal_entry_id = db.Column(db.Text, db.ForeignKey('journal_entries.id'))

class PriceFeeds(db.Model):
    price_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.BigInteger)
    price = db.Column(db.Numeric)
    volume = db.Column(db.Numeric)

class Rates(db.Model):
    date = db.Column(db.BigInteger, primary_key=True)
    source = db.Column(db.Text)
    currency = db.Column(db.Text)
    rate = db.Column(db.Numeric)

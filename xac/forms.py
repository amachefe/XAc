# Copyright (c) 2016, AB Uobis
# All rights reserved.

from flask_wtf import Form
from wtforms import TextField, TextAreaField, \
SubmitField, SelectField, FloatField, validators, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Required, Length
from wtforms.ext.sqlalchemy.orm import model_form
from sqlalchemy.sql import func 
from xac import models, db
from xac.models import Elements, Classifications, Accounts, LedgerEntries

def available_classification_parents():
    return Elements.query

def available_account_parents():
    return Classifications.query

def available_subaccount_parents():
    return Accounts.query

class NewClassification(Form):
    classification = TextField("Classification Name")
    classificationparent = QuerySelectField(query_factory=available_classification_parents, allow_blank=False)

class NewAccount(Form):
    account = TextField("Account Name")
    accountparent = QuerySelectField(query_factory=available_account_parents, allow_blank=False)

class NewSubAccount(Form):
    subaccount = TextField("Sub-Account Name")
    subaccountparent = QuerySelectField(query_factory=available_subaccount_parents, allow_blank=False)

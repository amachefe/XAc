# Copyright (c) 2016, AB Uobis
# All rights reserved.

from flask import Flask
from flask.ext.babel import Babel
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
babel = Babel(app)
db = SQLAlchemy(app)

@app.context_processor
def utility_processor():
    def format_satoshis(amount):
        return u'{:,}'.format(abs(amount)/100000000)
    def format_usd(amount):
        return u"${:,.2f}".format(abs(amount))
    return dict(format_usd=format_usd, format_satoshis=format_satoshis)

from xac import views, models, forms

# -*- coding: utf8 -*-
# Copyright (c) 2016, AB Uobis
# All rights reserved.

# The CSRF_ENABLED setting activates the cross-site request forgery prevention. 
# In most cases you want to have this option enabled as it makes your app more secure.
import os
basedir = os.path.abspath(os.path.dirname(__file__))


CSRF_ENABLED = True

SECRET_KEY = os.environ.get('SECRET_KEY')  or 'XAcPacioliPlus'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pdf','tiff', 'xlsx','xls','csv'])
SQLALCHEMY_DATABASE_URI = "postgresql://xacu@localhost/xacdb"
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'XAC.db')
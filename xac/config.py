# -*- coding: utf8 -*-

# Copyright (c) 2016, AB Uobis
# All rights reserved.

CSRF_ENABLED = True

# Change the secret key. 

SECRET_KEY = 'eaoR2CMuUKp1'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pdf','tiff', 'xlsx','xls','csv'])
SQLALCHEMY_DATABASE_URI = "postgresql://xac@localhost/xac"

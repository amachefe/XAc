import xac

xac.app.config['TESTING'] = True
xac.app.config['WTF_CSRF_ENABLED'] = False
xac.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'xac.db')
xac.db.drop_all()
xac.db.create_all()
xac.rates.import_summary('xac-test')
asset_entry =  xac.models.Classifications(name = 'Asset')
xac.db.session.add(asset_entry)
liability_entry =  xac.models.Classifications(name = 'Liability')
xac.db.session.add(liability_entry)
equity_entry =  xac.models.Classifications(name = 'Equity')
xac.db.session.add(equity_entry)
revenue_entry =  xac.models.Classifications(name = 'Revenue')
xac.db.session.add(revenue_entry)
expense_entry =  xac.models.Classifications(name = 'Expense')
xac.db.session.add(expense_entry)
xac.db.session.commit()

asset_entry =  xac.models.Accounts(name = 'Asset', parent = 'Asset')
xac.db.session.add(asset_entry)
bitcoins_entry =  xac.models.Accounts(name = 'Bitcoins', parent = 'Asset')
xac.db.session.add(bitcoins_entry)
liability_entry =  xac.models.Accounts(name = 'Liability', parent = 'Liability')
xac.db.session.add(liability_entry)
equity_entry =  xac.models.Accounts(name = 'Equity', parent = 'Equity')
xac.db.session.add(equity_entry)
revenue_entry =  xac.models.Accounts(name = 'Revenue', parent = 'Revenue')
xac.db.session.add(revenue_entry)
expense_entry =  xac.models.Accounts(name = 'Expense', parent = 'Expense')
xac.db.session.add(expense_entry)
xac.db.session.commit()

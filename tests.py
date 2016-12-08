# Copyright (c) 2016, AB Uobis
# All rights reserved.

#!flask/bin/python

import os
import fnmatch
import unittest
import uuid
import xac

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


class TestCase(unittest.TestCase):
    def setUp(self):
        xac.app.config['TESTING'] = True
        xac.app.config['WTF_CSRF_ENABLED'] = False
        xac.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'xac-test')
        self.app = xac.app.test_client()
        print("Setup complete.")

    def tearDown(self):
        xac.models.LedgerEntries.query.delete()
        xac.db.session.commit()
        xac.models.JournalEntries.query.delete()
        xac.db.session.commit()
        xac.models.MemorandaTransactions.query.delete()
        xac.db.session.commit()
        xac.models.Memoranda.query.delete()
        xac.db.session.commit()
        xac.db.session.remove()
        print("Tear down complete.")
    
    def test_empty_uploads(self):
        rv = self.app.get('/Bookkeeping/Upload')
        page = rv.data.decode("utf-8")
        assert "No files have been uploaded." in page
        
    def test_empty_memoranda(self):
        rv = self.app.get('/Bookkeeping/Memoranda')
        page = rv.data.decode("utf-8")
        assert "No memoranda have been recorded." in page
        
    def test_empty_memoranda_transactions(self):
        rv = self.app.get('/Bookkeeping/Memoranda/Transactions')
        page = rv.data.decode("utf-8")
        assert "No memorandum transactions have been recorded." in page
        
    def test_empty_general_journal(self):
        rv = self.app.get('/Bookkeeping/GeneralJournal')
        page = rv.data.decode("utf-8")
        assert "No journal entries have been recorded." in page
        
    def test_empty_general_ledger(self):
        rv = self.app.get('/Bookkeeping/GeneralLedger')
        page = rv.data.decode("utf-8")
        assert "No ledger entries have been recorded." in page

    # Too hard, saving this for later
    # def test_upload(self):
    #     response = app_client.post('/Upload', buffered=True,
    #       content_type='multipart/form-data',
    #       data={'file': (io.ByteIO('hello there'), 'hello.txt')})
    #     assert res.status_code == 200
    #     assert 'file saved' in res.data
    
    def test_process_csv(self):
        searchdir = os.path.join(APP_ROOT,'xac/data_wallets/')
        matches = []
        for root, dirnames, filenames in os.walk('%s' % searchdir):
            for filename in fnmatch.filter(filenames, '*Test.csv'):
                matches.append(os.path.join(root,filename))
        for csvfile in matches:
            memoranda_id = str(uuid.uuid4())
            fileName = csvfile.split("/")
            fileName = fileName[-1]
            fileType = fileName.rsplit('.', 1)[1]
            fileSize = os.path.getsize(csvfile)
            with open(csvfile, 'rt') as csvfile:
                fileText = csvfile.read()
                xac.memoranda.process_memoranda(fileName, fileType, fileSize, fileText)
        rv = self.app.get('/Bookkeeping/Upload')
        page = rv.data.decode("utf-8")
        assert '<a href="/Bookkeeping/Memoranda/MultiBit' in page
        assert '<a href="/Bookkeeping/Memoranda/Coinbase' in page
        assert '<a href="/Bookkeeping/Memoranda/Bitcoin' in page
        assert '<a href="/Bookkeeping/Memoranda/Electrum' in page
        assert '<a href="/Bookkeeping/Memoranda/Armory' in page
        
        rv = self.app.get('/Bookkeeping/Memoranda/Transactions')
        page = rv.data.decode("utf-8")
        assert '0000000000000000000000000000000000000000000000000000000000000000-000' in page
        assert '1HR5hGL912oTAEWVn4gyY2jjDw259c4XxF' in page
        assert '2013-01-01T01:01:01' in page
        
        rv = self.app.get('/Bookkeeping/GeneralJournal')
        page = rv.data.decode("utf-8")
        assert '<a href="/Bookkeeping/Ledger/Expense/All">' in page
        assert '01-01-2013 01:01' in page
        assert '50.0' in page
        
        rv = self.app.get('/Bookkeeping/GeneralLedger')
        page = rv.data.decode("utf-8")
        assert '<a href="/Bookkeeping/Ledger/Bitcoins/Monthly/01-2013">' in page
        assert '250.0' in page
        assert '<a href="/Bookkeeping/Ledger/Expense/All">' in page
        
        rv = self.app.get('/Bookkeeping/Ledger/Bitcoins/Monthly/01-2013')
        page = rv.data.decode("utf-8")
        assert '<a href="/Bookkeeping/Ledger/Bitcoins/Daily">' in page
        assert '250.0' in page
        assert '<a href="/Bookkeeping/GeneralJournal/' in page
        
        rv = self.app.get('/FinancialStatements/IncomeStatement')
        page = rv.data.decode("utf-8")
        assert '12-2013' in page
        assert '-250.0' in page
        assert 'Net Income' in page
        
        balance = xac.ledgers.get_balance('Bitcoins', '11/20/2013')
        assert balance == 25000000000
        
        
        balance = xac.ledgers.get_balance('Bitcoins', '12/31/2013 11:59:59.00PM')
        assert balance == 0
        
        fifo_costbasis = xac.ledgers.get_fifo_costbasis('Bitcoins', '12/31/2013 11:59:59.00PM')
        assert fifo_costbasis == [0, 0, 0]
        
        fifo_costbasis = xac.ledgers.get_fifo_costbasis('Bitcoins', '11/30/2013 11:59:59.00PM')
        assert fifo_costbasis[2] == 3250
        
        fifo_unrealized_gain = xac.ledgers.get_fifo_unrealized_gain('Bitcoins', '12/31/2013 11:59:59.00PM')
        assert fifo_unrealized_gain == 0.0
        
        fifo_unrealized_gain = xac.ledgers.get_fifo_unrealized_gain('Bitcoins', '11/30/2013 11:59:59.00PM')
        assert fifo_unrealized_gain == 265750.0
        
        fifo_realized_gain = xac.ledgers.get_fifo_realized_gain('Bitcoins', '12/1/2013', '12/31/2013 11:59:59.00PM')
        assert fifo_realized_gain == 141400.0
        
        fifo_realized_gain = xac.ledgers.get_fifo_realized_gain('Bitcoins', '11/1/2013',  '11/30/2013 11:59:59.00PM')
        assert fifo_realized_gain == 0.0

if __name__ == '__main__':
    unittest.main()

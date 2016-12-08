XAc
=======

XAc is an accounting software implemented with a Python/Flask/PostgreSQL stack.

It is a fork of Pacioli (a bitcoin accounting software), and modified for general accounting!

## Guide to Installing XAc

1. Install [PostgreSQL](http://www.postgresql.org/) (switch sqlite3 for dev on config.py)
2. Create a user called xacu and a new database ([Instructions](http://killtheyak.com/use-postgresql-with-django-flask/))
3. Clone the repository(https://help.github.com/articles/clone-a-repo/)
4. Create a virtual environment <code>python3 -m venv venv</code>
5. Activate the virtual environment <code>. venv/bin/activate</code>
5. Install the requirements <code>pip install -r requirements.txt</code>
6. Run <code>python db_create.py</code>
7. Run <code>python run.py</code>


OAuthHub
========

An OAuth Server that consolidates identities from multiple OAuth Servers.

# Database configuration

Set up an `SQLALCHEMY_DATABASE_URI` environment variable as per
<http://flask-sqlalchemy.pocoo.org/2.0/config/>.

Of course, you'll have to create a database, create a user, and authorise the 
user to access the database, before you'll be able to set up this environment 
variable. An example of the authorisation could be like this:

    $ sudo mysql
    mysql> CREATE DATABASE lol_db;
    mysql> CREATE USER 'lol_user'@'localhost' IDENTIFIED
        -> BY 'clear-text-password';
    mysql> GRANT ALL PRIVILEGES ON lol_db.* TO 'lol_user'@'localhost'
        -> IDENTIFIED BY 'clear-text-password';

# Python 3

If you're using MySQL, notice that the module `MySQLdb` (from the pip package
[`MySQL-python`](https://pypi.python.org/pypi/MySQL-python/1.2.5)) doesn't
support Python 3. To use Flask-SQLAlchemy, you'll need to use a different
"driver" (a.k.a. "engine"?) as per
<http://flask-sqlalchemy.pocoo.org/2.0/config/#connection-uri-format>.

The pip package `PyMySQL` (`pip install pymysql`) seems to work, and is known
to Flask-SQLAlchemy as `pymysql` in the "driver" field of the URI string. More
details on `PyMySQL`:
<http://stackoverflow.com/questions/22252397/importerror-no-module-named-mysqldb>.

# Unit testing

For unit testing, create a separate database in the same DBMS (e.g. MySQL) using 
the same approach, and set up an environment variable 
`SQLALCHEMY_TESTING_DATABASE_URI` of the same format as 
`SQLALCHEMY_DATABASE_URI`.

To run the tests, `cd` to the directory which contains this README, then run
something equivalent to these commands:

    $ source .venv/bin/activate
    (.venv)$ PYTHONPATH=. python tests/whichever_you_want.py

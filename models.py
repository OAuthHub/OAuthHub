from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    fullname = db.Column(db.String)
    password = db.Column(db.String)
    authorizations = db.relationship("AccessToken", backref=db.backref("user"))

    def __repr__(self):
        return "<User(name='{}', fullname='{}', password='{}')>".format(self.name, self.fullname, self.password)

class AccessToken(db.Model):
    __tablename__ = 'access_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String)
    secret = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))

    def __repr__(self):
        return "<AccessToken(user='{}', server='{}', token='{}', secret='{}')>".format(self.user.name, self.server.name, self.token, self.secret)

class OAuthServer(db.Model):
    __tablename__ = 'servers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __repr__(self):
        return "<OAuthServer(name='{}')>".format(self.name)

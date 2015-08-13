#!/usr/bin/python3

import os
from flask import session
from models import OAuthServer, AccessToken, User, db

class Twitter(OAuthServer):
    def __init__(self, oauth):
        super(Twitter, self).__init__(name='Twitter')

        self.client = oauth.remote_app('twitter',
            base_url='https://api.twitter.com/1.1/',
            request_token_url='https://api.twitter.com/oauth/request_token',
            access_token_url='https://api.twitter.com/oauth/access_token',
            authorize_url='https://api.twitter.com/oauth/authenticate',
            consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
            consumer_secret=os.environ['TWITTER_SECRET_KEY']
        )

        self.client.tokengetter(self.getTwitterToken)

    def getTwitterToken(self, token=None):
        user_id = session.get('user_id')

        latestToken = AccessToken.query.join(User)\
            .filter(User.id == user_id)\
            .order_by(db.desc(AccessToken.id))\
            .first()

        if latestToken is None:
            return None

        return (latestToken.token, latestToken.secret)

    def getTwitterAccountStatus(self):
        resp = self.client.get('account/verify_credentials.json')

        if resp.status == 200:
            data = resp.data
        else:
            data = None
            flash('Unable to load data from Twitter. Maybe out of '
                  'API calls or Twitter is overloaded.')

        return data

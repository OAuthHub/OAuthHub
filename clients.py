#!/usr/bin/python3

import os
from flask import session
from models import AccessToken, User, db

def twitter(oauth):
    client = oauth.remote_app('twitter',
        base_url='https://api.twitter.com/1.1/',
        request_token_url='https://api.twitter.com/oauth/request_token',
        access_token_url='https://api.twitter.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authenticate',
        consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
        consumer_secret=os.environ['TWITTER_SECRET_KEY']
    )


    @client.tokengetter
    def get_twitter_token(token=None):
        user_id = session.get('user_id')

        latestToken = AccessToken.query.join(User)\
            .filter(User.id == user_id)\
            .order_by(db.desc(AccessToken.id))\
            .first()

        if latestToken is None:
            return None

        return (latestToken.token, latestToken.secret)

    return client

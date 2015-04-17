# -*- coding: utf-8 -*-
## import required modules
try:
    import json
except ImportError:
    from gluon.contrib import simplejson as json
from stravalib.client import Client
from gluon.contrib.login_methods.oauth20_account import OAuthAccount
from gluon.tools import Auth

# Set up database
db = DAL('sqlite://storage.db')

# Define auth
auth = Auth(db)
auth.define_tables(username=False)

# Define oauth application id and secret.
STRAVA_CLIENT_ID='3517'
STRAVA_CLIENT_SECRET='' # Don't push with this revealed

# extend the OAuthAccount class
class StravaAccount(OAuthAccount):
    AUTH_URL = 'https://www.strava.com/oauth/authorize'
    TOKEN_URL = 'https://www.strava.com/oauth/token'

    def __init__(self):
        OAuthAccount.__init__(self, None, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET,
                              self.AUTH_URL, self.TOKEN_URL,
                              response_type='code',
                              approval_prompt='auto') # 'force' to force strava auth on every login
        self.client = None

    # get user info
    def get_user(self):
        client = Client()
        token = self.accessToken()

        if token is None:
            return None

        client.access_token = token
        athlete = client.get_athlete()
        return dict(first_name=athlete.firstname,
                    last_name=athlete.lastname,
                    email=athlete.email)

## use the above class to build a new login form
auth.settings.login_form = StravaAccount()
auth.settings.login_next = URL('index')

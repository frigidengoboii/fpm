import requests
import json
import sys
import os
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from fpm.util.decorators import default_args as default_args
from .exceptions import GraphAuthError, GraphUnknownError

'''
    FB Graph Api handler class
    
    Two possible auth methods:
     - FB Device Login (implemented instead of FB Login Auth because it doesn't 
       require us to run a webserver and catch the redirect)
     - FB Login Auth [DEPRECATED and removed]

    Required options/settings in config:
    config.json
     |- fb_api
     |   |- enable          [bool]
     |   |- app_id          [uint]
     |   |- app_secret      [hexstring]
     |   |- client_token    [hexstring]
     |   |- page_id         [uint]
'''
class GraphApi:
    API_VERSION = '2.10'
    API_ENDPOINT = 'https://graph.facebook.com/v{}'.format(API_VERSION)
    APP_PERMS = 'manage_pages,publish_pages,read_page_mailboxes'
    
    '''
        __init__(self, app_id, app_secret, host, port, page_id)

        Loads options, tries to load access tokens from temp files if not
        specified
    '''
    def __init__(self, *args, **kwargs):
        if 'config' in kwargs:
            with open(kwargs['config']) as fp:
                config = json.load(fp)
        else:
            config = {'fb_api': {}}

        for k in set(list(config['fb_api'].keys()) + list(kwargs.keys())):
            if getattr(self, k, None) is None:
                setattr(self, k, kwargs[k] if kwargs.get(k) is not None 
                                            else config['fb_api'].get(k))
        if os.path.isfile('.access_token'):
            with open('.access_token', 'r') as fp:
                self.access_token = fp.read().strip()
        if os.path.isfile('.page_access_token'):
            with open('.page_access_token', 'r') as fp:
                self.page_access_token = fp.read().strip()
        self.redirect_uri = "https://google.com"
    
    '''
        Log in using facebook's device login API.

        Asks for user to navigate to browser and accept permissions for graph
        API. 
    '''
    @default_args('app_id', 'client_token', 'app_secret', 'redirect_uri')
    def device_login(self, app_id=None, client_token=None, app_secret=None,
            redirect_uri=None):

        params = {
                'access_token': '|'.join((app_id, client_token)),
                'scope': GraphApi.APP_PERMS
            }
        uri = '{}/device/login'.format(
                GraphApi.API_ENDPOINT
            )
        r = requests.post(uri, data=params)
        data = json.loads(r.text)
        uri = data['verification_uri']
        code = data['user_code']
        self.auth_code = data['code']

        print('Please copy the following URL '
                'into your browser:\n{}\n\nThen enter '
                'the following numeric code: {}'.format(uri, code))

        self.access_token = None
        for i in range(0,420,5):
            time.sleep(5)
            params = {
                    'access_token': '|'.join((app_id, client_token)),
                    'code': self.auth_code
                }
            uri = '{}/device/login_status'.format(
                    GraphApi.API_ENDPOINT
                )
            r = requests.post(uri, data=params)
            data = json.loads(r.text)
            if 'error' in data:
                print('Poll failed. Trying again soon...')
                print(data)
                print('Message:{}'.format(data['error']['error_user_msg']))
            else:
                self.access_token = data['access_token']
                self.access_token_expiry = data['expires_in']
                print('Succeess! Got token!')
                break

        if self.access_token is None:
            print('No dice. All polls failed. Restart program and try again')
            sys.exit(1)

        print(self.access_token)
        with open('.access_token', 'w+') as fp:
            fp.write(self.access_token)

        return self.access_token

    '''
        Sends a text post with content <message> to feed of page associated 
        with <page_id>. Requires auth via <page_access_token>.
    '''
    @default_args('page_access_token','page_id')
    def post_text(self, message, page_access_token=None, page_id=None):
        params = {
                'message': message,
                'access_token': page_access_token
            }
        uri = '{}/{}/feed'.format(
                GraphApi.API_ENDPOINT, page_id
            )
        r = requests.post(uri, data=params)
        data = json.loads(r.text)
        self.check_response_auth(data)
        return data['id']

    '''
        Gets a page access token for page associated with <page_id> through
        account associated with <access_token>.
    '''
    @default_args('access_token','page_id')
    def get_page_access_token(self, access_token=None, page_id=None):
        params = {
                'fields': 'access_token',
                'access_token': access_token
            }
        uri = '{}/{}'.format(
                GraphApi.API_ENDPOINT, page_id
            )
        r = requests.get(uri, params=params)
        data = json.loads(r.text)
        self.check_response_auth(data)
        self.page_access_token = data['access_token']
        with open('.page_access_token', 'w+') as fp:
            fp.write(self.page_access_token)

        return self.page_access_token

    '''
        Dumps all messages received by <page_id>. Requires <page_access_token> 
        for authentication.
    '''
    @default_args('page_access_token','page_id')
    def get_conversations(self, page_access_token=None, page_id=None):
        params = {
                'fields':       'id,updated_time,link,'
                                'messages.limit(2147483647)'
                                '{message,created_time,attachments,from,to}',
                'limit':        2147483647,
                'access_token': page_access_token
            }
        uri = '{}/{}/conversations'.format(
                GraphApi.API_ENDPOINT, page_id
            )
        r = requests.get(uri, params=params)
        data = json.loads(r.text)
        self.check_response_auth(data)
        return data['data']
    
    '''
        Utility method to check response to authentication request.
        Raises GraphAuthError or GraphUnknownError when appropriate.
    '''
    def check_response_auth(self, data):
        if 'error' in data:
            data = data['error']
            if data['type'] == 'OAuthException' or data['code'] == 102:
                raise GraphAuthError(data, data['message'])
            else:
                raise GraphUnknownError(data, data['message'])

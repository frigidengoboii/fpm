import requests
import json
import sys
import os
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from fpm.util.decorators import default_args as default_args
from .exceptions import GraphAuthError, GraphUnknownError

class GraphApi:
    API_VERSION = '2.10'
    API_ENDPOINT = 'https://graph.facebook.com/v{}'.format(API_VERSION)
    APP_PERMS = 'manage_pages,publish_pages,read_page_mailboxes'
    
    #CURRENTLY UNUSED
    class _Handler(BaseHTTPRequestHandler):
        def do_GET():
            strip_code()

        def do_POST():
            strip_code()

        def strip_code():
            params = { p.split('&')[0] : p.split('&')[1] 
                    for p in requestline.split('?')[-1].split('&') }
            if 'code' in params:
                server.__ACCESS_CODE__ = params['code']
                send_response(200, 
                        'Code received. You may close this window now!')
                server.shutdown()
            else:
                send_response(200, 
                        'Not the code we\'re looking for. '
                        'Keep looking; try the address again!')
                
    #   __init__(self, app_id, app_secret, host, port, page_id)
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
    
    #CURRENTLY UNUSED
    @default_args('app_id', 'app_secret', 'host', 'port')
    def init_login(self, app_id=None, app_secret=None, 
            host=None, port=None):

        params = {
                'client_id': app_id,
                'redirect_uri': self.redirect_uri,
                'scope': GraphApi.APP_PERMS
            }
        uri = 'https://www.facebook.com/dialog/oauth'

        full_uri = '{}?{}'.format(uri, '&'.join(['{}={}'.format(k, v) 
                                        for k, v in params.items()]))

        print('Please copy the following URL '
            'into your browser and log in\n{}'.format(full_uri))
        
        addr = ('', 8000)
        s = HTTPServer(addr, GraphApi._Handler)
        s.serve_forever(poll_interval=0.5)

        # wait till shutdown
        self.auth_code = server.__ACCESS_CODE__
        return self.auth_code

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
                #print('Message:{}'.format(data['error']['error_user_msg']))
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

    @default_args('app_id', 'auth_code', 'app_secret', 'redirect_uri')
    def get_access_token(self, app_id=None, auth_code=None, app_secret=None, 
            redirect_uri= None):
        params = {
                'client_id': app_id,
                'redirect_uri': self.redirect_uri,
                'client_secret': app_secret,
                'code': auth_code
            }
        uri = '{}/oauth/access_token'.format(
                GraphApi.API_ENDPOINT
            )
        r = requests.get(uri, params=params)
        data = json.loads(r.text)
        self.check_response_auth(data)
        self.access_token = data['access_token']
        return self.access_token

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

    def check_response_auth(self, data):
        if 'error' in data:
            data = data['error']
            if data['type'] == 'OAuthException' or data['code'] == 102:
                raise GraphAuthError(data, data['message'])
            else:
                raise GraphUnknownError(data, data['message'])

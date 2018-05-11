import requests
import json
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

from fpm.util.decorators import default_args as default_args

'''
    Google Sheets Api handler class
    
    CLI-auth provided by oauth2client.

    Required options/settings in config:
    config.json
     |- sheets_api
     |   |- enable          [bool]
     |   |- api_key         [base64string]
     |   |- spreadsheet_id  [base64string]
'''
class SheetsApi:
    API_VERSION = '4'
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

    '''
        Initialisation and authentication of Sheets API using oauth2client.
        Reads credentials from sheets_credentials.json
    '''
    def __init__(self, *args, **kwargs):
        if 'config' in kwargs:
            with open(kwargs['config']) as fp:
                config = json.load(fp)
        else:
            config = {'sheets_api': {}}

        # Load in config
        for k in set(list(config['sheets_api'].keys()) 
                        + list(kwargs.keys())):
            if getattr(self, k, None) is None:
                setattr(self, k, kwargs[k] if kwargs.get(k) is not None 
                                        else config['sheets_api'].get(k))

        store = file.Storage('sheets_credentials.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(
                    'sheets_client_secret.json', 
                    SheetsApi.SCOPES
                )
            creds = tools.run_flow(flow, store)
        self.api = discovery.build(
                'sheets', 
                'v{}'.format(SheetsApi.API_VERSION), 
                http=creds.authorize(Http())
            )

    '''
        Get range specified by <range_> from spreadsheet associated with 
        <spreadsheet_id>. Authentication should be completed if instance method
        is available.
    '''
    @default_args('spreadsheet_id') 
    def get_range(self, range_, spreadsheet_id=None):
        return self.api.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_,
                majorDimension='ROWS',
                valueRenderOption='FORMATTED_VALUE'
            ).execute().get('values', [])




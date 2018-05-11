from xxhash import xxh64
import json
import pytz
import importlib
from datetime import datetime
from pprint import pprint

from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions 

from fpm.controller.state import FpmState
from fpm.graph.api import GraphApi
from fpm.graph.exceptions import GraphAuthError, GraphUnknownError
from fpm.sheets.api import SheetsApi
from fpm.util.post_tools import messages_to_postlist, sheets_to_postlist

'''
    Controller class designed to operate everything.
    Implements program loop.

    Required options/settings in config:
    config.json
     |- fpm
     |   |- state_file          [string; file path]
     |   |- post_format         [string; dict format]
     |   |- timestamp_format    [string; strftime format]
     |- fb_api
     |   |- page_id             [int]
     |- selenium
     |   |- python_module       [string; python library path]
     |   |- driver_path         [string; file path]

'''
class FpmController:

    # xmap paths for fb page elements
    SELENIUM_XPATH_MAP = {
            'post_button': '//span[text()=\'Write something...\']',
            'post_field': '//div[@aria-multiline=\'true\']',
            'submit_button': '//span[text()=\'Publish\']'
        }

    # chrome options for selenium
    SELENIUM_CHROME = {
            'chromeOptions': {
                'prefs': {
                    'profile.managed_default_content_settings.notifications': 1
                }
            }
        }
    
    # facebook login url
    SELENIUM_LOGIN_URL = 'https://www.facebook.com/login/'

    '''
        Load config, initialise state (from file).
    '''
    def __init__(self, config):
        # load and hook config
        with open(config, 'r') as fp:
            self.config = json.load(fp)
        self.configfile = config

        with open(self.config['fpm']['post_format'], 'r') as fp:
            self.post_format = fp.read()
        
        if 'state_file' in self.config['fpm']:
            self.state = FpmState.load(self.config['fpm']['state_file'])
        else:
            self.state = FpmState()
        self.selenium = None

    '''
        Setup APIs, fetch postlists from enabled sources

        Returns postlist
    '''
    def setup(self, graph_auth_callback):
        graph_posts = []
        fb_posts = []
        if self.config['fb_api']['enable']:
            # init fb graph api, fetch messages, fix auth
            self.graph = GraphApi(config=self.configfile)
            graph_data = None
            escape = 0
            if self.state.page_access_token is None:
                self.graph_auth_flow(graph_auth_callback)
            while graph_data is None:
                try: 
                    graph_data = self.graph.get_conversations(
                            page_access_token=self.state.page_access_token,
                            page_id=self.config['fb_api']['page_id']
                        )
                except GraphAuthError as e:
                    self.graph_auth_flow(graph_auth_callback)
            graph_posts = list(messages_to_postlist(
                    graph_data,
                    page_id=self.config['fb_api']['page_id'],
                    ignore_messages_older_than=
                        self.state.ignore_messages_older_than
                ))
        
        if self.config['sheets_api']['enable']:
            # init sheets api, fetch data, auth automatically checked
            self.sheets = SheetsApi(config=self.configfile)
            columns = self.config['sheets_api']['column_range']
            colstart, colend = columns.split(':', 2)
            srange = '{}{}:{}{}'.format(
                    colstart, 
                    self.state.current_sheets_row,
                    colend,
                    '' # end row - leave this blank to get all rows from start
                )
            sheets_data = self.sheets.get_range(srange)
            sheets_posts = list(sheets_to_postlist(
                    sheets_data, 
                    self.config['sheets_api']['column_mappings'],
                    ignore_messages_older_than=
                        self.state.ignore_messages_older_than
                ))

        postlist = graph_posts + sheets_posts
        postlist.sort(key=lambda p: p.get('timestamp') 
                                or datetime.now(pytz.utc))
        return postlist

    '''
        Helper method for Fb Graph Api authentication checks
    '''
    def graph_auth_flow(self, graph_auth_callback):
        try:
            self.state.page_access_token = self.graph.get_page_access_token(
                access_token=self.state.access_token,
            )
        except GraphAuthError as e:
            self.state.access_token = graph_auth_callback(self.graph)
            self.state.page_access_token = self.graph.get_page_access_token(
                access_token=self.state.access_token,
            )
        self.state.save(self.config['fpm']['state_file'])

    '''
        Initialise Selenium session. Request login to Facebook.
    '''
    def setup_selenium(self, auth_conf_callback):
        args = {}
        mod = self.config['selenium']['python_module']
        path = self.config['selenium']['driver_path']
        if path:
            args['executable_path'] = path
        if 'chrome' in path:
            args['desired_capabilities'] = FpmController.SELENIUM_CHROME

        # import selenium
        wd = importlib.import_module(mod)

        self.selenium = wd.WebDriver(**args)
        
        # Cookie injection
        if len(self.state.cookies):
            self.selenium.get(FpmController.SELENIUM_LOGIN_URL)
            for cookie in self.state.cookies:
                self.selenium.add_cookie(cookie)

        self.selenium.get(FpmController.SELENIUM_LOGIN_URL)
        if self.selenium.current_url == FpmController.SELENIUM_LOGIN_URL:
            auth_conf_callback()
        self.state.cookies = self.selenium.get_cookies()
        self.state.save(self.config['fpm']['state_file'])
        return

    '''
        Stop Selenium session. Try to catch any final alerts (currently doesn't
        always work as intended).
    '''
    def stop_selenium(self):
        if self.selenium:
            self.selenium.quit()
            self.selenium = None

    '''
        Process a post from a postlist using Selenium, request confirmation to 
        send post (allow time for any alterations). On confirmation, sends post 
        and shows success message.
    '''
    def process_post_selenium(self, post, confirmation_callback, 
            success_callback):
        # check for duplicate content posts
        if not self.selenium:
            raise 'Error: Selenium not started. WTF dude'
        
        # Generate post hash
        post['hash'] = xxh64(post['content']).hexdigest()
        if post['hash'] in self.state.posts:
            return False

        # Convert datetime.datetime to human-readable formatted string
        if post['timestamp']:
            post['nice_timestamp'] = post['timestamp'].strftime(
                    self.config['fpm']['timestamp_format']
                )

        # Credit field formatting hack for Frigid Engo Boii facebook page
        if post['credit'] != '':
            post['credit'] = ' - {}'.format(post['credit'])

        # Inject post number into post (since we have now hit number)
        post['post_number'] = self.state.current_post_number

        # Generate formatted string representation of post
        post['_repr'] = self.post_format.format_map(post)

        # Load page, inject post into 'post' field (click on field, send keys)
        try:
            self.selenium.get('https://facebook.com/{}'.format(
                    self.config['fb_api']['page_id']
                ))
            self.selenium.switch_to_alert().accept()
        except NoAlertPresentException:
            pass
        postbutton = WebDriverWait(self.selenium, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, FpmController.SELENIUM_XPATH_MAP['post_button'])
                )
            )
        postbutton.click()
        postbox = WebDriverWait(self.selenium, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, FpmController.SELENIUM_XPATH_MAP['post_field'])
                )
            )
        postbox.send_keys(post['_repr'])

        # Check confirmation callback and receive confirmation.
        if not confirmation_callback(post):
            # Reject post - update timestamp and save state, return
            self.state.ignore_messages_older_than = post['timestamp']
            self.state.save(self.config['fpm']['state_file'])
            return False
        
        # Accept post - click submit button
        self.selenium.find_element_by_xpath(
                FpmController.SELENIUM_XPATH_MAP['submit_button']
            ).click()
        # Update post number, timestamp; add hash to post db; save state
        self.state.current_post_number += 1
        self.state.ignore_messages_older_than = post['timestamp']
        self.state.posts.add(post['hash'])
        self.state.save(self.config['fpm']['state_file'])

        # Report success to callback, return
        success_callback(post)
        return True
        

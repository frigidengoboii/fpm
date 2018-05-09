from xxhash import xxh64
import json
import pytz
from datetime import datetime
from pprint import pprint

from fpm.controller.state import FpmState
from fpm.graph.api import GraphApi
from fpm.graph.exceptions import GraphAuthError, GraphUnknownError
from fpm.sheets.api import SheetsApi
from fpm.util.post_tools import messages_to_postlist, sheets_to_postlist

class FpmController:

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

    # setup process also returns postlist 
    def setup(self, graph_auth_callback):
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

    def process_post(self, post, confirmation_callback, success_callback, 
            graph_auth_callback):
        # check for duplicate content posts
        post['hash'] = xxh64(post['content']).hexdigest()
        if post['hash'] in self.state.posts:
            return False

        if post['timestamp']:
            post['nice_timestamp'] = post['timestamp'].strftime(
                    self.config['fpm']['timestamp_format']
                )
        if post['credit'] != '':
            post['credit'] = ' - {}'.format(post['credit'])
        post['post_number'] = self.state.current_post_number
        pprint(post)
        post['_repr'] = self.post_format.format_map(post)

        if not confirmation_callback(post):
            self.state.ignore_messages_older_than = post['timestamp']
            self.state.save(self.config['fpm']['state_file'])
            return False
        res = None
        while res is None:
            try:
                res = self.graph.post_text(
                        post['_repr'],
                        page_access_token=self.state.page_access_token,
                        page_id=self.config['fb_api']['page_id']
                    )
            except GraphAuthError as gae:
                self.graph_auth_flow(graph_auth_callback)
        self.state.current_post_number += 1
        self.state.ignore_messages_older_than = post['timestamp']
        self.state.posts.add(post['hash'])
        self.state.save(self.config['fpm']['state_file'])

        success_callback(post, res)
        return True
	

        


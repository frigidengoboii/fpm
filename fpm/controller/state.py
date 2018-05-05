from datetime import datetime
import pickle

class FpmState:
    
    def __init__(self):
        defaults = {
                'current_sheets_row': 1,
                'current_post_number': 1,
                'ignore_messages_older_than': datetime(1970, 1, 1),
                'posts': set(),
                'access_token': None,
                'page_access_token': None
            }
        for k, v in defaults.items():
            setattr(self, k, v)

    def save(self, filename):
        with open(filename, 'wb+') as fp:
            pickle.dump(self, fp)

    def load(filename):
        with open(filename, 'rb') as fp:
            return pickle.load(fp)


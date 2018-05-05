from fpm.controller.controller import FpmController
from fpm.graph.api import GraphApi

CLS='\033[H\033[J'

def crap_line_interface():
    print('::WARNING::\nThis CLI implementation is utter garbage and only '
            'suitable for testing and masochism purposes.\nUse at own risk')

    controller = FpmController('config.json')

    postlist = controller.setup(GraphApi.device_login)
    
    for post in postlist:
        controller.process_post(post, cli_confirmation, cli_success, 
                GraphApi.device_login)


def cli_confirmation(post):
    print(CLS)
    print(post['_repr'])
    print('----------------------------------------------------------')
    conf = input('Would you like to post the above? Y/n? ')
    return ('y' in conf or 'Y' in conf)
    
def cli_success(post, post_id):
    print('----------------------------------------------------------')
    print('Post successfully posted to \n'
            '    https://www.facebook.com/{}'.format(post_id))
    conf = input('Press enter to continue... ')
    return
    




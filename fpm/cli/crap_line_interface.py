import signal, sys

from fpm.controller.controller import FpmController
from fpm.graph.api import GraphApi

global_controller = None

CLS='\033[H\033[J'

def crap_line_interface():
    print('::WARNING::\nThis CLI implementation is utter garbage and only '
            'suitable for testing and masochism purposes.\nUse at own risk')
    signal.signal(signal.SIGINT, signal_handler)

    controller = FpmController('config.json')
    global_controller = controller

    postlist = controller.setup(GraphApi.device_login)
    controller.setup_selenium(login_prompt)
    
    for post in postlist:
        controller.process_post_selenium(post, cli_confirmation, cli_success)

    controller.stop_selenium()

def signal_handler(signal, frame):
    if global_controller and global_controller.selenium:
        global_controller.stop_selenium()
    sys.exit(1)

def cli_confirmation(post):
    print(CLS)
    print(post['_repr'])
    print('----------------------------------------------------------')
    conf = input('Would you like to post the above? Y/n? ')
    return ('y' in conf or 'Y' in conf)
    
def cli_success(post):
    print('----------------------------------------------------------')
    print('Post successfully posted!\n')
    conf = input('Press enter to continue... ')
    return
    
def login_prompt():
    print('----------------------------------------------------------')
    conf = input('Please log in to Facebook, then press enter to continue...')
    return

